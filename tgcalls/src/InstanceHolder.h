#pragma once

#include "tgcalls/Instance.h"
#include "tgcalls/group/GroupInstanceImpl.h"

struct InstanceHolder {
    std::unique_ptr<tgcalls::Instance> nativeInstance;
    std::unique_ptr<tgcalls::GroupInstanceImpl> groupNativeInstance;
    std::shared_ptr<tgcalls::VideoCaptureInterface> _videoCapture;
};
