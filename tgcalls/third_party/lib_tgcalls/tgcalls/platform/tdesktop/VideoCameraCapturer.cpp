#include "VideoCameraCapturer.h"

#include "api/video/i420_buffer.h"
#include "api/video/video_frame_buffer.h"
#include "api/video/video_rotation.h"
#include "modules/video_capture/video_capture_factory.h"
#include "rtc_base/checks.h"
#include "rtc_base/logging.h"

#include <stdint.h>
#include <memory>
#include <algorithm>

namespace tgcalls {
namespace {

constexpr auto kPreferredWidth = 640;
constexpr auto kPreferredHeight = 480;
constexpr auto kPreferredFps = 30;

} // namespace

VideoCameraCapturer::VideoCameraCapturer() = default;

VideoCameraCapturer::~VideoCameraCapturer() {
	destroy();
}

void VideoCameraCapturer::create() {
	const auto info = std::unique_ptr<webrtc::VideoCaptureModule::DeviceInfo>(
		webrtc::VideoCaptureFactory::CreateDeviceInfo());
	if (!info) {
		return;
	}
	const auto count = info->NumberOfDevices();
	if (count <= 0) {
		return;
	}
	const auto getId = [&](int index) {
		constexpr auto kLengthLimit = 256;
		char name[kLengthLimit] = { 0 };
		char id[kLengthLimit] = { 0 };
		return (info->GetDeviceName(index, name, kLengthLimit, id, kLengthLimit) == 0)
			? std::string(id)
			: std::string();
	};
	auto preferredId = std::string();
	for (auto i = 0; i != count; ++i) {
		const auto id = getId(i);
		if ((_requestedDeviceId == id)
			|| (preferredId.empty()
				&& (_requestedDeviceId.empty() || _requestedDeviceId == "default"))) {
			preferredId = id;
		}
	}
	if (create(info.get(), preferredId)) {
		return;
	}
	for (auto i = 0; i != count; ++i) {
		if (create(info.get(), getId(i))) {
			return;
		}
	}
}

bool VideoCameraCapturer::create(webrtc::VideoCaptureModule::DeviceInfo *info, const std::string &deviceId) {
	_module = webrtc::VideoCaptureFactory::Create(deviceId.c_str());
	if (!_module) {
		RTC_LOG(LS_ERROR)
			<< "Failed to create VideoCameraCapturer '" << deviceId << "'.";
		return false;
	}
	_module->RegisterCaptureDataCallback(this);

	auto requested = webrtc::VideoCaptureCapability();
	requested.videoType = webrtc::VideoType::kI420;
	requested.width = kPreferredWidth;
	requested.height = kPreferredHeight;
	requested.maxFPS = kPreferredFps;
	info->GetBestMatchedCapability(
		_module->CurrentDeviceName(),
		requested,
		_capability);
	if (!_capability.width || !_capability.height || !_capability.maxFPS) {
		_capability.width = kPreferredWidth;
		_capability.height = kPreferredHeight;
		_capability.maxFPS = kPreferredFps;
	}
	_capability.videoType = webrtc::VideoType::kI420;
	if (_module->StartCapture(_capability) != 0) {
		RTC_LOG(LS_ERROR)
			<< "Failed to start VideoCameraCapturer '" << _requestedDeviceId << "'.";
		destroy();
		return false;
	}
	_dimensions = std::make_pair(_capability.width, _capability.height);
	return true;
}

void VideoCameraCapturer::setState(VideoState state) {
	if (_state == state) {
		return;
	}
	_state = state;
	if (_state == VideoState::Active) {
		create();
	} else {
		destroy();
	}
}

void VideoCameraCapturer::setDeviceId(std::string deviceId) {
	if (_requestedDeviceId == deviceId) {
		return;
	}
	destroy();
	_requestedDeviceId = deviceId;
	if (_state == VideoState::Active) {
		create();
	}
}

void VideoCameraCapturer::setPreferredCaptureAspectRatio(float aspectRatio) {
	_aspectRatio = aspectRatio;
}

std::pair<int, int> VideoCameraCapturer::resolution() const {
	return _dimensions;
}

void VideoCameraCapturer::destroy() {
	if (!_module) {
		return;
	}

	_module->StopCapture();
	_module->DeRegisterCaptureDataCallback();
	_module = nullptr;
}

void VideoCameraCapturer::OnFrame(const webrtc::VideoFrame &frame) {
	if (_state != VideoState::Active) {
		return;
	}
	//int cropped_width = 0;
	//int cropped_height = 0;
	//int out_width = 0;
	//int out_height = 0;

	//if (!_videoAdapter.AdaptFrameResolution(
	//	frame.width(), frame.height(), frame.timestamp_us() * 1000,
	//	&cropped_width, &cropped_height, &out_width, &out_height)) {
	//	// Drop frame in order to respect frame rate constraint.
	//	return;
	//}
	//if (out_height != frame.height() || out_width != frame.width()) {
	//	// Video adapter has requested a down-scale. Allocate a new buffer and
	//	// return scaled version.
	//	// For simplicity, only scale here without cropping.
	//	rtc::scoped_refptr<webrtc::I420Buffer> scaled_buffer =
	//		webrtc::I420Buffer::Create(out_width, out_height);
	//	scaled_buffer->ScaleFrom(*frame.video_frame_buffer()->ToI420());
	//	webrtc::VideoFrame::Builder new_frame_builder =
	//		webrtc::VideoFrame::Builder()
	//		.set_video_frame_buffer(scaled_buffer)
	//		.set_rotation(webrtc::kVideoRotation_0)
	//		.set_timestamp_us(frame.timestamp_us())
	//		.set_id(frame.id());
	//	if (frame.has_update_rect()) {
	//		webrtc::VideoFrame::UpdateRect new_rect = frame.update_rect().ScaleWithFrame(
	//			frame.width(), frame.height(), 0, 0, frame.width(), frame.height(),
	//			out_width, out_height);
	//		new_frame_builder.set_update_rect(new_rect);
	//	}
	//	_broadcaster.OnFrame(new_frame_builder.build());

	//} else {
	//	// No adaptations needed, just return the frame as is.
	//	_broadcaster.OnFrame(frame);
	//}

	if (_aspectRatio <= 0.001) {
		_broadcaster.OnFrame(frame);
		return;
	}
	const auto originalWidth = frame.width();
	const auto originalHeight = frame.height();
	auto width = (originalWidth > _aspectRatio * originalHeight)
		? int(std::round(_aspectRatio * originalHeight))
		: originalWidth;
	auto height = (originalWidth > _aspectRatio * originalHeight)
		? originalHeight
		: int(std::round(originalHeight / _aspectRatio));
	if ((width >= originalWidth && height >= originalHeight) || !width || !height) {
		_broadcaster.OnFrame(frame);
		return;
	}

	width &= ~int(1);
	height &= ~int(1);
	const auto left = (originalWidth - width) / 2;
	const auto top = (originalHeight - height) / 2;
	rtc::scoped_refptr<webrtc::I420Buffer> croppedBuffer =
		webrtc::I420Buffer::Create(width, height);
	croppedBuffer->CropAndScaleFrom(
		*frame.video_frame_buffer()->ToI420(),
		left,
		top,
		width,
		height);
	webrtc::VideoFrame::Builder croppedBuilder =
		webrtc::VideoFrame::Builder()
		.set_video_frame_buffer(croppedBuffer)
		.set_rotation(webrtc::kVideoRotation_0)
		.set_timestamp_us(frame.timestamp_us())
		.set_id(frame.id());
	if (frame.has_update_rect()) {
		croppedBuilder.set_update_rect(frame.update_rect().ScaleWithFrame(
			frame.width(),
			frame.height(),
			left,
			top,
			width,
			height,
			width,
			height));
	}
	_broadcaster.OnFrame(croppedBuilder.build());
}

void VideoCameraCapturer::AddOrUpdateSink(
		rtc::VideoSinkInterface<webrtc::VideoFrame> *sink,
		const rtc::VideoSinkWants &wants) {
	_broadcaster.AddOrUpdateSink(sink, wants);
	updateVideoAdapter();
}

void VideoCameraCapturer::RemoveSink(rtc::VideoSinkInterface<webrtc::VideoFrame> *sink) {
	_broadcaster.RemoveSink(sink);
	updateVideoAdapter();
}

void VideoCameraCapturer::updateVideoAdapter() {
	//_videoAdapter.OnSinkWants(_broadcaster.wants());
}

}  // namespace tgcalls
