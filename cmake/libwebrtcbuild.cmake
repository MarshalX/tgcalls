add_library(libwebrtcbuild INTERFACE)
add_library(tg_owt::libwebrtcbuild ALIAS libwebrtcbuild)

target_link_libraries(libwebrtcbuild
INTERFACE
    tg_owt::libabsl
    tg_owt::libyuv
)

target_compile_definitions(libwebrtcbuild
INTERFACE
    WEBRTC_ENABLE_PROTOBUF=0
    WEBRTC_APM_DEBUG_DUMP=0
    WEBRTC_USE_BUILTIN_ISAC_FLOAT
    WEBRTC_OPUS_VARIABLE_COMPLEXITY=0
    WEBRTC_INCLUDE_INTERNAL_AUDIO_DEVICE
    WEBRTC_USE_H264
    WEBRTC_LIBRARY_IMPL
    WEBRTC_NON_STATIC_TRACE_EVENT_HANDLERS=1
    WEBRTC_ENABLE_LINUX_ALSA
    WEBRTC_ENABLE_LINUX_PULSE
    HAVE_WEBRTC_VIDEO
    RTC_ENABLE_VP9
)

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
    )
endif()

target_include_directories(libwebrtcbuild
INTERFACE
    $<BUILD_INTERFACE:${webrtc_loc}>
    $<INSTALL_INTERFACE:${webrtc_includedir}>
)
