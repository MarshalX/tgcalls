#pragma once

#include "tgcalls/Instance.h"
#include "tgcalls/group/GroupInstanceCustomImpl.h"

struct InstanceHolder {
    std::unique_ptr<tgcalls::Instance> nativeInstance;
    std::unique_ptr<tgcalls::GroupInstanceCustomImpl> groupNativeInstance;
    std::shared_ptr<tgcalls::VideoCaptureInterface> _videoCapture;
};
