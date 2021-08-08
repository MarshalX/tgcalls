#include "RawAudioDeviceDescriptor.h"

void RawAudioDeviceDescriptor::_setRecordedBuffer(int8_t *frame, size_t length) const {
  auto bytes = std::string((const char *) frame, sizeof(int8_t) * length);
  _setRecordedBufferCallback(bytes, length);
}

int8_t *RawAudioDeviceDescriptor::_getPlayoutBuffer(size_t length) const {
  std::string frame = _getPlayedBufferCallback(length);

  return (int8_t *) (new std::string{frame})->data();
}
