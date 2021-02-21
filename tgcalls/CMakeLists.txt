include(cmake/external_ffmpeg.cmake)
include(cmake/lib_tgcalls.cmake)

list(APPEND SOURCES
    ${src_loc}/tgcalls.cpp
    ${src_loc}/NativeInstance.h
    ${src_loc}/NativeInstance.cpp
    ${src_loc}/RtcServer.h
    ${src_loc}/RtcServer.cpp
    ${src_loc}/InstanceHolder.h
)

pybind11_add_module(tgcalls ${SOURCES})

target_link_libraries(tgcalls
PRIVATE
    lib_tgcalls
    external_ffmpeg
    external_webrtc
)

#target_compile_definitions(tgcalls
#PUBLIC
#    DEBUG
#)
