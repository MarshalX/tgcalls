#ifndef TGCALLS_AUDIO_DEVICE_HELPER_H
#define TGCALLS_AUDIO_DEVICE_HELPER_H

#include <string>

namespace webrtc {
class AudioDeviceModule;
} // namespace webrtc

namespace tgcalls {

void SetAudioInputDeviceById(webrtc::AudioDeviceModule *adm, const std::string &id);
void SetAudioOutputDeviceById(webrtc::AudioDeviceModule *adm, const std::string &id);

void ReinitAudioInputDevice(webrtc::AudioDeviceModule *adm);
void ReinitAudioOutputDevice(webrtc::AudioDeviceModule *adm);

} // namespace tgcalls

#endif
