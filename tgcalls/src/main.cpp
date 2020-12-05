#include "stdio.h"
#include <pybind11/pybind11.h>
#include "tgcalls/InstanceImpl.h"

namespace py = pybind11;


int print(std::string str) {
    py::print(str);
}

PYBIND11_MODULE(tgcalls, m) {
    m.def("print", &print, R"pbdoc(
        Print text
    )pbdoc");
}
