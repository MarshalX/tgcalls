#include "PythonVideoTrackSource.h"


class PythonVideoSource : public rtc::VideoSourceInterface<webrtc::VideoFrame> {
public:
  PythonVideoSource(std::unique_ptr<PythonSource> source, int fps) {
    // TODO rewrite this thread
    _data = std::make_shared<Data>();
    _data->is_running = true;

    std::thread([fps, data = _data, source = std::move(source)] {
      std::uint32_t step = 0;
      while (data->is_running) {
        step++;

        std::this_thread::sleep_for(std::chrono::milliseconds(1000 / fps));
        auto frame = source->next_frame();

        frame.set_id(static_cast<std::uint16_t>(step));
        frame.set_timestamp_us(rtc::TimeMicros());

        data->broadcaster.OnFrame(frame);
      }
    }).detach();
  }

  ~PythonVideoSource() {
    _data->is_running = false;
  }

  using VideoFrameT = webrtc::VideoFrame;
  void AddOrUpdateSink(rtc::VideoSinkInterface<VideoFrameT> *sink, const rtc::VideoSinkWants &wants) override {
    _data->broadcaster.AddOrUpdateSink(sink, wants);
  }

  // TODO
  // RemoveSink must guarantee that at the time the method returns,
  // there is no current and no future calls to VideoSinkInterface::OnFrame.
  void RemoveSink(rtc::VideoSinkInterface<VideoFrameT> *sink) {
    _data->broadcaster.RemoveSink(sink);
  }

private:
  struct Data {
    std::atomic<bool> is_running;
    rtc::VideoBroadcaster broadcaster;
  };
  std::shared_ptr<Data> _data;
};

class PythonVideoSourceImpl : public webrtc::VideoTrackSource {
public:
  static rtc::scoped_refptr<PythonVideoSourceImpl> Create(std::unique_ptr<PythonSource> source, int fps) {
    return rtc::scoped_refptr<PythonVideoSourceImpl>(new rtc::RefCountedObject<PythonVideoSourceImpl>(std::move(source), fps));
  }

  explicit PythonVideoSourceImpl(std::unique_ptr<PythonSource> source, int fps) :
    VideoTrackSource(false), source_(std::move(source), fps) {
  }

protected:
  PythonVideoSource source_;
  rtc::VideoSourceInterface<webrtc::VideoFrame> *source() override {
    return &source_;
  }
};

std::function<webrtc::VideoTrackSourceInterface*()> PythonVideoTrackSource::create(std::unique_ptr<PythonSource> frame_source, int fps) {
  auto source = PythonVideoSourceImpl::Create(std::move(frame_source), fps);
  return [source] {
    return source.get();
  };
}

rtc::scoped_refptr<webrtc::VideoTrackSourceInterface> PythonVideoTrackSource::createPtr(std::unique_ptr<PythonSource> frame_source, int fps) {
  return PythonVideoSourceImpl::Create(std::move(frame_source), fps);
}
