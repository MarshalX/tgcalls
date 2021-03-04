
namespace rtc {
class Thread;
}

namespace tgcalls {

namespace StaticThreads {

rtc::Thread *getNetworkThread();
rtc::Thread *getMediaThread();
rtc::Thread *getWorkerThread();

}

};
