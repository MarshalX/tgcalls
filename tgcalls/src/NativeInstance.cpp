#include <rtc_base/ssl_adapter.h>
#include <tgcalls/InstanceImpl.h>
#include <tgcalls/group/GroupInstanceImpl.h>

#include "NativeInstance.h"

namespace py = pybind11;

std::string license = "GNU Lesser General Public License v3 (LGPLv3)";
std::string copyright = "Copyright (C) 2020-2021 Il`ya (Marshal) <https://github.com/MarshalX>";
auto noticeDisplayed = false;


NativeInstance::NativeInstance() {
    if (!noticeDisplayed) {
        py::print("tgcalls BETA, " + copyright);
        py::print("Licensed under the terms of the " + license + "\n\n");

        noticeDisplayed = true;
    }
    rtc::InitializeSSL();
    tgcalls::Register<tgcalls::InstanceImpl>();
}

NativeInstance::~NativeInstance() {}

void NativeInstance::startGroupCall(bool logToStdErr,
                                    string logPath,
                                    bool useFileAudioDevice,
                                    std::function<void(tgcalls::GroupJoinPayload)> &emitJoinPayloadCallback,
                                    std::function<void(bool)> &networkStateUpdated,
                                    std::function<void(std::vector<uint32_t> const &)> &participantDescriptionsRequired,
                                    std::function<std::string()> &getInputFilename,
                                    std::function<std::string()> &getOutputFilename) {
    // TODO move to the constructor
    _emitJoinPayloadCallback = emitJoinPayloadCallback;
    _networkStateUpdated = networkStateUpdated;
    _participantDescriptionsRequired = participantDescriptionsRequired;

    _getInputFilename = getInputFilename;
    _getOutputFilename = getOutputFilename;

    tgcalls::GroupInstanceDescriptor descriptor {
        .config = tgcalls::GroupConfig {
            .logPath = {std::move(logPath)},
            .logToStdErr = logToStdErr,
        },
        .networkStateUpdated = [=](bool is_connected) {
            _networkStateUpdated(is_connected);
        },
        .audioLevelsUpdated = [=](tgcalls::GroupLevelsUpdate const &update) {}, // TODO
        .useFileAudioDevice = useFileAudioDevice,
        .getInputFilename = [=]() {
            return _getInputFilename();
        },
        .getOutputFilename = [=]() {
            return _getOutputFilename();
        },
        .participantDescriptionsRequired = [=](std::vector<uint32_t> const &ssrcs) {
            _participantDescriptionsRequired(ssrcs);
        },
    };

    instanceHolder = std::make_unique<InstanceHolder>();
    instanceHolder->groupNativeInstance = std::make_unique<tgcalls::GroupInstanceImpl>(std::move(descriptor));
    instanceHolder->groupNativeInstance->emitJoinPayload([=](tgcalls::GroupJoinPayload payload) {
        _emitJoinPayloadCallback(std::move(payload));
    });
};

void NativeInstance::stopGroupCall() const {
//    instanceHolder->groupNativeInstance->stop();
// thank u tdesktop
    instanceHolder->groupNativeInstance.reset();
}

void NativeInstance::setJoinResponsePayload(tgcalls::GroupJoinResponsePayload payload, std::vector<tgcalls::GroupParticipantDescription> &&participants) const {
    instanceHolder->groupNativeInstance->setJoinResponsePayload(std::move(payload), std::move(participants));
}

void NativeInstance::setIsMuted(bool isMuted) const {
    instanceHolder->groupNativeInstance->setIsMuted(isMuted);
}

void NativeInstance::setVolume(uint32_t ssrc, double volume) const {
    instanceHolder->groupNativeInstance->setVolume(ssrc, volume);
}

void NativeInstance::reinitAudioInputDevice() const {
    instanceHolder->groupNativeInstance->reinitAudioInputDevice();
}

void NativeInstance::reinitAudioOutputDevice() const {
    instanceHolder->groupNativeInstance->reinitAudioOutputDevice();
}

void NativeInstance::setAudioOutputDevice(std::string id) const {
    instanceHolder->groupNativeInstance->setAudioOutputDevice(std::move(id));
}

void NativeInstance::setAudioInputDevice(std::string id) const {
    instanceHolder->groupNativeInstance->setAudioInputDevice(std::move(id));
}

void NativeInstance::removeSsrcs(std::vector<uint32_t> ssrcs) const {
    instanceHolder->groupNativeInstance->removeSsrcs(std::move(ssrcs));
}

void NativeInstance::addParticipants(std::vector<tgcalls::GroupParticipantDescription> &&participants) const {
    instanceHolder->groupNativeInstance->addParticipants(std::move(participants));
}

