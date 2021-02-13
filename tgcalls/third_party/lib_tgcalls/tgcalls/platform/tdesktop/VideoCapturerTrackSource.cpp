#include "VideoCapturerTrackSource.h"

#include "tgcalls/platform/tdesktop/VideoCameraCapturer.h"

#include "modules/video_capture/video_capture_factory.h"

namespace tgcalls {

rtc::scoped_refptr<VideoCapturerTrackSource> VideoCapturerTrackSource::Create() {
	return new rtc::RefCountedObject<VideoCapturerTrackSource>(
		CreateTag{},
		std::make_unique<VideoCameraCapturer>());
}

VideoCapturerTrackSource::VideoCapturerTrackSource(
	const CreateTag &,
	std::unique_ptr<VideoCameraCapturer> capturer) :
VideoTrackSource(/*remote=*/false),
_capturer(std::move(capturer)) {
}

VideoCameraCapturer *VideoCapturerTrackSource::capturer() const {
	return _capturer.get();
}

rtc::VideoSourceInterface<webrtc::VideoFrame>* VideoCapturerTrackSource::source() {
	return _capturer.get();
}

} // namespace tgcalls
