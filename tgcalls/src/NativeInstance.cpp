#include <iostream>

#include <rtc_base/ssl_adapter.h>

#include "NativeInstance.h"

namespace py = pybind11;

auto noticeDisplayed = false;

NativeInstance::NativeInstance(bool logToStdErr, string logPath)
    : _logToStdErr(logToStdErr), _logPath(std::move(logPath)) {
  if (!noticeDisplayed) {
    auto ver = std::string(PROJECT_VER);
    auto dev = std::count(ver.begin(), ver.end(), '.') == 3 ? " DEV" : "";
    py::print("tgcalls v" + ver + dev + ", Copyright (C) 2020-2021 Il`ya (Marshal) <https://github.com/MarshalX>");
    py::print("Licensed under the terms of the GNU Lesser General Public License v3 (LGPLv3) \n\n");

    noticeDisplayed = true;
  }
  rtc::InitializeSSL();
//    tgcalls::Register<tgcalls::InstanceImpl>();
}

NativeInstance::~NativeInstance() = default;

void NativeInstance::setupGroupCall(
    std::function<void(tgcalls::GroupJoinPayload)> &emitJoinPayloadCallback,
    std::function<void(bool)> &networkStateUpdated,
    int outgoingAudioBitrateKbit) {
  _emitJoinPayloadCallback = emitJoinPayloadCallback;
  _networkStateUpdated = networkStateUpdated;
  _outgoingAudioBitrateKbit = outgoingAudioBitrateKbit;
}

void NativeInstance::createInstanceHolder(
    std::function<rtc::scoped_refptr<webrtc::AudioDeviceModule>(webrtc::TaskQueueFactory *)> createAudioDeviceModule,
    std::string initialInputDeviceId = "",
    std::string initialOutputDeviceId = ""
) {
  tgcalls::GroupInstanceDescriptor descriptor{
      .threads = tgcalls::StaticThreads::getThreads(),
      .config = tgcalls::GroupConfig{.need_log = true,
          .logPath = {std::move(_logPath)},
          .logToStdErr = _logToStdErr},
      .networkStateUpdated =
      [=](tgcalls::GroupNetworkState groupNetworkState) {
        _networkStateUpdated(groupNetworkState.isConnected);
      },
      .audioLevelsUpdated =
      [=](tgcalls::GroupLevelsUpdate const &update) {}, // its necessary for audio analyzing (VAD)
      .initialInputDeviceId = std::move(initialInputDeviceId),
      .initialOutputDeviceId = std::move(initialOutputDeviceId),
      .createAudioDeviceModule = std::move(createAudioDeviceModule),
      .outgoingAudioBitrateKbit=_outgoingAudioBitrateKbit,
      .disableOutgoingAudioProcessing=true,
      // deprecated
//      .participantDescriptionsRequired =
//      [=](std::vector<uint32_t> const &ssrcs) {
//        _participantDescriptionsRequired(ssrcs);
//      },
      //        .requestBroadcastPart = [=](int64_t time, int64_t period,
      //        std::function<void(tgcalls::BroadcastPart &&)> done) {},
  };

  instanceHolder = std::make_unique<InstanceHolder>();
  instanceHolder->groupNativeInstance = std::make_unique<tgcalls::GroupInstanceCustomImpl>(std::move(descriptor));
  instanceHolder->groupNativeInstance->emitJoinPayload(
      [=](tgcalls::GroupJoinPayload payload) {
        _emitJoinPayloadCallback(std::move(payload));
      }
  );
}

void NativeInstance::startGroupCall(std::shared_ptr<FileAudioDeviceDescriptor> fileAudioDeviceDescriptor) {
  _fileAudioDeviceDescriptor = std::move(fileAudioDeviceDescriptor);
  createInstanceHolder(
      [&](webrtc::TaskQueueFactory *taskQueueFactory) -> rtc::scoped_refptr<webrtc::AudioDeviceModule> {
        return WrappedAudioDeviceModuleImpl::Create(
            webrtc::AudioDeviceModule::kDummyAudio, taskQueueFactory, std::move(_fileAudioDeviceDescriptor)
        );
      });
}

