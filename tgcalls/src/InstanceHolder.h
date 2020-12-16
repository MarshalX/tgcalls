#pragma once

#include "tgcalls/Instance.h"
#include "tgcalls/PlatformContext.h"

struct InstanceHolder {
    std::unique_ptr<tgcalls::Instance> nativeInstance;
    std::shared_ptr<tgcalls::VideoCaptureInterface> _videoCapture;
    std::shared_ptr<tgcalls::PlatformContext> _platformContext;
};
