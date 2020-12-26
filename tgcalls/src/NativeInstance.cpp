#include <rtc_base/ssl_adapter.h>
#include <tgcalls/InstanceImpl.h>
#include <tgcalls/group/GroupInstanceImpl.h>
#include "NativeInstance.h"


NativeInstance::NativeInstance() {
//    rtc::InitializeSSL();
//    tgcalls::Register<tgcalls::InstanceImpl>();
}

void NativeInstance::startGroupCall() {
    tgcalls::GroupInstanceDescriptor descriptor {
        .networkStateUpdated = [=](bool state) {},
        .audioLevelsUpdated = [=](tgcalls::GroupLevelsUpdate const &update) {},
    };

    InstanceHolder holder = InstanceHolder();
    holder.groupNativeInstance = std::make_unique<tgcalls::GroupInstanceImpl>(std::move(descriptor));
    holder.groupNativeInstance->emitJoinPayload(emitJoinPayloadCallback);
    instanceHolder = std::move(holder);
};

void NativeInstance::setEmitJoinPayloadCallback(const std::function<void(const tgcalls::GroupJoinPayload &payload)> &f) {
    emitJoinPayloadCallback = f;
}

void NativeInstance::setJoinResponsePayload(tgcalls::GroupJoinResponsePayload payload) {
    instanceHolder.groupNativeInstance->setJoinResponsePayload(payload);
}

void NativeInstance::setIsMuted(bool isMuted) {
    instanceHolder.groupNativeInstance->setIsMuted(isMuted);
}

void NativeInstance::setAudioOutputDevice(std::string id) {
    instanceHolder.groupNativeInstance->setAudioOutputDevice(id);
}

void NativeInstance::setAudioInputDevice(std::string id) {
    instanceHolder.groupNativeInstance->setAudioInputDevice(id);
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
                    .logPath = {logPath},
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

    InstanceHolder holder = InstanceHolder();
    holder.nativeInstance = tgcalls::Meta::Create("3.0.0", std::move(descriptor));
    holder._videoCapture = videoCapture;
    holder.nativeInstance.get()->setNetworkType(tgcalls::NetworkType::WiFi);
    holder.nativeInstance.get()->setRequestedVideoAspect(1);
    holder.nativeInstance.get()->setMuteMicrophone(false);

    instanceHolder = std::move(holder);
}

void NativeInstance::receiveSignalingData(std::vector<uint8_t> &data) {
//    py::print("receiveSignalingData");
    instanceHolder.nativeInstance->receiveSignalingData(data);
}

void NativeInstance::setSignalingDataEmittedCallback(const std::function<void(const std::vector<uint8_t> &data)> &f) {
//    py::print("setSignalingDataEmittedCallback");
    signalingDataEmittedCallback = f;
}
