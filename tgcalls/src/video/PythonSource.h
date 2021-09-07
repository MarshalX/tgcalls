#pragma once

#include <functional>
#include <memory>
#include <string>
#include <api/scoped_refptr.h>
#include <api/video/video_frame.h>
#include <api/video/i420_buffer.h>
#include <libyuv.h>


class PythonSource {
public:
  PythonSource(std::function<std::string()>, float, int, int);
  ~PythonSource() = default;

  webrtc::VideoFrame next_frame();

private:
  std::function<std::string()> _getNextFrameBuffer = nullptr;
  float _fps;
  int _width;
  int _height;

  int _required_width = 1280;
  int _required_height = 720;
};
