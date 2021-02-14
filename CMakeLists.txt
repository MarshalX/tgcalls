cmake_minimum_required(VERSION 3.16)
cmake_policy(SET CMP0076 NEW)
cmake_policy(SET CMP0091 NEW)

project(tgcalls
    DESCRIPTION "Python binding for tgcalls"
    HOMEPAGE_URL "https://github.com/MarshalX/tgcalls"
)

get_filename_component(third_party_loc "tgcalls/third_party" REALPATH)
get_filename_component(src_loc "tgcalls/src" REALPATH)

include(cmake/variables.cmake)
include(cmake/validate_special_target.cmake)
include(cmake/nice_target_sources.cmake)
include(cmake/target_link_static_libraries.cmake)
include(cmake/target_link_frameworks.cmake)
include(cmake/options.cmake)
include(cmake/init_target.cmake)

add_subdirectory(cmake/external/openssl)
add_subdirectory(cmake/external/jpeg)
add_subdirectory(cmake/external/opus)
add_subdirectory(cmake/external/webrtc)

add_subdirectory(${third_party_loc}/pybind11)

add_subdirectory(tgcalls)
