#ifndef TGCALLS_CUSTOM_EXTERNAL_CAPTURER_H
#define TGCALLS_CUSTOM_EXTERNAL_CAPTURER_H
#ifdef WEBRTC_IOS
#import <Foundation/Foundation.h>
#import <AVFoundation/AVFoundation.h>

#include <memory>
#include "api/scoped_refptr.h"
#include "api/media_stream_interface.h"
#import "base/RTCVideoFrame.h"
#include "Instance.h"

@interface CustomExternalCapturer : NSObject

- (instancetype)initWithSource:(rtc::scoped_refptr<webrtc::VideoTrackSourceInterface>)source;

+ (void)passPixelBuffer:(CVPixelBufferRef)pixelBuffer rotation:(RTCVideoRotation)rotation toSource:(rtc::scoped_refptr<webrtc::VideoTrackSourceInterface>)source croppingBuffer:(std::vector<uint8_t> &)croppingBuffer;

@end
#endif // WEBRTC_IOS
#endif
