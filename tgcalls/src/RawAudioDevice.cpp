#include "RawAudioDevice.h"

#include <cstring>

#include <modules/audio_device/audio_device_impl.h>
#include <rtc_base/ref_counted_object.h>
#include <rtc_base/checks.h>
#include <rtc_base/logging.h>
#include <rtc_base/platform_thread.h>
#include <rtc_base/time_utils.h>
#include <system_wrappers/include/sleep.h>

// TODO set from Python
const int kRecordingFixedSampleRate = 48000;
const size_t kRecordingNumChannels = 2;
const int kPlayoutFixedSampleRate = 48000;
const size_t kPlayoutNumChannels = 2;
const size_t kPlayoutBufferSize =
    kPlayoutFixedSampleRate / 100 * kPlayoutNumChannels * 2;
const size_t kRecordingBufferSize =
    kRecordingFixedSampleRate / 100 * kRecordingNumChannels * 2;

RawAudioDevice::RawAudioDevice(std::shared_ptr<RawAudioDeviceDescriptor> RawAudioDeviceDescriptor)
    : _ptrAudioBuffer(nullptr),
      _recordingBuffer(nullptr),
      _playoutBuffer(nullptr),
      _playoutFramesLeft(0),
      _recordingBufferSizeIn10MS(0),
      _recordingFramesIn10MS(0),
      _playoutFramesIn10MS(0),
      _playing(false),
      _recording(false),
      _lastCallPlayoutMillis(0),
      _lastCallRecordMillis(0),
      _rawAudioDeviceDescriptor(std::move(RawAudioDeviceDescriptor)) {}

RawAudioDevice::~RawAudioDevice() = default;

int32_t RawAudioDevice::ActiveAudioLayer(
    webrtc::AudioDeviceModule::AudioLayer &audioLayer) const {
  return -1;
}

webrtc::AudioDeviceGeneric::InitStatus RawAudioDevice::Init() {
  return InitStatus::OK;
}

int32_t RawAudioDevice::Terminate() {
  return 0;
}

bool RawAudioDevice::Initialized() const {
  return true;
}

int16_t RawAudioDevice::PlayoutDevices() {
  return 1;
}

int16_t RawAudioDevice::RecordingDevices() {
  return 1;
}

int32_t RawAudioDevice::PlayoutDeviceName(uint16_t index,
                                           char name[webrtc::kAdmMaxDeviceNameSize],
                                           char guid[webrtc::kAdmMaxGuidSize]) {
  const char *kName = "dummy_device";
  const char *kGuid = "dummy_device_unique_id";
  if (index < 1) {
    memset(name, 0, webrtc::kAdmMaxDeviceNameSize);
    memset(guid, 0, webrtc::kAdmMaxGuidSize);
    memcpy(name, kName, strlen(kName));
    memcpy(guid, kGuid, strlen(guid));
    return 0;
  }
  return -1;
}

int32_t RawAudioDevice::RecordingDeviceName(uint16_t index,
                                             char name[webrtc::kAdmMaxDeviceNameSize],
                                             char guid[webrtc::kAdmMaxGuidSize]) {
  const char *kName = "dummy_device";
  const char *kGuid = "dummy_device_unique_id";
  if (index < 1) {
    memset(name, 0, webrtc::kAdmMaxDeviceNameSize);
    memset(guid, 0, webrtc::kAdmMaxGuidSize);
    memcpy(name, kName, strlen(kName));
    memcpy(guid, kGuid, strlen(guid));
    return 0;
  }
  return -1;
}

int32_t RawAudioDevice::SetPlayoutDevice(uint16_t index) {
  if (index == 0) {
    _playout_index = index;
    return 0;
  }
  return -1;
}

int32_t RawAudioDevice::SetPlayoutDevice(
    webrtc::AudioDeviceModule::WindowsDeviceType device) {
  return -1;
}

int32_t RawAudioDevice::SetRecordingDevice(uint16_t index) {
  if (index == 0) {
    _record_index = index;
    return _record_index;
  }
  return -1;
}

int32_t RawAudioDevice::SetRecordingDevice(
    webrtc::AudioDeviceModule::WindowsDeviceType device) {
  return -1;
}

int32_t RawAudioDevice::PlayoutIsAvailable(bool &available) {
  if (_playout_index == 0) {
    available = true;
    return _playout_index;
  }
  available = false;
  return -1;
}

int32_t RawAudioDevice::InitPlayout() {
  webrtc::MutexLock lock(&mutex_);

  if (_playing) {
    return -1;
  }

  _playoutFramesIn10MS = static_cast<size_t>(kPlayoutFixedSampleRate / 100);

  if (_ptrAudioBuffer) {
    _ptrAudioBuffer->SetPlayoutSampleRate(kPlayoutFixedSampleRate);
    _ptrAudioBuffer->SetPlayoutChannels(kPlayoutNumChannels);
  }
  return 0;
}

