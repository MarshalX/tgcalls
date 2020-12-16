#include <stdio.h>
#include <sstream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/iostream.h>
#include <tgcalls/InstanceImpl.h>
#include "NativeInstance.h"

namespace py = pybind11;

void ping() {
    py::print("pong");
}

PYBIND11_MODULE(tgcalls, m) {
    m.def("ping", &ping);

    py::add_ostream_redirect(m, "ostream_redirect");

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

    py::class_<NativeInstance>(m, "NativeInstance")
            .def(py::init<vector<RtcServer>, std::array<uint8_t, 256>, bool, string>())
            .def("start", &NativeInstance::start)
            .def("receiveSignalingData", &NativeInstance::receiveSignalingData)
            .def("setSignalingDataEmittedCallback", &NativeInstance::setSignalingDataEmittedCallback);
}