void NativeInstance::startCall(vector<RtcServer> servers, std::array<uint8_t, 256> authKey, bool isOutgoing, string logPath) {
    auto encryptionKeyValue = std::make_shared<std::array<uint8_t, 256>>();
    std::memcpy(encryptionKeyValue->data(), &authKey, 256);

    std::shared_ptr<tgcalls::VideoCaptureInterface> videoCapture = nullptr;

    tgcalls::MediaDevicesConfig mediaConfig = {
            .audioInputId = "VB-Cable",
//            .audioInputId = "default (Built-in Input)",
            .audioOutputId = "default (Built-in Output)",
//            .audioInputId = "0",
//            .audioOutputId = "0",
            .inputVolume = 1.f,
            .outputVolume = 1.f
    };

    tgcalls::Descriptor descriptor = {
            .config = tgcalls::Config{
                    .initializationTimeout = 1000,
                    .receiveTimeout = 1000,
                    .dataSaving = tgcalls::DataSaving::Never,
                    .enableP2P = false,
                    .allowTCP = false,
                    .enableStunMarking = true,
                    .enableAEC = true,
                    .enableNS = true,
                    .enableAGC = true,
                    .enableVolumeControl = true,
                    .logPath = {std::move(logPath)},
                    .statsLogPath = {"/Users/marshal/projects/tgcalls/python-binding/pytgcalls/tgcalls-stat.txt"},
                    .maxApiLayer = 92,
                    .enableHighBitrateVideo = false,
                    .preferredVideoCodecs = std::vector<std::string>(),
                    .protocolVersion = tgcalls::ProtocolVersion::V0
//                .preferredVideoCodecs = {cricket::kVp9CodecName}
            },
            .persistentState = {std::vector<uint8_t>()},
//            .initialNetworkType = tgcalls::NetworkType::WiFi,
            .encryptionKey = tgcalls::EncryptionKey(encryptionKeyValue, isOutgoing),
            .mediaDevicesConfig = mediaConfig,
            .videoCapture = videoCapture,
            .stateUpdated = [=](tgcalls::State state) {
//                py::print("stateUpdated");
            },
            .signalBarsUpdated = [=](int count) {
//                py::print("signalBarsUpdated");
            },
            .audioLevelUpdated = [=](float level) {
//                py::print("audioLevelUpdated");
            },
            .remoteBatteryLevelIsLowUpdated = [=](bool isLow) {
//                py::print("remoteBatteryLevelIsLowUpdated");
            },
            .remoteMediaStateUpdated = [=](tgcalls::AudioState audioState, tgcalls::VideoState videoState) {
//                py::print("remoteMediaStateUpdated");
            },
            .remotePrefferedAspectRatioUpdated = [=](float ratio) {
//                py::print("remotePrefferedAspectRatioUpdated");
            },
            .signalingDataEmitted = [=](const std::vector<uint8_t> &data) {
//                py::print("signalingDataEmitted");
                signalingDataEmittedCallback(data);
            },
    };

    for (int i = 0, size = servers.size(); i < size; ++i) {
        RtcServer rtcServer = std::move(servers.at(i));

        const auto host = rtcServer.ip;
        const auto hostv6 = rtcServer.ipv6;
        const auto port = uint16_t(rtcServer.port);

        if (rtcServer.isStun) {
            const auto pushStun = [&](const string &host) {
                descriptor.rtcServers.push_back(tgcalls::RtcServer{
                    .host = host,
                    .port = port,
                    .isTurn = false
                });
            };
            pushStun(host);
            pushStun(hostv6);

//            descriptor.rtcServers.push_back(rtcServer.toTgcalls(false, false));
//            descriptor.rtcServers.push_back(rtcServer.toTgcalls(true, false));
        }

//        && !rtcServer.login.empty() && !rtcServer.password.empty()
        const auto username = rtcServer.login;
        const auto password = rtcServer.password;
        if (rtcServer.isTurn) {
            const auto pushTurn = [&](const string &host) {
                descriptor.rtcServers.push_back(tgcalls::RtcServer{
                    .host = host,
                    .port = port,
                    .login = username,
                    .password = password,
                    .isTurn = true,
                });
            };
            pushTurn(host);
            pushTurn(hostv6);

//            descriptor.rtcServers.push_back(rtcServer.toTgcalls());
//            descriptor.rtcServers.push_back(rtcServer.toTgcalls(true));
        }
    }

    instanceHolder = std::make_unique<InstanceHolder>();
    instanceHolder->nativeInstance = tgcalls::Meta::Create("3.0.0", std::move(descriptor));
    instanceHolder->_videoCapture = videoCapture;
    instanceHolder->nativeInstance->setNetworkType(tgcalls::NetworkType::WiFi);
    instanceHolder->nativeInstance->setRequestedVideoAspect(1);
    instanceHolder->nativeInstance->setMuteMicrophone(false);
}

void NativeInstance::receiveSignalingData(std::vector<uint8_t> &data) const {
    instanceHolder->nativeInstance->receiveSignalingData(data);
}

void NativeInstance::setSignalingDataEmittedCallback(const std::function<void(const std::vector<uint8_t> &data)> &f) {
//    py::print("setSignalingDataEmittedCallback");
    signalingDataEmittedCallback = f;
}
