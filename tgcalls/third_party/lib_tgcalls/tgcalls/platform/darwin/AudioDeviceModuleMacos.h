
#ifndef TGCALLS_AUDIO_DEVICE_MODULE_MACOS
#define TGCALLS_AUDIO_DEVICE_MODULE_MACOS

#include "platform/PlatformInterface.h"

namespace tgcalls {

class AudioDeviceModuleMacos : public DefaultWrappedAudioDeviceModule {
public:
    AudioDeviceModuleMacos(rtc::scoped_refptr<webrtc::AudioDeviceModule> impl) :
    DefaultWrappedAudioDeviceModule(impl) {
    }

    virtual ~AudioDeviceModuleMacos() {
    }

    virtual void Stop() override {
        WrappedInstance()->StopPlayout();
        WrappedInstance()->StopRecording();
        WrappedInstance()->Terminate();
    }
};

}

#endif
