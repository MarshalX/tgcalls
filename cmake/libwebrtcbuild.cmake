add_library(libwebrtcbuild INTERFACE)
add_library(tg_owt::libwebrtcbuild ALIAS libwebrtcbuild)

target_link_libraries(libwebrtcbuild
INTERFACE
    tg_owt::libyuv
)
if (NOT absl_FOUND)
    target_link_libraries(libwebrtcbuild INTERFACE tg_owt::libabsl)
endif()

target_compile_definitions(libwebrtcbuild
INTERFACE
    WEBRTC_ENABLE_PROTOBUF=0
    WEBRTC_APM_DEBUG_DUMP=0
    WEBRTC_USE_BUILTIN_ISAC_FLOAT
    WEBRTC_OPUS_VARIABLE_COMPLEXITY=0
    WEBRTC_OPUS_SUPPORT_120MS_PTIME=1
    WEBRTC_INCLUDE_INTERNAL_AUDIO_DEVICE
    WEBRTC_USE_H264
    WEBRTC_LIBRARY_IMPL
    WEBRTC_NON_STATIC_TRACE_EVENT_HANDLERS=1
    NO_MAIN_THREAD_WRAPPING
    HAVE_WEBRTC_VIDEO
    RTC_ENABLE_VP9
    RTC_DISABLE_TRACE_EVENTS
    BWE_TEST_LOGGING_COMPILE_TIME_ENABLE=0
)

if (TG_OWT_USE_PIPEWIRE)
    target_compile_definitions(libwebrtcbuild
    INTERFACE
        WEBRTC_USE_PIPEWIRE
    )
endif()

if (NOT TG_OWT_BUILD_AUDIO_BACKENDS)
    target_compile_definitions(libwebrtcbuild
    INTERFACE
        WEBRTC_DUMMY_AUDIO_BUILD
    )
elseif (UNIX AND NOT APPLE)
    target_compile_definitions(libwebrtcbuild
    INTERFACE
        WEBRTC_ENABLE_LINUX_ALSA
        WEBRTC_ENABLE_LINUX_PULSE
    )
endif()

if (WIN32)
    target_compile_definitions(libwebrtcbuild
    INTERFACE
        WEBRTC_WIN
    )
elseif (APPLE)
    target_compile_definitions(libwebrtcbuild
    INTERFACE
        WEBRTC_POSIX
        WEBRTC_MAC
    )
else()
    target_compile_definitions(libwebrtcbuild
    INTERFACE
        WEBRTC_POSIX
        WEBRTC_LINUX
        WEBRTC_USE_X11
    )
endif()

target_include_directories(libwebrtcbuild
INTERFACE
    $<BUILD_INTERFACE:${webrtc_loc}>
    $<INSTALL_INTERFACE:${webrtc_includedir}>
)