bool RawAudioDevice::PlayoutIsInitialized() const {
  return _playoutFramesIn10MS != 0;
}

int32_t RawAudioDevice::RecordingIsAvailable(bool &available) {
  if (_record_index == 0) {
    available = true;
    return _record_index;
  }
  available = false;
  return -1;
}

int32_t RawAudioDevice::InitRecording() {
  webrtc::MutexLock lock(&mutex_);

  if (_recording) {
    return -1;
  }

  _recordingFramesIn10MS = static_cast<size_t>(kRecordingFixedSampleRate / 100);

  if (_ptrAudioBuffer) {
    _ptrAudioBuffer->SetRecordingSampleRate(kRecordingFixedSampleRate);
    _ptrAudioBuffer->SetRecordingChannels(kRecordingNumChannels);
  }
  return 0;
}

bool RawAudioDevice::RecordingIsInitialized() const {
  return _recordingFramesIn10MS != 0;
}

int32_t RawAudioDevice::StartPlayout() {
  if (_playing) {
    return 0;
  }

  _playing = true;
  _playoutFramesLeft = 0;

  if (!_playoutBuffer) {
    _playoutBuffer = new int8_t[kPlayoutBufferSize];
  }
  if (!_playoutBuffer) {
    _playing = false;
    return -1;
  }

  _ptrThreadPlay.reset(new rtc::PlatformThread(
      PlayThreadFunc, this, "webrtc_audio_module_play_thread",
      rtc::kRealtimePriority));
  _ptrThreadPlay->Start();

  RTC_LOG(LS_INFO) << "Started playout capture Python callback";
  return 0;
}

int32_t RawAudioDevice::StopPlayout() {
  {
    webrtc::MutexLock lock(&mutex_);
    _playing = false;
  }
  // stop playout thread first
  if (_ptrThreadPlay) {
    _ptrThreadPlay->Stop();
    _ptrThreadPlay.reset();
  }

  webrtc::MutexLock lock(&mutex_);

  _playoutFramesLeft = 0;
  delete[] _playoutBuffer;
  _playoutBuffer = nullptr;

  RTC_LOG(LS_INFO) << "Stopped playout capture to Python";
  return 0;
}

bool RawAudioDevice::Playing() const {
  return _playing;
}

int32_t RawAudioDevice::StartRecording() {
  _recording = true;

  // Make sure we only create the buffer once.
  _recordingBufferSizeIn10MS = _recordingFramesIn10MS * kRecordingNumChannels * 2;
  if (!_recordingBuffer) {
    _recordingBuffer = new int8_t[_recordingBufferSizeIn10MS];
  }

  _ptrThreadRec.reset(new rtc::PlatformThread(
      RecThreadFunc, this, "webrtc_audio_module_capture_thread",
      rtc::kRealtimePriority));

  _ptrThreadRec->Start();

  RTC_LOG(LS_INFO) << "Started recording from Python";

  return 0;
}

int32_t RawAudioDevice::StopRecording() {
  {
    webrtc::MutexLock lock(&mutex_);
    _recording = false;
  }

  if (_ptrThreadRec) {
    _ptrThreadRec->Stop();
    _ptrThreadRec.reset();
  }

  webrtc::MutexLock lock(&mutex_);
  if (_recordingBuffer) {
    delete[] _recordingBuffer;
    _recordingBuffer = nullptr;
  }

  RTC_LOG(LS_INFO) << "Stopped recording from Python";
  return 0;
}

bool RawAudioDevice::Recording() const {
  return _recording;
}

int32_t RawAudioDevice::InitSpeaker() {
  return -1;
}

bool RawAudioDevice::SpeakerIsInitialized() const {
  return false;
}

int32_t RawAudioDevice::InitMicrophone() {
  return 0;
}

bool RawAudioDevice::MicrophoneIsInitialized() const {
  return true;
}

int32_t RawAudioDevice::SpeakerVolumeIsAvailable(bool &available) {
  return -1;
}

int32_t RawAudioDevice::SetSpeakerVolume(uint32_t volume) {
  return -1;
}

int32_t RawAudioDevice::SpeakerVolume(uint32_t &volume) const {
  return -1;
}

int32_t RawAudioDevice::MaxSpeakerVolume(uint32_t &maxVolume) const {
  return -1;
}

int32_t RawAudioDevice::MinSpeakerVolume(uint32_t &minVolume) const {
  return -1;
}

int32_t RawAudioDevice::MicrophoneVolumeIsAvailable(bool &available) {
  return -1;
}

int32_t RawAudioDevice::SetMicrophoneVolume(uint32_t volume) {
  return -1;
}

int32_t RawAudioDevice::MicrophoneVolume(uint32_t &volume) const {
  return -1;
}

int32_t RawAudioDevice::MaxMicrophoneVolume(uint32_t &maxVolume) const {
  return -1;
}

