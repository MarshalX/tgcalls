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
    void startGroupCall();
    void stopGroupCall();

    void setIsMuted(bool isMuted);
    void setAudioOutputDevice(std::string id);
    void setAudioInputDevice(std::string id);

    void receiveSignalingData(std::vector<uint8_t> &data);
    void setJoinResponsePayload(tgcalls::GroupJoinResponsePayload payload);
    void setSignalingDataEmittedCallback(const std::function<void(const std::vector<uint8_t> &data)> &f);
    void setEmitJoinPayloadCallback(const std::function<void(const tgcalls::GroupJoinPayload &payload)> &f);
};
