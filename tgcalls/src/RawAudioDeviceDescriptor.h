#pragma once

#include <string>
#include <functional>

#include <pybind11/pybind11.h>

namespace py = pybind11;

class RawAudioDeviceDescriptor {
public:
    std::function<std::string(size_t)> _getPlayedBufferCallback = nullptr;
    std::function<void(const py::bytes &frame, size_t)> _setRecordedBufferCallback = nullptr;

    std::function<bool()> _isPlayoutPaused = nullptr;
    std::function<bool()> _isRecordingPaused = nullptr;

    void _setRecordedBuffer(int8_t*, size_t) const;
    std::string* _getPlayoutBuffer(size_t) const;
};
