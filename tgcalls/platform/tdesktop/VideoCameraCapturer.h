#ifndef TGCALLS_VIDEO_CAMERA_CAPTURER_H
#define TGCALLS_VIDEO_CAMERA_CAPTURER_H

#include "api/scoped_refptr.h"
#include "api/video/video_frame.h"
#include "api/video/video_source_interface.h"
#include "media/base/video_adapter.h"
#include "media/base/video_broadcaster.h"
#include "modules/video_capture/video_capture.h"

#include "VideoCaptureInterface.h"

#include <memory>
#include <vector>
#include <stddef.h>

namespace tgcalls {

class VideoCameraCapturer :
	public rtc::VideoSourceInterface<webrtc::VideoFrame>,
	public rtc::VideoSinkInterface<webrtc::VideoFrame> {
public:
	VideoCameraCapturer();
	~VideoCameraCapturer();

	void setState(VideoState state);
	void setDeviceId(std::string deviceId);
	void setPreferredCaptureAspectRatio(float aspectRatio);

	std::pair<int, int> resolution() const;

	void AddOrUpdateSink(rtc::VideoSinkInterface<webrtc::VideoFrame>* sink,
		const rtc::VideoSinkWants& wants) override;
	void RemoveSink(rtc::VideoSinkInterface<webrtc::VideoFrame>* sink) override;

	void OnFrame(const webrtc::VideoFrame &frame) override;

private:
	void create();
	bool create(webrtc::VideoCaptureModule::DeviceInfo *info, const std::string &deviceId);
	void destroy();
	void updateVideoAdapter();

	rtc::VideoBroadcaster _broadcaster;
	rtc::scoped_refptr<webrtc::VideoCaptureModule> _module;
	webrtc::VideoCaptureCapability _capability;

	VideoState _state = VideoState::Inactive;
	std::string _requestedDeviceId;
	std::pair<int, int> _dimensions;
	float _aspectRatio = 0.;

};

}  // namespace tgcalls

#endif
