#pragma once

#include <string>


class FileAudioDeviceDescriptor {
public:
    std::function<std::string()> _getInputFilename = nullptr;
    std::function<std::string()> _getOutputFilename = nullptr;
};