void NativeInstance::startGroupCall(std::shared_ptr<RawAudioDeviceDescriptor> rawAudioDeviceDescriptor) {
  _rawAudioDeviceDescriptor = std::move(rawAudioDeviceDescriptor);
  createInstanceHolder(
      [&](webrtc::TaskQueueFactory *taskQueueFactory) -> rtc::scoped_refptr<webrtc::AudioDeviceModule> {
        return WrappedAudioDeviceModuleImpl::Create(
            webrtc::AudioDeviceModule::kDummyAudio, taskQueueFactory, std::move(_rawAudioDeviceDescriptor)
        );
      });
}

void NativeInstance::startGroupCall(std::string initialInputDeviceId = "", std::string initialOutputDeviceId = "") {
  createInstanceHolder(
      [&](webrtc::TaskQueueFactory *taskQueueFactory) -> rtc::scoped_refptr<webrtc::AudioDeviceModule> {
        return webrtc::AudioDeviceModule::Create(
            webrtc::AudioDeviceModule::kPlatformDefaultAudio, taskQueueFactory
        );
      }, std::move(initialInputDeviceId), std::move(initialOutputDeviceId));
}

void NativeInstance::stopGroupCall() const {
  instanceHolder->groupNativeInstance = nullptr;
}

bool NativeInstance::isGroupCallNativeCreated() const {
  return instanceHolder != nullptr && instanceHolder->groupNativeInstance != nullptr;
}

void NativeInstance::emitJoinPayload(std::function<void(tgcalls::GroupJoinPayload)> const &f) const {
  instanceHolder->groupNativeInstance->emitJoinPayload(f);
}

void NativeInstance::setJoinResponsePayload(std::string const &payload) const {
  instanceHolder->groupNativeInstance->setJoinResponsePayload(payload);
}

void NativeInstance::setIsMuted(bool isMuted) const {
  instanceHolder->groupNativeInstance->setIsMuted(isMuted);
}

void NativeInstance::setVolume(uint32_t ssrc, double volume) const {
  instanceHolder->groupNativeInstance->setVolume(ssrc, volume);
}

void NativeInstance::setConnectionMode(
    tgcalls::GroupConnectionMode connectionMode,
    bool keepBroadcastIfWasEnabled) const {
  instanceHolder->groupNativeInstance->setConnectionMode(
      connectionMode, keepBroadcastIfWasEnabled);
}

void NativeInstance::stopAudioDeviceModule() const {
  instanceHolder->groupNativeInstance->performWithAudioDeviceModule(
      [&](const rtc::scoped_refptr<tgcalls::WrappedAudioDeviceModule>& audioDeviceModule) {
        if (!audioDeviceModule) {
          return;
        }

        audioDeviceModule->StopRecording();
        audioDeviceModule->StopPlayout();
//        audioDeviceModule->Stop();
      }
  );
}

void NativeInstance::startAudioDeviceModule() const {
  instanceHolder->groupNativeInstance->performWithAudioDeviceModule(
      [&](const rtc::scoped_refptr<tgcalls::WrappedAudioDeviceModule>& audioDeviceModule) {
        if (!audioDeviceModule) {
          return;
        }

        if (!audioDeviceModule->Recording()) {
          audioDeviceModule->StartRecording();
        }
        if (!audioDeviceModule->Playing()){
          audioDeviceModule->StartPlayout();
        }
      }
  );
}

void NativeInstance::restartAudioInputDevice() const {
  instanceHolder->groupNativeInstance->performWithAudioDeviceModule(
      [&](const rtc::scoped_refptr<tgcalls::WrappedAudioDeviceModule>& audioDeviceModule) {
        if (!audioDeviceModule) {
          return;
        }

        const auto recording = audioDeviceModule->Recording();
        if (recording) {
          audioDeviceModule->StopRecording();
        }
        if (recording && audioDeviceModule->InitRecording() == 0) {
          audioDeviceModule->StartRecording();
        }
      }
  );
}

