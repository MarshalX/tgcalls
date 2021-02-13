#include "DarwinInterface.h"

#include "VideoCapturerInterfaceImpl.h"
#include "sdk/objc/native/src/objc_video_track_source.h"

#include "media/base/media_constants.h"
#include "TGRTCDefaultVideoEncoderFactory.h"
#include "TGRTCDefaultVideoDecoderFactory.h"
#include "sdk/objc/native/api/video_encoder_factory.h"
#include "sdk/objc/native/api/video_decoder_factory.h"
#include "api/video_track_source_proxy.h"
#import "base/RTCLogging.h"

#ifdef WEBRTC_IOS
#include "sdk/objc/components/audio/RTCAudioSession.h"
#import <UIKit/UIKit.h>
#endif // WEBRTC_IOS

#import <AVFoundation/AVFoundation.h>

#include <sys/sysctl.h>

namespace tgcalls {

static webrtc::ObjCVideoTrackSource *getObjCVideoSource(const rtc::scoped_refptr<webrtc::VideoTrackSourceInterface> nativeSource) {
    webrtc::VideoTrackSourceProxy *proxy_source =
    static_cast<webrtc::VideoTrackSourceProxy *>(nativeSource.get());
    return static_cast<webrtc::ObjCVideoTrackSource *>(proxy_source->internal());
}

static NSString *getPlatformInfo() {
    const char *typeSpecifier = "hw.machine";
    
    size_t size;
    sysctlbyname(typeSpecifier, NULL, &size, NULL, 0);
    
    char *answer = (char *)malloc(size);
    sysctlbyname(typeSpecifier, answer, &size, NULL, 0);
    
    NSString *results = [NSString stringWithCString:answer encoding:NSUTF8StringEncoding];
    
    free(answer);
    return results;
}

void DarwinInterface::configurePlatformAudio() {
#ifdef WEBRTC_IOS
    [RTCAudioSession sharedInstance].useManualAudio = true;
    [[RTCAudioSession sharedInstance] audioSessionDidActivate:[AVAudioSession sharedInstance]];
    [RTCAudioSession sharedInstance].isAudioEnabled = true;
    
    RTCLogInfo(@"Configuring platform: %@ %@", getPlatformInfo(), [[UIDevice currentDevice] systemVersion]);
#endif
}

std::unique_ptr<webrtc::VideoEncoderFactory> DarwinInterface::makeVideoEncoderFactory() {
    return webrtc::ObjCToNativeVideoEncoderFactory([[TGRTCDefaultVideoEncoderFactory alloc] init]);
}

std::unique_ptr<webrtc::VideoDecoderFactory> DarwinInterface::makeVideoDecoderFactory() {
    return webrtc::ObjCToNativeVideoDecoderFactory([[TGRTCDefaultVideoDecoderFactory alloc] init]);
}

bool DarwinInterface::supportsEncoding(const std::string &codecName) {
	if (codecName == cricket::kH265CodecName) {
#ifdef WEBRTC_IOS
		if (@available(iOS 11.0, *)) {
			return [[AVAssetExportSession allExportPresets] containsObject:AVAssetExportPresetHEVCHighestQuality];
		}
#elif defined WEBRTC_MAC // WEBRTC_IOS
//		if (@available(macOS 10.14, *)) {
//			return [[AVAssetExportSession allExportPresets] containsObject:AVAssetExportPresetHEVCHighestQuality];
//		}
#endif // WEBRTC_IOS || WEBRTC_MAC
    } else if (codecName == cricket::kH264CodecName) {
        return true;
    } else if (codecName == cricket::kVp8CodecName) {
        return true;
    } else if (codecName == cricket::kVp9CodecName) {
        return true;
    }
    return false;
}

rtc::scoped_refptr<webrtc::VideoTrackSourceInterface> DarwinInterface::makeVideoSource(rtc::Thread *signalingThread, rtc::Thread *workerThread) {
    rtc::scoped_refptr<webrtc::ObjCVideoTrackSource> objCVideoTrackSource(new rtc::RefCountedObject<webrtc::ObjCVideoTrackSource>());
    return webrtc::VideoTrackSourceProxy::Create(signalingThread, workerThread, objCVideoTrackSource);
}

void DarwinInterface::adaptVideoSource(rtc::scoped_refptr<webrtc::VideoTrackSourceInterface> videoSource, int width, int height, int fps) {
    getObjCVideoSource(videoSource)->OnOutputFormatRequest(width, height, fps);
}

std::unique_ptr<VideoCapturerInterface> DarwinInterface::makeVideoCapturer(rtc::scoped_refptr<webrtc::VideoTrackSourceInterface> source, std::string deviceId, std::function<void(VideoState)> stateUpdated, std::function<void(PlatformCaptureInfo)> captureInfoUpdated, std::shared_ptr<PlatformContext> platformContext, std::pair<int, int> &outResolution) {
    return std::make_unique<VideoCapturerInterfaceImpl>(source, deviceId, stateUpdated, captureInfoUpdated, outResolution);
}

std::unique_ptr<PlatformInterface> CreatePlatformInterface() {
	return std::make_unique<DarwinInterface>();
}

} // namespace tgcalls
