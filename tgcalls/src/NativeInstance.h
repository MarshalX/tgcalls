#pragma once

#include <pybind11/pybind11.h>

#include <modules/audio_device/include/audio_device.h>
#include <tgcalls/ThreadLocalObject.h>

#include "config.h"
#include "InstanceHolder.h"
#include "RtcServer.h"
#include "WrappedAudioDeviceModuleImpl.h"

namespace py = pybind11;

class NativeInstance {
public:
    std::unique_ptr<InstanceHolder> instanceHolder;

    bool _logToStdErr;
    string _logPath;

    int _outgoingAudioBitrateKbit = 128;

    std::function<void(const std::vector<uint8_t> &data)> signalingDataEmittedCallback;

    std::function<void(tgcalls::GroupJoinPayload payload)> _emitJoinPayloadCallback = nullptr;
    std::function<void(bool)> _networkStateUpdated = nullptr;

    std::shared_ptr<FileAudioDeviceDescriptor> _fileAudioDeviceDescriptor;
    std::shared_ptr<RawAudioDeviceDescriptor> _rawAudioDeviceDescriptor;

    NativeInstance(bool, string);
    ~NativeInstance();

    void startCall(vector<RtcServer> servers, std::array<uint8_t, 256> authKey, bool isOutgoing, std::string logPath);

    void setupGroupCall(
            std::function<void(tgcalls::GroupJoinPayload)> &,
            std::function<void(bool)> &,
            int
    );

    void startGroupCall(std::shared_ptr<FileAudioDeviceDescriptor>);
    void startGroupCall(std::shared_ptr<RawAudioDeviceDescriptor>);
    void startGroupCall(std::string, std::string);
    void stopGroupCall() const;
    bool isGroupCallNativeCreated() const;

    void setIsMuted(bool isMuted) const;
    void setVolume(uint32_t ssrc, double volume) const;
    void emitJoinPayload(std::function<void(tgcalls::GroupJoinPayload payload)> const &) const;
    void setConnectionMode(tgcalls::GroupConnectionMode, bool) const;

    void restartAudioInputDevice() const;
    void restartAudioOutputDevice() const;

    void stopAudioDeviceModule() const;
    void startAudioDeviceModule() const;

    std::vector<tgcalls::GroupInstanceInterface::AudioDevice> getPlayoutDevices() const;
    std::vector<tgcalls::GroupInstanceInterface::AudioDevice> getRecordingDevices() const;

    void setAudioOutputDevice(std::string id) const;
    void setAudioInputDevice(std::string id) const;

    void receiveSignalingData(std::vector<uint8_t> &data) const;
    void setJoinResponsePayload(std::string const &) const;
    void setSignalingDataEmittedCallback(const std::function<void(const std::vector<uint8_t> &data)> &f);

private:
    void createInstanceHolder(
        std::function<rtc::scoped_refptr<webrtc::AudioDeviceModule>(webrtc::TaskQueueFactory*)>,
        std::string,
        std::string
    );
};
