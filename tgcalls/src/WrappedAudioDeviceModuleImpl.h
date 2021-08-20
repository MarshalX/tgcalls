#pragma once

#include <rtc_base/logging.h>
#include <rtc_base/ref_counted_object.h>
#include <modules/audio_device/audio_device_impl.h>

#include "FileAudioDevice.h"
#include "FileAudioDeviceDescriptor.h"
#include "RawAudioDevice.h"
#include "RawAudioDeviceDescriptor.h"

namespace rtc {
  class PlatformThread;
}  // namespace rtc

class WrappedAudioDeviceModuleImpl : public webrtc::AudioDeviceModule {
public:
  static rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl> Create(
      AudioLayer,
      webrtc::TaskQueueFactory *,
      std::shared_ptr<FileAudioDeviceDescriptor>);

  static rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl> Create(
      AudioLayer,
      webrtc::TaskQueueFactory *,
      std::shared_ptr<RawAudioDeviceDescriptor>);

  static rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl> CreateForTest(
      AudioLayer,
      webrtc::TaskQueueFactory *,
      std::shared_ptr<FileAudioDeviceDescriptor>);

  static rtc::scoped_refptr<webrtc::AudioDeviceModuleImpl> CreateForTest(
      AudioLayer,
      webrtc::TaskQueueFactory *,
      std::shared_ptr<RawAudioDeviceDescriptor>);
};
