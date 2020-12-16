#pragma once

#include <pybind11/pybind11.h>
#include "InstanceHolder.h"
#include "RtcServer.h"

namespace py = pybind11;

class NativeInstance {
public:
    InstanceHolder instanceHolder;

    vector<RtcServer> rtcServers;
    std::array<uint8_t, 256> authKey;
    bool isOutgoing;
    std::string logPath;

    std::function<void(const std::vector<uint8_t> &data)> signalingDataEmittedCallback;

    NativeInstance(vector<RtcServer> servers, std::array<uint8_t, 256> authKey, bool isOutgoing, std::string logPath);

    void start();

    void receiveSignalingData(std::vector<uint8_t> &data);
    void setSignalingDataEmittedCallback(const std::function<void(const std::vector<uint8_t> &data)> &f);
};
