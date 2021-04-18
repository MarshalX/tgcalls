#include "RawAudioDeviceDescriptor.h"

void RawAudioDeviceDescriptor::_setRecordedBuffer(int8_t *frame, size_t length) const {
  _setRecordedBufferCallback(std::string ((const char *) frame, sizeof(int8_t) * length), length);
}

int8_t *RawAudioDeviceDescriptor::_getPlayoutBuffer(size_t length) const {
  std::string frame = _getPlayedBufferCallback(length);

  // TODO
  return (int8_t *) frame.data();
}
