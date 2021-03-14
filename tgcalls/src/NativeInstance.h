#pragma once

#include <pybind11/pybind11.h>
#include "InstanceHolder.h"
#include "RtcServer.h"
#include "FileAudioDeviceDescriptor.h"

namespace py = pybind11;

class NativeInstance {
public:
    std::unique_ptr<InstanceHolder> instanceHolder;

    bool _logToStdErr;
    string _logPath;

    std::function<void(const std::vector<uint8_t> &data)> signalingDataEmittedCallback;

    std::function<void(tgcalls::GroupJoinPayload payload)> _emitJoinPayloadCallback = nullptr;
    std::function<void(bool)> _networkStateUpdated = nullptr;
    std::function<void(std::vector<uint32_t> const &)> _participantDescriptionsRequired = nullptr;

    FileAudioDeviceDescriptor _fileAudioDeviceDescriptor;

    NativeInstance(bool, string);
    ~NativeInstance();

    void startCall(vector<RtcServer> servers, std::array<uint8_t, 256> authKey, bool isOutgoing, std::string logPath);

    void setupGroupCall(
            std::function<void(tgcalls::GroupJoinPayload)> &,
            std::function<void(bool)> &,
            std::function<void(std::vector<uint32_t> const &)> &
    );

    void startGroupCall(FileAudioDeviceDescriptor &);
    void stopGroupCall() const;

    void setIsMuted(bool isMuted) const;
    void setVolume(uint32_t ssrc, double volume) const;
    void setConnectionMode(tgcalls::GroupConnectionMode, bool);

    void reinitAudioInputDevice() const;
    void reinitAudioOutputDevice() const;

    void setAudioOutputDevice(std::string id) const;
    void setAudioInputDevice(std::string id) const;

    void removeSsrcs(std::vector<uint32_t> ssrcs) const;
    void addParticipants(std::vector<tgcalls::GroupParticipantDescription> &&participants) const;

    void receiveSignalingData(std::vector<uint8_t> &data) const;
    void setJoinResponsePayload(tgcalls::GroupJoinResponsePayload payload, std::vector<tgcalls::GroupParticipantDescription> &&participants) const;
    void setSignalingDataEmittedCallback(const std::function<void(const std::vector<uint8_t> &data)> &f);
};
