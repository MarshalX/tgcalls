#include "WrappedAudioDeviceModuleImpl.h"

rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl>
WrappedAudioDeviceModuleImpl::Create(
    AudioLayer audio_layer, webrtc::TaskQueueFactory *task_queue_factory,
    std::shared_ptr<FileAudioDeviceDescriptor> fileAudioDeviceDescriptor) {
  RTC_LOG(INFO) << __FUNCTION__;
  return WrappedAudioDeviceModuleImpl::CreateForTest(
      audio_layer, task_queue_factory, std::move(fileAudioDeviceDescriptor));
}

rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl>
WrappedAudioDeviceModuleImpl::Create(
    AudioLayer audio_layer, webrtc::TaskQueueFactory *task_queue_factory,
    std::shared_ptr<RawAudioDeviceDescriptor> rawAudioDeviceDescriptor) {
  RTC_LOG(INFO) << __FUNCTION__;
  return WrappedAudioDeviceModuleImpl::CreateForTest(
      audio_layer, task_queue_factory, std::move(rawAudioDeviceDescriptor));
}

rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl>
WrappedAudioDeviceModuleImpl::CreateForTest(
    AudioLayer audio_layer, webrtc::TaskQueueFactory *task_queue_factory,
    std::shared_ptr<FileAudioDeviceDescriptor> fileAudioDeviceDescriptor) {
  RTC_LOG(INFO) << __FUNCTION__;

  // Create the generic reference counted (platform independent) implementation.
  rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl> audioDevice(
      new rtc::RefCountedObject<webrtc::AudioDeviceModuleImpl>(
          audio_layer, task_queue_factory));

  // Ensure that the current platform is supported.
  if (audioDevice->CheckPlatform() == -1) {
    return nullptr;
  }

  audioDevice->ResetAudioDevice(new FileAudioDevice(std::move(fileAudioDeviceDescriptor)));

  // Ensure that the generic audio buffer can communicate with the platform
  // specific parts.
  if (audioDevice->AttachAudioBuffer() == -1) {
    return nullptr;
  }

  return audioDevice;
}

rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl>
WrappedAudioDeviceModuleImpl::CreateForTest(
    AudioLayer audio_layer, webrtc::TaskQueueFactory *task_queue_factory,
    std::shared_ptr<RawAudioDeviceDescriptor> rawAudioDeviceDescriptor) {
  RTC_LOG(INFO) << __FUNCTION__;

  // Create the generic reference counted (platform independent) implementation.
  rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl> audioDevice(
      new rtc::RefCountedObject<webrtc::AudioDeviceModuleImpl>(
          audio_layer, task_queue_factory));

  // Ensure that the current platform is supported.
  if (audioDevice->CheckPlatform() == -1) {
    return nullptr;
  }

  audioDevice->ResetAudioDevice(new RawAudioDevice(std::move(rawAudioDeviceDescriptor)));

  // Ensure that the generic audio buffer can communicate with the platform
  // specific parts.
  if (audioDevice->AttachAudioBuffer() == -1) {
    return nullptr;
  }

  return audioDevice;
}

// TODO rewrite this shit (duplication)