int32_t RawAudioDevice::MinMicrophoneVolume(uint32_t &minVolume) const {
  return -1;
}

int32_t RawAudioDevice::SpeakerMuteIsAvailable(bool &available) {
  return -1;
}

int32_t RawAudioDevice::SetSpeakerMute(bool enable) {
  return -1;
}

int32_t RawAudioDevice::SpeakerMute(bool &enabled) const {
  return -1;
}

int32_t RawAudioDevice::MicrophoneMuteIsAvailable(bool &available) {
  return -1;
}

int32_t RawAudioDevice::SetMicrophoneMute(bool enable) {
  return -1;
}

int32_t RawAudioDevice::MicrophoneMute(bool &enabled) const {
  return -1;
}

int32_t RawAudioDevice::StereoPlayoutIsAvailable(bool &available) {
  available = true;
  return 0;
}

int32_t RawAudioDevice::SetStereoPlayout(bool enable) {
  return 0;
}

int32_t RawAudioDevice::StereoPlayout(bool &enabled) const {
  enabled = true;
  return 0;
}

int32_t RawAudioDevice::StereoRecordingIsAvailable(bool &available) {
  available = true;
  return 0;
}

int32_t RawAudioDevice::SetStereoRecording(bool enable) {
  return 0;
}

int32_t RawAudioDevice::StereoRecording(bool &enabled) const {
  enabled = true;
  return 0;
}

int32_t RawAudioDevice::PlayoutDelay(uint16_t &delayMS) const {
  return 0;
}

void RawAudioDevice::AttachAudioBuffer(webrtc::AudioDeviceBuffer *audioBuffer) {
  webrtc::MutexLock lock(&mutex_);

  _ptrAudioBuffer = audioBuffer;
  _ptrAudioBuffer->SetRecordingSampleRate(0);
  _ptrAudioBuffer->SetPlayoutSampleRate(0);
  _ptrAudioBuffer->SetRecordingChannels(0);
  _ptrAudioBuffer->SetPlayoutChannels(0);
}

void RawAudioDevice::PlayThreadFunc(void *pThis) {
  auto *device = static_cast<RawAudioDevice *>(pThis);
  while (device->PlayThreadProcess()) {
  }
}

void RawAudioDevice::RecThreadFunc(void *pThis) {
  auto *device = static_cast<RawAudioDevice *>(pThis);
  while (device->RecThreadProcess()) {
  }
}

bool RawAudioDevice::PlayThreadProcess() {
  if (!_playing) {
    return false;
  }
  int64_t currentTime = rtc::TimeMillis();
  mutex_.Lock();

  if (_lastCallPlayoutMillis == 0 ||
      currentTime - _lastCallPlayoutMillis >= 10) {
    mutex_.Unlock();
    _ptrAudioBuffer->RequestPlayoutData(_playoutFramesIn10MS);
    mutex_.Lock();

    _playoutFramesLeft = _ptrAudioBuffer->GetPlayoutData(_playoutBuffer);
    RTC_DCHECK_EQ(_playoutFramesIn10MS, _playoutFramesLeft);
    if (!_rawAudioDeviceDescriptor->_isRecordingPaused()) {
      _rawAudioDeviceDescriptor->_setRecordedBuffer(_playoutBuffer, kPlayoutBufferSize);
    }
    _lastCallPlayoutMillis = currentTime;
  }
  _playoutFramesLeft = 0;
  mutex_.Unlock();

  int64_t deltaTimeMillis = rtc::TimeMillis() - currentTime;
  if (deltaTimeMillis < 10) {
    webrtc::SleepMs(10 - deltaTimeMillis);
  }

  return true;
}

bool RawAudioDevice::RecThreadProcess() {
  if (!_recording) {
    return false;
  }

  int64_t currentTime = rtc::TimeMillis();
  mutex_.Lock();

  if (_lastCallRecordMillis == 0 || currentTime - _lastCallRecordMillis >= 10) {
    if (!_rawAudioDeviceDescriptor->_isPlayoutPaused()) {
      auto recordingStringBuffer = _rawAudioDeviceDescriptor->_getPlayoutBuffer(kRecordingBufferSize);
//      in prev impl was setting of _recordingBuffer
      _ptrAudioBuffer->SetRecordedBuffer((int8_t *) recordingStringBuffer->data(), _recordingFramesIn10MS);

      _lastCallRecordMillis = currentTime;
      mutex_.Unlock();
      _ptrAudioBuffer->DeliverRecordedData();
      mutex_.Lock();

      delete recordingStringBuffer;
    }
  }

  mutex_.Unlock();

  int64_t deltaTimeMillis = rtc::TimeMillis() - currentTime;
  if (deltaTimeMillis < 10) {
    webrtc::SleepMs(10 - deltaTimeMillis);
  }

  return true;
}
