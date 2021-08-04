#import "VideoMetalViewMac.h"
#import <Metal/Metal.h>
#import <MetalKit/MetalKit.h>
#import "TGRTCCVPixelBuffer.h"
#import "base/RTCLogging.h"
#import "base/RTCVideoFrame.h"
#import "base/RTCVideoFrameBuffer.h"
#import "components/video_frame_buffer/RTCCVPixelBuffer.h"
#include "sdk/objc/native/api/video_frame.h"
#include "sdk/objc/native/src/objc_frame_buffer.h"

#import "api/video/video_sink_interface.h"
#import "api/media_stream_interface.h"
#import "rtc_base/time_utils.h"

#import <SSignalKit/SSignalKit.h>


#import "api/video/video_sink_interface.h"
#import "api/media_stream_interface.h"

#import "TGRTCMTLI420Renderer.h"

#define MTKViewClass NSClassFromString(@"MTKView")
#define TGRTCMTLI420RendererClass NSClassFromString(@"TGRTCMTLI420Renderer")

SQueue *renderQueue = [[SQueue alloc] init];

namespace {
    
static RTCVideoFrame *customToObjCVideoFrame(const webrtc::VideoFrame &frame, RTCVideoRotation &rotation) {
    rotation = RTCVideoRotation(frame.rotation());
    RTCVideoFrame *videoFrame =
    [[RTCVideoFrame alloc] initWithBuffer:webrtc::ToObjCVideoFrameBuffer(frame.video_frame_buffer())
                                 rotation:rotation
                              timeStampNs:frame.timestamp_us() * rtc::kNumNanosecsPerMicrosec];
    videoFrame.timeStamp = frame.timestamp();
    
    return videoFrame;
}

class VideoRendererAdapterImpl : public rtc::VideoSinkInterface<webrtc::VideoFrame> {
public:
    VideoRendererAdapterImpl(void (^frameReceived)(CGSize, RTCVideoFrame *, RTCVideoRotation)) {
        _frameReceived = [frameReceived copy];
    }
    
    void OnFrame(const webrtc::VideoFrame& nativeVideoFrame) override {
        RTCVideoRotation rotation = RTCVideoRotation_0;
        RTCVideoFrame* videoFrame = customToObjCVideoFrame(nativeVideoFrame, rotation);
        
        CGSize currentSize = (videoFrame.rotation % 180 == 0) ? CGSizeMake(videoFrame.width, videoFrame.height) : CGSizeMake(videoFrame.height, videoFrame.width);

        if (_frameReceived) {
            _frameReceived(currentSize, videoFrame, rotation);
        }
    }
    
private:
    void (^_frameReceived)(CGSize, RTCVideoFrame *, RTCVideoRotation);
};

}



@interface VideoMetalView () <MTKViewDelegate> {
    SQueueLocalObject *_rendererI420;

    CAMetalLayer *_metalView;
    RTCVideoFrame *_videoFrame;
    CGSize _videoFrameSize;
    int64_t _lastFrameTimeNs;
    
    CGSize _currentSize;
    std::shared_ptr<VideoRendererAdapterImpl> _sink;
    
    void (^_onFirstFrameReceived)(float);
    bool _firstFrameReceivedReported;
    void (^_onOrientationUpdated)(int, CGFloat);
    void (^_onIsMirroredUpdated)(bool);
    
    bool _didSetShouldBeMirrored;
    bool _shouldBeMirrored;
    bool _forceMirrored;
}

@end

@implementation VideoMetalView

+ (bool)isSupported {
    return [VideoMetalView isMetalAvailable];
}

