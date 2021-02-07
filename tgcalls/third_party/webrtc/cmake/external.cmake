# OpenSSL
set(TG_OWT_OPENSSL_INCLUDE_PATH "" CACHE STRING "Include path for openssl.")
function(link_openssl target_name)
    if (TG_OWT_PACKAGED_BUILD)
        find_package(OpenSSL REQUIRED)
        target_include_directories(${target_name} PRIVATE ${OPENSSL_INCLUDE_DIR})
        target_link_libraries(${target_name} PRIVATE ${OPENSSL_LIBRARIES})
    else()
        if (TG_OWT_OPENSSL_INCLUDE_PATH STREQUAL "")
            message(FATAL_ERROR "You should specify 'TG_OWT_OPENSSL_INCLUDE_PATH'.")
        endif()

        target_include_directories(${target_name}
        PRIVATE
            ${TG_OWT_OPENSSL_INCLUDE_PATH}
        )
    endif()
endfunction()

# Opus
set(TG_OWT_OPUS_INCLUDE_PATH "" CACHE STRING "Include path for opus.")
function(link_opus target_name)
    if (TG_OWT_PACKAGED_BUILD)
        find_package(PkgConfig REQUIRED)
        pkg_check_modules(OPUS REQUIRED opus)
        target_include_directories(${target_name} PRIVATE ${OPUS_INCLUDE_DIRS})
        target_link_libraries(${target_name} PRIVATE ${OPUS_LINK_LIBRARIES})
    else()
        if (TG_OWT_OPUS_INCLUDE_PATH STREQUAL "")
            message(FATAL_ERROR "You should specify 'TG_OWT_OPUS_INCLUDE_PATH'.")
        endif()

        target_include_directories(${target_name}
        PRIVATE
            ${TG_OWT_OPUS_INCLUDE_PATH}
        )
    endif()
endfunction()

# FFmpeg
set(TG_OWT_FFMPEG_INCLUDE_PATH "" CACHE STRING "Include path for ffmpeg.")
option(TG_OWT_PACKAGED_BUILD_FFMPEG_STATIC "Link ffmpeg statically in packaged mode." OFF)
function(link_ffmpeg target_name)
    if (TG_OWT_PACKAGED_BUILD)
        find_package(PkgConfig REQUIRED)
        pkg_check_modules(AVCODEC REQUIRED libavcodec)
        pkg_check_modules(AVFORMAT REQUIRED libavformat)
        pkg_check_modules(AVUTIL REQUIRED libavutil)
        pkg_check_modules(SWSCALE REQUIRED libswscale)
        pkg_check_modules(SWRESAMPLE REQUIRED libswresample)
        target_include_directories(${target_name} PRIVATE
            ${AVCODEC_INCLUDE_DIRS}
            ${AVFORMAT_INCLUDE_DIRS}
            ${AVUTIL_INCLUDE_DIRS}
            ${SWSCALE_INCLUDE_DIRS}
            ${SWRESAMPLE_INCLUDE_DIRS}
        )
        if (TG_OWT_PACKAGED_BUILD_FFMPEG_STATIC)
            target_link_libraries(${target_name}
            PRIVATE
                ${AVCODEC_STATIC_LINK_LIBRARIES}
                ${AVFORMAT_STATIC_LINK_LIBRARIES}
                ${AVUTIL_STATIC_LINK_LIBRARIES}
                ${SWSCALE_STATIC_LINK_LIBRARIES}
                ${SWRESAMPLE_STATIC_LINK_LIBRARIES}
            )
        else()
            target_link_libraries(${target_name}
            PRIVATE
                ${AVCODEC_LINK_LIBRARIES}
                ${AVFORMAT_LINK_LIBRARIES}
                ${AVUTIL_LINK_LIBRARIES}
                ${SWSCALE_LINK_LIBRARIES}
                ${SWRESAMPLE_LINK_LIBRARIES}
            )
        endif()
    else()
        if (TG_OWT_FFMPEG_INCLUDE_PATH STREQUAL "")
            message(FATAL_ERROR "You should specify 'TG_OWT_FFMPEG_INCLUDE_PATH'.")
        endif()

        target_include_directories(${target_name}
        PRIVATE
            ${TG_OWT_FFMPEG_INCLUDE_PATH}
        )
    endif()
endfunction()

# libjpeg
set(TG_OWT_LIBJPEG_INCLUDE_PATH "" CACHE STRING "Include path for libjpeg.")
function(link_libjpeg target_name)
    if (TG_OWT_PACKAGED_BUILD)
        find_package(JPEG REQUIRED)
        target_include_directories(${target_name} PRIVATE ${JPEG_INCLUDE_DIRS})
        target_link_libraries(${target_name} PRIVATE ${JPEG_LIBRARIES})
    else()
        if (TG_OWT_LIBJPEG_INCLUDE_PATH STREQUAL "")
            message(FATAL_ERROR "You should specify 'TG_OWT_LIBJPEG_INCLUDE_PATH'.")
        endif()

        target_include_directories(${target_name}
        PRIVATE
            ${TG_OWT_LIBJPEG_INCLUDE_PATH}
            ${TG_OWT_LIBJPEG_INCLUDE_PATH}/src
        )
    endif()
endfunction()

# alsa
function(link_libalsa target_name)
    if (TG_OWT_PACKAGED_BUILD)
        find_package(ALSA REQUIRED)
        target_include_directories(${target_name} PRIVATE ${ALSA_INCLUDE_DIRS})
    endif()
endfunction()

# pulseaudio
function(link_libpulse target_name)
    if (TG_OWT_PACKAGED_BUILD)
        find_package(PkgConfig REQUIRED)
        pkg_check_modules(PULSE REQUIRED libpulse)
        target_include_directories(${target_name} PRIVATE ${PULSE_INCLUDE_DIRS})
    endif()
endfunction()

# dl
function(link_dl target_name)
    if (TG_OWT_PACKAGED_BUILD)
        target_link_libraries(${target_name} PRIVATE ${CMAKE_DL_LIBS})
    endif()
endfunction()
