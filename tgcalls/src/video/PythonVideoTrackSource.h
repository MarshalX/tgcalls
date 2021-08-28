#pragma once

#include <thread>
#include <memory>
#include <functional>
#include <api/scoped_refptr.h>
#include <media/base/video_broadcaster.h>
#include <pc/video_track_source.h>
#include <libyuv.h>

#include "PythonSource.h"

namespace webrtc {
  class VideoTrackSourceInterface;
  class VideoFrame;
}

class PythonVideoTrackSource {
public:
  static std::function<webrtc::VideoTrackSourceInterface*()> create(std::unique_ptr<PythonSource> source, int fps);
  static rtc::scoped_refptr<webrtc::VideoTrackSourceInterface> createPtr(std::unique_ptr<PythonSource> source, int fps);
};