- (instancetype)initWithFrame:(CGRect)frameRect {
    self = [super initWithFrame:frameRect];
    if (self) {
        [self configure];
        _lastFrameTimeNs = INT32_MAX;
        _currentSize = CGSizeZero;
        
       
        
        __weak VideoMetalView *weakSelf = self;
        _sink.reset(new VideoRendererAdapterImpl(^(CGSize size, RTCVideoFrame *videoFrame, RTCVideoRotation rotation) {
            dispatch_async(dispatch_get_main_queue(), ^{
                __strong VideoMetalView *strongSelf = weakSelf;
                if (strongSelf == nil) {
                    return;
                }
                if (!CGSizeEqualToSize(size, strongSelf->_currentSize)) {
                    strongSelf->_currentSize = size;
                    [strongSelf setSize:size];
                }
                
                int mappedValue = 0;
                switch (rotation) {
                    case RTCVideoRotation_90:
                        mappedValue = 0;
                        break;
                    case RTCVideoRotation_180:
                        mappedValue = 1;
                        break;
                    case RTCVideoRotation_270:
                        mappedValue = 2;
                        break;
                    default:
                        mappedValue = 0;
                        break;
                }
                [strongSelf setInternalOrientation:mappedValue];
                
                [strongSelf renderFrame:videoFrame];
                
                if ([videoFrame.buffer isKindOfClass:[RTCCVPixelBuffer class]]) {
                    RTCCVPixelBuffer *buffer = (RTCCVPixelBuffer*)videoFrame.buffer;
                    
                    if ([buffer isKindOfClass:[TGRTCCVPixelBuffer class]]) {
                        bool shouldBeMirrored = ((TGRTCCVPixelBuffer *)buffer).shouldBeMirrored;
                        if (shouldBeMirrored != strongSelf->_shouldBeMirrored) {
                            strongSelf->_shouldBeMirrored = shouldBeMirrored;
                            if (strongSelf->_onIsMirroredUpdated) {
                                strongSelf->_onIsMirroredUpdated(strongSelf->_shouldBeMirrored);
                            }
                        }
                    }
                }
                
                if (!strongSelf->_firstFrameReceivedReported && strongSelf->_onFirstFrameReceived) {
                    strongSelf->_firstFrameReceivedReported = true;
                    strongSelf->_onFirstFrameReceived((float)videoFrame.width / (float)videoFrame.height);
                }
            });
        }));

    }
    return self;
}

- (BOOL)isEnabled {
    return YES;
}

- (void)setEnabled:(BOOL)enabled {
    
}

- (CALayerContentsGravity)videoContentMode {
    return _metalView.contentsGravity;
}

- (void)setVideoContentMode:(CALayerContentsGravity)mode {
    _metalView.contentsGravity = mode;
}

#pragma mark - Private

+ (BOOL)isMetalAvailable {
    return CGDirectDisplayCopyCurrentMetalDevice(CGMainDisplayID()) != nil;
}

+ (CAMetalLayer *)createMetalView:(CGRect)frame {
    return [[CAMetalLayer alloc] init];
}

+ (TGRTCMTLI420Renderer *)createI420Renderer {
    return [[TGRTCMTLI420RendererClass alloc] init];
}


- (void)configure {
    NSAssert([VideoMetalView isMetalAvailable], @"Metal not availiable on this device");
    self.wantsLayer = YES;
    self.layerContentsRedrawPolicy = NSViewLayerContentsRedrawDuringViewResize;
    _metalView = [VideoMetalView createMetalView:self.bounds];
    self.layer = _metalView;
    _metalView.framebufferOnly = true;
    _metalView.opaque = false;

    _metalView.cornerRadius = 4;
    _metalView.backgroundColor = [NSColor clearColor].CGColor;
    _metalView.contentsGravity = kCAGravityResizeAspect;//UIViewContentModeScaleAspectFill;
    _videoFrameSize = CGSizeZero;
    
    CAMetalLayer *layer = _metalView;
    
    _rendererI420 = [[SQueueLocalObject alloc] initWithQueue:renderQueue generate: ^{
        TGRTCMTLI420Renderer *renderer = [VideoMetalView createI420Renderer];
        [renderer addRenderingDestination:layer];
        return renderer;
    }];
}


-(void)setFrameSize:(NSSize)newSize {
    [super setFrameSize:newSize];
}
- (void)layout {
    [super layout];
    
    CGRect bounds = self.bounds;
    _metalView.frame = bounds;
    if (!CGSizeEqualToSize(_videoFrameSize, CGSizeZero)) {
        _metalView.drawableSize = [self drawableSize];
    } else {
        _metalView.drawableSize = bounds.size;
    }
}


-(void)dealloc {
    int bp = 0;
    bp += 1;
}

#pragma mark -

- (void)setRotationOverride:(NSValue *)rotationOverride {
    _rotationOverride = rotationOverride;
    
    _metalView.drawableSize = [self drawableSize];
    [self setNeedsLayout:YES];
}

