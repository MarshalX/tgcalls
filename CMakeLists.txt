cmake_minimum_required(VERSION 3.14)
cmake_policy(SET CMP0076 NEW)
# cmake 3.15+ make_policy(SET CMP0091 NEW)

include(cmake/variables.cmake)

set(ROOT_PATH $ENV{ROOT_PATH})
if (ROOT_PATH)
    if (build_win64)
        get_filename_component(libs_loc "${ROOT_PATH}/Libraries/win64" REALPATH)
    elseif (NOT APPLE OR build_osx)
        get_filename_component(libs_loc "${ROOT_PATH}/Libraries" REALPATH)
    else()
        get_filename_component(libs_loc "${ROOT_PATH}/Libraries/macos" REALPATH)
    endif()
endif()

include(cmake/validate_special_target.cmake)

project(tgcalls
    LANGUAGES C CXX
    DESCRIPTION "Python binding for tgcalls"
    HOMEPAGE_URL "https://github.com/MarshalX/tgcalls"
    VERSION "3.0.0.6"
)

get_filename_component(third_party_loc "tgcalls/third_party" REALPATH)
get_filename_component(src_loc "tgcalls/src" REALPATH)

include(cmake/nice_target_sources.cmake)
include(cmake/target_link_static_libraries.cmake)
include(cmake/target_link_frameworks.cmake)
include(cmake/init_target.cmake)
include(cmake/generate_target.cmake)

include(cmake/options.cmake)

add_subdirectory(${third_party_loc}/pybind11)

add_subdirectory(cmake/external/jpeg)
add_subdirectory(cmake/external/openssl)
add_subdirectory(cmake/external/opus)
add_subdirectory(cmake/external/webrtc)

add_subdirectory(tgcalls)