void NativeInstance::restartAudioOutputDevice() const {
  instanceHolder->groupNativeInstance->performWithAudioDeviceModule(
      [&](const rtc::scoped_refptr<tgcalls::WrappedAudioDeviceModule>& audioDeviceModule) {
        if (!audioDeviceModule) {
          return;
        }

        if (audioDeviceModule->Playing()) {
          audioDeviceModule->StopPlayout();
        }
        if (audioDeviceModule->InitPlayout() == 0) {
          audioDeviceModule->StartPlayout();
        }
      }
  );
}

std::vector<tgcalls::GroupInstanceInterface::AudioDevice> NativeInstance::getPlayoutDevices() const {
  return instanceHolder->groupNativeInstance->getAudioDevices(
      tgcalls::GroupInstanceInterface::AudioDevice::Type::Output
  );
}


std::vector<tgcalls::GroupInstanceInterface::AudioDevice> NativeInstance::getRecordingDevices() const {
  return instanceHolder->groupNativeInstance->getAudioDevices(
      tgcalls::GroupInstanceInterface::AudioDevice::Type::Input
  );
}


void NativeInstance::setAudioOutputDevice(std::string id) const {
  instanceHolder->groupNativeInstance->setAudioOutputDevice(std::move(id));
}

void NativeInstance::setAudioInputDevice(std::string id) const {
  instanceHolder->groupNativeInstance->setAudioInputDevice(std::move(id));
}

void NativeInstance::startCall(vector<RtcServer> servers,
                               std::array<uint8_t, 256> authKey,
                               bool isOutgoing, string logPath) {
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
      .outputVolume = 1.f};

  tgcalls::Descriptor descriptor = {
      .config =
      tgcalls::Config{
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
          .statsLogPath = {"/Users/marshal/projects/tgcalls/python-binding/"
                           "pytgcalls/tgcalls-stat.txt"},
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
      .stateUpdated =
      [=](tgcalls::State state) {
        //                py::print("stateUpdated");
      },
      .signalBarsUpdated =
      [=](int count) {
        //                py::print("signalBarsUpdated");
      },
      .audioLevelUpdated =
      [=](float level) {
        //                py::print("audioLevelUpdated");
      },
      .remoteBatteryLevelIsLowUpdated =
      [=](bool isLow) {
        //                py::print("remoteBatteryLevelIsLowUpdated");
      },
      .remoteMediaStateUpdated =
      [=](tgcalls::AudioState audioState, tgcalls::VideoState videoState) {
        //                py::print("remoteMediaStateUpdated");
      },
      .remotePrefferedAspectRatioUpdated =
      [=](float ratio) {
        //                py::print("remotePrefferedAspectRatioUpdated");
      },
      .signalingDataEmitted =
      [=](const std::vector<uint8_t> &data) {
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
        descriptor.rtcServers.push_back(
            tgcalls::RtcServer{.host = host, .port = port, .isTurn = false});
      };
      pushStun(host);
      pushStun(hostv6);

      //            descriptor.rtcServers.push_back(rtcServer.toTgcalls(false,
      //            false));
      //            descriptor.rtcServers.push_back(rtcServer.toTgcalls(true,
      //            false));
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
  instanceHolder->nativeInstance =
      tgcalls::Meta::Create("3.0.0", std::move(descriptor));
  instanceHolder->_videoCapture = videoCapture;
  instanceHolder->nativeInstance->setNetworkType(tgcalls::NetworkType::WiFi);
  instanceHolder->nativeInstance->setRequestedVideoAspect(1);
  instanceHolder->nativeInstance->setMuteMicrophone(false);
}

void NativeInstance::receiveSignalingData(std::vector<uint8_t> &data) const {
  instanceHolder->nativeInstance->receiveSignalingData(data);
}

void NativeInstance::setSignalingDataEmittedCallback(
    const std::function<void(const std::vector<uint8_t> &data)> &f) {
  //    py::print("setSignalingDataEmittedCallback");
  signalingDataEmittedCallback = f;
}