- (RTCVideoRotation)rtcFrameRotation {
    if (_rotationOverride) {
        RTCVideoRotation rotation;
        if (@available(macOS 10.13, *)) {
            [_rotationOverride getValue:&rotation size:sizeof(rotation)];
        } else {
            [_rotationOverride getValue:&rotation];
        }
        return rotation;
    }
    
    return _videoFrame.rotation;
}

- (CGSize)drawableSize {
    // Flip width/height if the rotations are not the same.
    CGSize videoFrameSize = _videoFrameSize;
    RTCVideoRotation frameRotation = [self rtcFrameRotation];
    
    BOOL useLandscape =
    (frameRotation == RTCVideoRotation_0) || (frameRotation == RTCVideoRotation_180);
    BOOL sizeIsLandscape = (_videoFrame.rotation == RTCVideoRotation_0) ||
    (_videoFrame.rotation == RTCVideoRotation_180);
    
    if (useLandscape == sizeIsLandscape) {
        return videoFrameSize;
    } else {
        return CGSizeMake(videoFrameSize.height, videoFrameSize.width);
    }
}

#pragma mark - RTCVideoRenderer

- (void)setSize:(CGSize)size {
    assert([NSThread isMainThread]);
           
   _videoFrameSize = size;
   CGSize drawableSize = [self drawableSize];
   _metalView.drawableSize = drawableSize;
   [self setNeedsLayout:YES];
    
    _internalAspect = _videoFrameSize.width / _videoFrameSize.height;
}

- (void)renderFrame:(nullable RTCVideoFrame *)frame {
    assert([NSThread isMainThread]);
    
    if (!self.isEnabled) {
        return;
    }
    
    if (frame == nil) {
        RTCLogInfo(@"Incoming frame is nil. Exiting render callback.");
        return;
    }
    _videoFrame = frame;
    
    RTCVideoFrame *videoFrame = _videoFrame;
    // Skip rendering if we've already rendered this frame.
    if (!videoFrame || videoFrame.timeStampNs == _lastFrameTimeNs) {
        return;
    }
        
    if (CGRectIsEmpty(self.bounds)) {
        return;
    }
    if (CGRectIsEmpty(self.visibleRect)) {
        return;
    }
    if (self.window == nil || self.superview == nil) {
        return;
    }
    if ((self.window.occlusionState & NSWindowOcclusionStateVisible) == 0) {
        return;
    }
            
    
    
    NSValue * rotationOverride = _rotationOverride;
    
    [_rendererI420 with:^(TGRTCMTLI420Renderer * object) {
        object.rotationOverride = rotationOverride;
        [object drawFrame:videoFrame];
    }];
    
    _lastFrameTimeNs = videoFrame.timeStampNs;

}

- (std::shared_ptr<rtc::VideoSinkInterface<webrtc::VideoFrame>>)getSink {
    assert([NSThread isMainThread]);
    
    return _sink;
}

- (void)setOnFirstFrameReceived:(void (^ _Nullable)(float))onFirstFrameReceived {
    _onFirstFrameReceived = [onFirstFrameReceived copy];
    _firstFrameReceivedReported = false;
}

- (void)setInternalOrientationAndSize:(int)internalOrientation size:(CGSize)size {
    CGFloat aspect = 1.0f;
    if (size.width > 1.0f && size.height > 1.0f) {
        aspect = size.width / size.height;
    }
    if (_internalOrientation != internalOrientation || ABS(_internalAspect - aspect) > 0.001) {
        RTCLogInfo(@"VideoMetalView@%lx orientation: %d, aspect: %f", (intptr_t)self, internalOrientation, (float)aspect);
        
        _internalOrientation = internalOrientation;
        _internalAspect = aspect;
        if (_onOrientationUpdated) {
            _onOrientationUpdated(internalOrientation, aspect);
        }
    }
}

- (void)internalSetOnOrientationUpdated:(void (^ _Nullable)(int, CGFloat))onOrientationUpdated {
    _onOrientationUpdated = [onOrientationUpdated copy];
}

- (void)internalSetOnIsMirroredUpdated:(void (^ _Nullable)(bool))onIsMirroredUpdated {
    _onIsMirroredUpdated = [onIsMirroredUpdated copy];
}

- (void)setForceMirrored:(BOOL)forceMirrored {
    _forceMirrored = forceMirrored;
    [self setNeedsLayout:YES];
}


@end
