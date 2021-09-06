#include "PythonSource.h"


PythonSource::PythonSource(std::function<std::string()> getNextFrameBuffer, int fps, int width, int height):
  _fps(fps), _width(width), _height(height) {
  _getNextFrameBuffer = std::move(getNextFrameBuffer);
}

webrtc::VideoFrame PythonSource::next_frame() {
  auto *frame = new std::string{_getNextFrameBuffer()};

  rtc::scoped_refptr<webrtc::I420Buffer> buffer = webrtc::I420Buffer::Create(_width, _height);

  libyuv::ABGRToI420((uint8_t *) frame->data(), _width * 4,
                     buffer->MutableDataY(), buffer->StrideY(),
                     buffer->MutableDataU(), buffer->StrideU(),
                     buffer->MutableDataV(), buffer->StrideV(),
                     _width, _height);

  delete frame;

  return webrtc::VideoFrame::Builder()
  .set_video_frame_buffer(buffer->Scale(_required_width, _required_height))
  .build();
}
