#include <iostream>

#include <rtc_base/ssl_adapter.h>

#include "NativeInstance.h"

namespace py = pybind11;

auto noticeDisplayed = false;

NativeInstance::NativeInstance(bool logToStdErr, string logPath)
    : _logToStdErr(logToStdErr), _logPath(std::move(logPath)) {
  if (!noticeDisplayed) {
    py::print("tgcalls v" + std::string(PROJECT_VER) + ", Copyright (C) 2020-2021 Il`ya (Marshal) <https://github.com/MarshalX>");
    py::print("Licensed under the terms of the GNU Lesser General Public License v3 (LGPLv3) \n\n");

    noticeDisplayed = true;
  }
  rtc::InitializeSSL();
//    tgcalls::Register<tgcalls::InstanceImpl>();
}

NativeInstance::~NativeInstance() {
  _audioDeviceModule = nullptr;
}

void NativeInstance::setupGroupCall(
    std::function<void(tgcalls::GroupJoinPayload)> &emitJoinPayloadCallback,
    std::function<void(bool)> &networkStateUpdated,
    std::function<void(std::vector<uint32_t> const &)>
    &participantDescriptionsRequired) {
  _emitJoinPayloadCallback = emitJoinPayloadCallback;
  _networkStateUpdated = networkStateUpdated;
  _participantDescriptionsRequired = participantDescriptionsRequired;
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
      [=](tgcalls::GroupLevelsUpdate const &update) {}, // TODO may be
      .initialInputDeviceId = std::move(initialInputDeviceId),
      .initialOutputDeviceId = std::move(initialOutputDeviceId),
      .createAudioDeviceModule = std::move(createAudioDeviceModule),
      .participantDescriptionsRequired =
      [=](std::vector<uint32_t> const &ssrcs) {
        _participantDescriptionsRequired(ssrcs);
      },
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

void NativeInstance::startGroupCall(FileAudioDeviceDescriptor &fileAudioDeviceDescriptor) {
  createInstanceHolder(
      [&](webrtc::TaskQueueFactory *taskQueueFactory) -> rtc::scoped_refptr<webrtc::AudioDeviceModule> {
        _audioDeviceModule = WrappedAudioDeviceModuleImpl::Create(
            webrtc::AudioDeviceModule::kDummyAudio, taskQueueFactory, &fileAudioDeviceDescriptor
        );

        return _audioDeviceModule;
      });
}

void NativeInstance::startGroupCall(RawAudioDeviceDescriptor &rawAudioDeviceDescriptor) {
  createInstanceHolder(
      [&](webrtc::TaskQueueFactory *taskQueueFactory) -> rtc::scoped_refptr<webrtc::AudioDeviceModule> {
        _audioDeviceModule = WrappedAudioDeviceModuleImpl::Create(
            webrtc::AudioDeviceModule::kDummyAudio, taskQueueFactory, &rawAudioDeviceDescriptor
        );

        return _audioDeviceModule;
      });
}

void NativeInstance::startGroupCall(std::string initialInputDeviceId = "", std::string initialOutputDeviceId = "") {
  createInstanceHolder(
      [&](webrtc::TaskQueueFactory *taskQueueFactory) -> rtc::scoped_refptr<webrtc::AudioDeviceModule> {
        _audioDeviceModule = webrtc::AudioDeviceModule::Create(
            webrtc::AudioDeviceModule::kPlatformDefaultAudio,
            taskQueueFactory
        );

        return _audioDeviceModule;
      }, std::move(initialInputDeviceId), std::move(initialOutputDeviceId));
}

void NativeInstance::stopGroupCall() const {
  instanceHolder->groupNativeInstance.reset();
}

bool NativeInstance::isGroupCallStarted() const {
  return instanceHolder != nullptr && instanceHolder->groupNativeInstance != nullptr;
}

void NativeInstance::emitJoinPayload(std::function<void(tgcalls::GroupJoinPayload)> &f) const {
  instanceHolder->groupNativeInstance->emitJoinPayload(f);
}

void NativeInstance::setJoinResponsePayload(
    tgcalls::GroupJoinResponsePayload payload,
    std::vector<tgcalls::GroupParticipantDescription> &&participants) const {
  instanceHolder->groupNativeInstance->setJoinResponsePayload(
      std::move(payload), std::move(participants));
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

void NativeInstance::restartAudioInputDevice() const {
  instanceHolder->groupNativeInstance->_internal->perform(
      RTC_FROM_HERE,
      [=](tgcalls::GroupInstanceCustomInternal *internal) {
        if (!_audioDeviceModule) {
          return;
        }

        const auto recording = _audioDeviceModule->Recording();
        if (recording) {
          _audioDeviceModule->StopRecording();
        }
        if (recording && _audioDeviceModule->InitRecording() == 0) {
          _audioDeviceModule->StartRecording();
        }
      });
}

void NativeInstance::restartAudioOutputDevice() const {
  instanceHolder->groupNativeInstance->_internal->perform(
      RTC_FROM_HERE,
      [=](tgcalls::GroupInstanceCustomInternal *internal) {
        if (!_audioDeviceModule) {
          return;
        }

        if (_audioDeviceModule->Playing()) {
          _audioDeviceModule->StopPlayout();
        }
        if (_audioDeviceModule->InitPlayout() == 0) {
          _audioDeviceModule->StartPlayout();
        }
      });
}

void NativeInstance::printAvailablePlayoutDevices() const {
  instanceHolder->groupNativeInstance->_internal->perform(
      RTC_FROM_HERE,
      [=](tgcalls::GroupInstanceCustomInternal *internal) {
        const auto count = _audioDeviceModule ? _audioDeviceModule->PlayoutDevices() : int16_t(-1);

        if (count < 0) {
          std::cout << "Can't find available playout devices" << std::endl;
          return;
        }

        for (auto i = 0; i != count; ++i) {
          char name[webrtc::kAdmMaxDeviceNameSize + 1] = {0};
          char guid[webrtc::kAdmMaxGuidSize + 1] = {0};
          _audioDeviceModule->PlayoutDeviceName(i, name, guid);
          std::cout << "Playout device #" << i << std::endl
          << "name: " << name << std::endl
          << "guid: " << guid << std::endl;
        }
      });
}


void NativeInstance::printAvailableRecordingDevices() const {
  instanceHolder->groupNativeInstance->_internal->perform(
      RTC_FROM_HERE,
      [=](tgcalls::GroupInstanceCustomInternal *internal) {
        const auto count = _audioDeviceModule ? _audioDeviceModule->RecordingDevices() : int16_t(-1);

        if (count < 0) {
          std::cout << "Can't find available recording devices" << std::endl;
          return;
        }

        for (auto i = 0; i != count; ++i) {
          char name[webrtc::kAdmMaxDeviceNameSize + 1] = {0};
          char guid[webrtc::kAdmMaxGuidSize + 1] = {0};
          _audioDeviceModule->RecordingDeviceName(i, name, guid);
          std::cout << "Recording device #" << i << std::endl
          << "name: " << name << std::endl
          << "guid: " << guid << std::endl;
        }
      });
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

void NativeInstance::addParticipants(
    std::vector<tgcalls::GroupParticipantDescription> &&participants) const {
  instanceHolder->groupNativeInstance->addParticipants(std::move(participants));
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
