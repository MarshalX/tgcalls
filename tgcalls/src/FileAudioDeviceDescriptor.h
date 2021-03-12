#pragma once

#include <string>


class FileAudioDeviceDescriptor {
public:
    std::function<std::string()> _getInputFilename = nullptr;
    std::function<std::string()> _getOutputFilename = nullptr;

    std::function<bool()> _isEndlessPlayout = nullptr;
    std::function<bool()> _isPlayoutPaused = nullptr;
    std::function<bool()> _isRecordingPaused = nullptr;

    std::function<void(std::string)> _playoutEndedCallback = nullptr;
};
