#include "DesktopInterface.h"

#include "platform/tdesktop/VideoCapturerInterfaceImpl.h"
#include "platform/tdesktop/VideoCapturerTrackSource.h"

#include "api/video_codecs/builtin_video_encoder_factory.h"
#include "api/video_codecs/builtin_video_decoder_factory.h"
#include "api/video_track_source_proxy.h"

namespace tgcalls {

std::unique_ptr<webrtc::VideoEncoderFactory> DesktopInterface::makeVideoEncoderFactory() {
	return webrtc::CreateBuiltinVideoEncoderFactory();
}

std::unique_ptr<webrtc::VideoDecoderFactory> DesktopInterface::makeVideoDecoderFactory() {
	return webrtc::CreateBuiltinVideoDecoderFactory();
}

rtc::scoped_refptr<webrtc::VideoTrackSourceInterface> DesktopInterface::makeVideoSource(rtc::Thread *signalingThread, rtc::Thread *workerThread) {
	const auto videoTrackSource = rtc::scoped_refptr<VideoCapturerTrackSource>(
		new rtc::RefCountedObject<VideoCapturerTrackSource>());
	return videoTrackSource
		? webrtc::VideoTrackSourceProxy::Create(signalingThread, workerThread, videoTrackSource)
		: nullptr;
}

bool DesktopInterface::supportsEncoding(const std::string &codecName) {
	return (codecName == cricket::kH264CodecName)
		|| (codecName == cricket::kVp8CodecName);
}

void DesktopInterface::adaptVideoSource(rtc::scoped_refptr<webrtc::VideoTrackSourceInterface> videoSource, int width, int height, int fps) {
}
//
std::unique_ptr<VideoCapturerInterface> DesktopInterface::makeVideoCapturer(rtc::scoped_refptr<webrtc::VideoTrackSourceInterface> source, std::string deviceId, std::function<void(VideoState)> stateUpdated, std::function<void(PlatformCaptureInfo)> captureInfoUpdated, std::shared_ptr<PlatformContext> platformContext, std::pair<int, int> &outResolution) {
//	return std::make_unique<VideoCapturerInterfaceImpl>(source, deviceId, stateUpdated, platformContext, outResolution);
  return nullptr;
}

std::unique_ptr<PlatformInterface> CreatePlatformInterface() {
	return std::make_unique<DesktopInterface>();
}

} // namespace tgcalls
