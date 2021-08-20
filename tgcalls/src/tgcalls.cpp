#include <cstdio>
#include <sstream>

#include <pybind11/smart_holder.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

#include "NativeInstance.h"

namespace py = pybind11;

void ping() {
    py::print("pong");
}

PYBIND11_TYPE_CASTER_BASE_HOLDER(T, std::unique_ptr<T>)

PYBIND11_SMART_HOLDER_TYPE_CASTERS(FileAudioDeviceDescriptor)
PYBIND11_SMART_HOLDER_TYPE_CASTERS(RawAudioDeviceDescriptor)

PYBIND11_TYPE_CASTER_BASE_HOLDER(FileAudioDeviceDescriptor, std::shared_ptr<FileAudioDeviceDescriptor)
PYBIND11_TYPE_CASTER_BASE_HOLDER(RawAudioDeviceDescriptor, std::shared_ptr<RawAudioDeviceDescriptor>)
PYBIND11_MODULE(tgcalls, m) {
    m.def("ping", &ping);

//    py::add_ostream_redirect(m, "ostream_redirect");

    py::register_exception_translator([](std::exception_ptr p) {
        try {
            if (p) std::rethrow_exception(p);
        } catch (const std::exception &e) {
            PyErr_SetString(PyExc_RuntimeError, e.what());
        }
    });

    py::class_<RtcServer>(m, "RtcServer")
            .def(py::init<string, string, int, string, string, bool, bool>())
            .def_readwrite("ip", &RtcServer::ip)
            .def_readwrite("ipv6", &RtcServer::ipv6)
            .def_readwrite("port", &RtcServer::port)
            .def_readwrite("login", &RtcServer::login)
            .def_readwrite("password", &RtcServer::password)
            .def_readwrite("isTurn", &RtcServer::isTurn)
            .def_readwrite("isStun", &RtcServer::isStun)
            .def("__repr__", [](const RtcServer &e) {
                ostringstream repr;
                repr << "<tgcalls.RtcServer ";
                repr << "ip=\"" << e.ip << "\" ";
                repr << "ipv6=\"" << e.ipv6 << "\" ";
                repr << "port=\"" << e.port << "\" ";
                repr << "login=\"" << e.login << "\" ";
                repr << "password=\"" << e.password << "\" ";
                repr << "isTurn=\"" << e.isTurn << "\" ";
                repr << "isStun=\"" << e.isStun << "\">";
                return repr.str();
            });

    py::class_<tgcalls::GroupJoinPayload>(m, "GroupJoinPayload")
            .def(py::init<>())
            .def_readwrite("audioSsrc", &tgcalls::GroupJoinPayload::audioSsrc)
            .def_readwrite("json", &tgcalls::GroupJoinPayload::json)
            .def("__repr__", [](const tgcalls::GroupJoinPayload &e) {
                ostringstream repr;
                repr << "<tgcalls.GroupJoinPayload ";
                repr << "audioSsrc=\"" << e.audioSsrc << "\" ";
                repr << "json=\"" << e.json << "\"> ";
                return repr.str();
            });

    py::class_<tgcalls::GroupJoinPayloadVideoPayloadType>(m, "GroupJoinPayloadVideoPayloadType")
            .def(py::init<>())
            .def_readwrite("id", &tgcalls::GroupJoinPayloadVideoPayloadType::id)
            .def_readwrite("name", &tgcalls::GroupJoinPayloadVideoPayloadType::name)
            .def_readwrite("clockrate", &tgcalls::GroupJoinPayloadVideoPayloadType::clockrate)
            .def_readwrite("channels", &tgcalls::GroupJoinPayloadVideoPayloadType::channels)
            .def_readwrite("feedbackTypes", &tgcalls::GroupJoinPayloadVideoPayloadType::feedbackTypes)
            .def_readwrite("parameters", &tgcalls::GroupJoinPayloadVideoPayloadType::parameters);

    py::class_<tgcalls::GroupJoinPayloadVideoSourceGroup>(m, "GroupJoinPayloadVideoSourceGroup")
            .def(py::init<>())
            .def_readwrite("ssrcs", &tgcalls::GroupJoinPayloadVideoSourceGroup::ssrcs)
            .def_readwrite("semantics", &tgcalls::GroupJoinPayloadVideoSourceGroup::semantics);

    py::classh<FileAudioDeviceDescriptor>(m, "FileAudioDeviceDescriptor")
            .def(py::init<>())
            .def_readwrite("getInputFilename", &FileAudioDeviceDescriptor::_getInputFilename)
            .def_readwrite("getOutputFilename", &FileAudioDeviceDescriptor::_getOutputFilename)
            .def_readwrite("isEndlessPlayout", &FileAudioDeviceDescriptor::_isEndlessPlayout)
            .def_readwrite("isPlayoutPaused", &FileAudioDeviceDescriptor::_isPlayoutPaused)
            .def_readwrite("isRecordingPaused", &FileAudioDeviceDescriptor::_isRecordingPaused)
            .def_readwrite("playoutEndedCallback", &FileAudioDeviceDescriptor::_playoutEndedCallback);

    py::classh<RawAudioDeviceDescriptor>(m, "RawAudioDeviceDescriptor")
            .def(py::init<>())
            .def_readwrite("setRecordedBufferCallback", &RawAudioDeviceDescriptor::_setRecordedBufferCallback)
            .def_readwrite("getPlayedBufferCallback", &RawAudioDeviceDescriptor::_getPlayedBufferCallback)
            .def_readwrite("isPlayoutPaused", &RawAudioDeviceDescriptor::_isPlayoutPaused)
            .def_readwrite("isRecordingPaused", &RawAudioDeviceDescriptor::_isRecordingPaused);

    py::class_<tgcalls::GroupInstanceInterface::AudioDevice>(m, "AudioDevice")
            .def_readwrite("name", &tgcalls::GroupInstanceInterface::AudioDevice::name)
            .def_readwrite("guid", &tgcalls::GroupInstanceInterface::AudioDevice::guid)
            .def("__repr__", [](const tgcalls::GroupInstanceInterface::AudioDevice &e) {
              ostringstream repr;
              repr << "<tgcalls.AudioDevice ";
              repr << "name=\"" << e.name << "\" ";
              repr << "guid=\"" << e.guid << "\"> ";
              return repr.str();
            });

    py::enum_<tgcalls::GroupConnectionMode>(m, "GroupConnectionMode")
            .value("GroupConnectionModeNone", tgcalls::GroupConnectionMode::GroupConnectionModeNone)
            .value("GroupConnectionModeRtc", tgcalls::GroupConnectionMode::GroupConnectionModeRtc)
            .value("GroupConnectionModeBroadcast", tgcalls::GroupConnectionMode::GroupConnectionModeBroadcast)
            .export_values();

    py::class_<NativeInstance>(m, "NativeInstance")
            .def(py::init<bool, string>())
            .def("startCall", &NativeInstance::startCall)
            .def("setupGroupCall", &NativeInstance::setupGroupCall)
            .def("startGroupCall", py::overload_cast<std::shared_ptr<FileAudioDeviceDescriptor>>(&NativeInstance::startGroupCall))
            .def("startGroupCall", py::overload_cast<std::shared_ptr<RawAudioDeviceDescriptor>>(&NativeInstance::startGroupCall))
            .def("startGroupCall", py::overload_cast<std::string, std::string>(&NativeInstance::startGroupCall))
            .def("isGroupCallNativeCreated", &NativeInstance::isGroupCallNativeCreated)
            .def("stopGroupCall", &NativeInstance::stopGroupCall)
            .def("setIsMuted", &NativeInstance::setIsMuted)
            .def("setVolume", &NativeInstance::setVolume)
            .def("restartAudioInputDevice", &NativeInstance::restartAudioInputDevice)
            .def("restartAudioOutputDevice", &NativeInstance::restartAudioOutputDevice)
            .def("stopAudioDeviceModule", &NativeInstance::stopAudioDeviceModule)
            .def("startAudioDeviceModule", &NativeInstance::startAudioDeviceModule)
            .def("getPlayoutDevices", &NativeInstance::getPlayoutDevices)
            .def("getRecordingDevices", &NativeInstance::getRecordingDevices)
            .def("setAudioOutputDevice", &NativeInstance::setAudioOutputDevice)
            .def("setAudioInputDevice", &NativeInstance::setAudioInputDevice)
            .def("setJoinResponsePayload", &NativeInstance::setJoinResponsePayload)
            .def("setConnectionMode", &NativeInstance::setConnectionMode)
            .def("emitJoinPayload", &NativeInstance::emitJoinPayload)
            .def("receiveSignalingData", &NativeInstance::receiveSignalingData)
            .def("setSignalingDataEmittedCallback", &NativeInstance::setSignalingDataEmittedCallback);
}
