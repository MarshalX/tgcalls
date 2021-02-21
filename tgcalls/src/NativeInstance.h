#pragma once

#include <pybind11/pybind11.h>
#include "InstanceHolder.h"
#include "RtcServer.h"

namespace py = pybind11;

class NativeInstance {
public:
    InstanceHolder instanceHolder;

    std::function<void(const std::vector<uint8_t> &data)> signalingDataEmittedCallback;
    std::function<void(const tgcalls::GroupJoinPayload &payload)> emitJoinPayloadCallback;

    NativeInstance();

    void startCall(vector<RtcServer> servers, std::array<uint8_t, 256> authKey, bool isOutgoing, std::string logPath);
    void startGroupCall(bool useFileAudioDevice,
                        std::function<std::string()> &getInputFilename,
                        std::function<std::string()> &getOutputFilename);
    void stopGroupCall() const;

    void setIsMuted(bool isMuted) const;

    void reinitAudioInputDevice() const;
    void reinitAudioOutputDevice() const;

    void setAudioOutputDevice(std::string id) const;
    void setAudioInputDevice(std::string id) const;

    void removeSsrcs(std::vector<uint32_t> ssrcs);

    void receiveSignalingData(std::vector<uint8_t> &data) const;
    void setJoinResponsePayload(tgcalls::GroupJoinResponsePayload payload) const;
    void setSignalingDataEmittedCallback(const std::function<void(const std::vector<uint8_t> &data)> &f);
    void setEmitJoinPayloadCallback(const std::function<void(const tgcalls::GroupJoinPayload &payload)> &f);
};
