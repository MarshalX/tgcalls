#include <cstdio>
#include <sstream>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

#include "NativeInstance.h"

namespace py = pybind11;

void ping() {
    py::print("pong");
}

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
            .def_readwrite("ufrag", &tgcalls::GroupJoinPayload::ufrag)
            .def_readwrite("pwd", &tgcalls::GroupJoinPayload::pwd)
            .def_readwrite("fingerprints", &tgcalls::GroupJoinPayload::fingerprints)
            .def_readwrite("ssrc", &tgcalls::GroupJoinPayload::ssrc)
            .def("__repr__", [](const tgcalls::GroupJoinPayload &e) {
                ostringstream repr;
                repr << "<tgcalls.GroupJoinPayload ";
                repr << "ufrag=\"" << e.ufrag << "\" ";
                repr << "pwd=\"" << e.pwd << "\" ";
                // TODO for each item to str
//                repr << "fingerprints=\"" << e.fingerprints << "\" ";
                repr << "ssrc=\"" << e.ssrc << "\"> ";
                return repr.str();
            });

    py::class_<tgcalls::GroupJoinPayloadFingerprint>(m, "GroupJoinPayloadFingerprint")
            .def(py::init<>())
            .def_readwrite("hash", &tgcalls::GroupJoinPayloadFingerprint::hash)
            .def_readwrite("setup", &tgcalls::GroupJoinPayloadFingerprint::setup)
            .def_readwrite("fingerprint", &tgcalls::GroupJoinPayloadFingerprint::fingerprint)
            .def("__repr__", [](const tgcalls::GroupJoinPayloadFingerprint &e) {
                ostringstream repr;
                repr << "<tgcalls.GroupJoinPayloadFingerprint ";
                repr << "hash=\"" << e.hash << "\" ";
                repr << "setup=\"" << e.setup << "\" ";
                repr << "fingerprint=\"" << e.fingerprint << "\"> ";
                return repr.str();
            });

    py::class_<tgcalls::GroupJoinResponsePayload>(m, "GroupJoinResponsePayload")
            .def(py::init<>())
            .def_readwrite("ufrag", &tgcalls::GroupJoinResponsePayload::ufrag)
            .def_readwrite("pwd", &tgcalls::GroupJoinResponsePayload::pwd)
            .def_readwrite("fingerprints", &tgcalls::GroupJoinResponsePayload::fingerprints)
            .def_readwrite("candidates", &tgcalls::GroupJoinResponsePayload::candidates)
            .def("__repr__", [](const tgcalls::GroupJoinResponsePayload &e) {
                ostringstream repr;
                repr << "<tgcalls.GroupJoinResponsePayload ";
                repr << "ufrag=\"" << e.ufrag << "\" ";
                repr << "pwd=\"" << e.pwd << "\" ";
                // TODO for each item to str
//                repr << "fingerprints=\"" << e.fingerprints << "\" ";
//                repr << "candidates=\"" << e.candidates << "\"> ";
                return repr.str();
            });

    py::class_<tgcalls::GroupJoinResponseCandidate>(m, "GroupJoinResponseCandidate")
            .def(py::init<>())
            .def_readwrite("port", &tgcalls::GroupJoinResponseCandidate::port)
            .def_readwrite("protocol", &tgcalls::GroupJoinResponseCandidate::protocol)
            .def_readwrite("network", &tgcalls::GroupJoinResponseCandidate::network)
            .def_readwrite("generation", &tgcalls::GroupJoinResponseCandidate::generation)
            .def_readwrite("id", &tgcalls::GroupJoinResponseCandidate::id)
            .def_readwrite("component", &tgcalls::GroupJoinResponseCandidate::component)
            .def_readwrite("foundation", &tgcalls::GroupJoinResponseCandidate::foundation)
            .def_readwrite("priority", &tgcalls::GroupJoinResponseCandidate::priority)
            .def_readwrite("ip", &tgcalls::GroupJoinResponseCandidate::ip)
            .def_readwrite("type", &tgcalls::GroupJoinResponseCandidate::type)

            .def_readwrite("tcpType", &tgcalls::GroupJoinResponseCandidate::tcpType)
            .def_readwrite("relAddr", &tgcalls::GroupJoinResponseCandidate::relAddr)
            .def_readwrite("relPort", &tgcalls::GroupJoinResponseCandidate::relPort)
            .def("__repr__", [](const tgcalls::GroupJoinResponseCandidate &e) {
                ostringstream repr;
                repr << "<tgcalls.GroupJoinResponseCandidate ";
                repr << "port=\"" << e.port << "\" ";
                // TODO add all fields
//                repr << "candidates=\"" << e.candidates << "\"> ";
                return repr.str();
            });

    py::class_<tgcalls::GroupParticipantDescription>(m, "GroupParticipantDescription")
            .def(py::init<>())
            .def_readwrite("endpointId", &tgcalls::GroupParticipantDescription::endpointId)
            .def_readwrite("audioSsrc", &tgcalls::GroupParticipantDescription::audioSsrc)
            .def_readwrite("videoPayloadTypes", &tgcalls::GroupParticipantDescription::videoPayloadTypes)
            .def_readwrite("videoExtensionMap", &tgcalls::GroupParticipantDescription::videoExtensionMap)
            .def_readwrite("videoSourceGroups", &tgcalls::GroupParticipantDescription::videoSourceGroups)
            .def_readwrite("isRemoved", &tgcalls::GroupParticipantDescription::isRemoved);

    py::class_<tgcalls::GroupJoinPayloadVideoPayloadType>(m, "GroupJoinPayloadVideoPayloadType")
            .def(py::init<>())
            .def_readwrite("id", &tgcalls::GroupJoinPayloadVideoPayloadType::id)
            .def_readwrite("name", &tgcalls::GroupJoinPayloadVideoPayloadType::name)
            .def_readwrite("clockrate", &tgcalls::GroupJoinPayloadVideoPayloadType::clockrate)
            .def_readwrite("channels", &tgcalls::GroupJoinPayloadVideoPayloadType::channels)
            .def_readwrite("feedbackTypes", &tgcalls::GroupJoinPayloadVideoPayloadType::feedbackTypes)
            .def_readwrite("parameters", &tgcalls::GroupJoinPayloadVideoPayloadType::parameters);

    py::class_<tgcalls::GroupJoinPayloadVideoPayloadFeedbackType>(m, "GroupJoinPayloadVideoPayloadFeedbackType")
            .def(py::init<>())
            .def_readwrite("type", &tgcalls::GroupJoinPayloadVideoPayloadFeedbackType::type)
            .def_readwrite("subtype", &tgcalls::GroupJoinPayloadVideoPayloadFeedbackType::subtype);

    py::class_<tgcalls::GroupJoinPayloadVideoSourceGroup>(m, "GroupJoinPayloadVideoSourceGroup")
            .def(py::init<>())
            .def_readwrite("ssrcs", &tgcalls::GroupJoinPayloadVideoSourceGroup::ssrcs)
            .def_readwrite("semantics", &tgcalls::GroupJoinPayloadVideoSourceGroup::semantics);

    py::class_<FileAudioDeviceDescriptor>(m, "FileAudioDeviceDescriptor")
            .def(py::init<>())
            .def_readwrite("getInputFilename", &FileAudioDeviceDescriptor::_getInputFilename)
            .def_readwrite("getOutputFilename", &FileAudioDeviceDescriptor::_getOutputFilename)
            .def_readwrite("isEndlessPlayout", &FileAudioDeviceDescriptor::_isEndlessPlayout)
            .def_readwrite("isPlayoutPaused", &FileAudioDeviceDescriptor::_isPlayoutPaused)
            .def_readwrite("isRecordingPaused", &FileAudioDeviceDescriptor::_isRecordingPaused)
            .def_readwrite("playoutEndedCallback", &FileAudioDeviceDescriptor::_playoutEndedCallback);

    py::class_<RawAudioDeviceDescriptor>(m, "RawAudioDeviceDescriptor")
            .def(py::init<>())
            .def_readwrite("setRecordedBufferCallback", &RawAudioDeviceDescriptor::_setRecordedBufferCallback)
            .def_readwrite("getPlayedBufferCallback", &RawAudioDeviceDescriptor::_getPlayedBufferCallback)
            .def_readwrite("isPlayoutPaused", &RawAudioDeviceDescriptor::_isPlayoutPaused)
            .def_readwrite("isRecordingPaused", &RawAudioDeviceDescriptor::_isRecordingPaused);

    py::enum_<tgcalls::GroupConnectionMode>(m, "GroupConnectionMode")
            .value("GroupConnectionModeNone", tgcalls::GroupConnectionMode::GroupConnectionModeNone)
            .value("GroupConnectionModeRtc", tgcalls::GroupConnectionMode::GroupConnectionModeRtc)
            .value("GroupConnectionModeBroadcast", tgcalls::GroupConnectionMode::GroupConnectionModeBroadcast)
            .export_values();

    py::class_<NativeInstance>(m, "NativeInstance")
            .def(py::init<bool, string>())
            .def("startCall", &NativeInstance::startCall)
            .def("setupGroupCall", &NativeInstance::setupGroupCall)
            .def("startGroupCall", py::overload_cast<FileAudioDeviceDescriptor &>(&NativeInstance::startGroupCall))
            .def("startGroupCall", py::overload_cast<RawAudioDeviceDescriptor &>(&NativeInstance::startGroupCall))
            .def("isGroupCallStarted", &NativeInstance::isGroupCallStarted)
            .def("stopGroupCall", &NativeInstance::stopGroupCall)
            .def("setIsMuted", &NativeInstance::setIsMuted)
            .def("setVolume", &NativeInstance::setVolume)
            .def("restartAudioInputDevice", &NativeInstance::restartAudioInputDevice)
            .def("restartAudioOutputDevice", &NativeInstance::restartAudioOutputDevice)
            .def("setAudioOutputDevice", &NativeInstance::setAudioOutputDevice)
            .def("setAudioInputDevice", &NativeInstance::setAudioInputDevice)
            .def("removeSsrcs", &NativeInstance::removeSsrcs)
            .def("addParticipants", &NativeInstance::addParticipants)
            .def("setJoinResponsePayload", &NativeInstance::setJoinResponsePayload)
            .def("setConnectionMode", &NativeInstance::setConnectionMode)
            .def("emitJoinPayload", &NativeInstance::emitJoinPayload)
            .def("receiveSignalingData", &NativeInstance::receiveSignalingData)
            .def("setSignalingDataEmittedCallback", &NativeInstance::setSignalingDataEmittedCallback);
}
