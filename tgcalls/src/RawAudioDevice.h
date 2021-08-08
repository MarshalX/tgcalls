#include <cstdio>

#include <memory>
#include <string>

#include <modules/audio_device/audio_device_impl.h>
#include <modules/audio_device/audio_device_generic.h>
#include <rtc_base/synchronization/mutex.h>
#include <rtc_base/system/file_wrapper.h>
#include <rtc_base/time_utils.h>

#include "RawAudioDeviceDescriptor.h"

namespace rtc {
  class PlatformThread;
}

class RawAudioDevice : public webrtc::AudioDeviceGeneric {
public:
  explicit RawAudioDevice(std::shared_ptr<RawAudioDeviceDescriptor>);

  ~RawAudioDevice() override;

  int32_t ActiveAudioLayer(webrtc::AudioDeviceModule::AudioLayer &audioLayer) const override;

  InitStatus Init() override;

  int32_t Terminate() override;

  bool Initialized() const override;

  int16_t PlayoutDevices() override;

  int16_t RecordingDevices() override;

  int32_t PlayoutDeviceName(uint16_t index,
                            char name[webrtc::kAdmMaxDeviceNameSize],
                            char guid[webrtc::kAdmMaxGuidSize]) override;

  int32_t RecordingDeviceName(uint16_t index,
                              char name[webrtc::kAdmMaxDeviceNameSize],
                              char guid[webrtc::kAdmMaxGuidSize]) override;

  int32_t SetPlayoutDevice(uint16_t index) override;

  int32_t SetPlayoutDevice(webrtc::AudioDeviceModule::WindowsDeviceType device) override;

  int32_t SetRecordingDevice(uint16_t index) override;

  int32_t SetRecordingDevice(webrtc::AudioDeviceModule::WindowsDeviceType device) override;

  int32_t PlayoutIsAvailable(bool &available) override;

  int32_t InitPlayout() override;

  bool PlayoutIsInitialized() const override;

  int32_t RecordingIsAvailable(bool &available) override;

  int32_t InitRecording() override;

  bool RecordingIsInitialized() const override;

  // Audio transport control
  int32_t StartPlayout() override;

  int32_t StopPlayout() override;

  bool Playing() const override;

  int32_t StartRecording() override;

  int32_t StopRecording() override;

  bool Recording() const override;

  int32_t InitSpeaker() override;

  bool SpeakerIsInitialized() const override;

  int32_t InitMicrophone() override;

  bool MicrophoneIsInitialized() const override;

  int32_t SpeakerVolumeIsAvailable(bool &available) override;

  int32_t SetSpeakerVolume(uint32_t volume) override;

  int32_t SpeakerVolume(uint32_t &volume) const override;

  int32_t MaxSpeakerVolume(uint32_t &maxVolume) const override;

  int32_t MinSpeakerVolume(uint32_t &minVolume) const override;

  int32_t MicrophoneVolumeIsAvailable(bool &available) override;

  int32_t SetMicrophoneVolume(uint32_t volume) override;

  int32_t MicrophoneVolume(uint32_t &volume) const override;

  int32_t MaxMicrophoneVolume(uint32_t &maxVolume) const override;

  int32_t MinMicrophoneVolume(uint32_t &minVolume) const override;

  int32_t SpeakerMuteIsAvailable(bool &available) override;

  int32_t SetSpeakerMute(bool enable) override;

  int32_t SpeakerMute(bool &enabled) const override;

  int32_t MicrophoneMuteIsAvailable(bool &available) override;

  int32_t SetMicrophoneMute(bool enable) override;

  int32_t MicrophoneMute(bool &enabled) const override;

  int32_t StereoPlayoutIsAvailable(bool &available) override;

  int32_t SetStereoPlayout(bool enable) override;

  int32_t StereoPlayout(bool &enabled) const override;

  int32_t StereoRecordingIsAvailable(bool &available) override;

  int32_t SetStereoRecording(bool enable) override;

  int32_t StereoRecording(bool &enabled) const override;

  int32_t PlayoutDelay(uint16_t &delayMS) const override;

  void AttachAudioBuffer(webrtc::AudioDeviceBuffer *audioBuffer) override;

private:
  static void RecThreadFunc(void *);

  static void PlayThreadFunc(void *);

  bool RecThreadProcess();

  bool PlayThreadProcess();

  int32_t _playout_index;
  int32_t _record_index;
  webrtc::AudioDeviceBuffer *_ptrAudioBuffer;
  int8_t *_recordingBuffer;  // In bytes.
  int8_t *_playoutBuffer;    // In bytes.
  uint32_t _playoutFramesLeft;
  webrtc::Mutex mutex_;

  size_t _recordingBufferSizeIn10MS;
  size_t _recordingFramesIn10MS;
  size_t _playoutFramesIn10MS;

  std::unique_ptr<rtc::PlatformThread> _ptrThreadRec;
  std::unique_ptr<rtc::PlatformThread> _ptrThreadPlay;

  bool _playing;
  bool _recording;
  int64_t _lastCallPlayoutMillis;
  int64_t _lastCallRecordMillis;

  std::shared_ptr<RawAudioDeviceDescriptor> _rawAudioDeviceDescriptor;
};
