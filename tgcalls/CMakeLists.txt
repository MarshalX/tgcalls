list(APPEND SOURCES
    ${src_loc}/main.cpp
)

pybind11_add_module(tgcalls ${SOURCES})

target_link_libraries(tgcalls
    PRIVATE
    lib_tgcalls
)

include(cmake/lib_tgcalls.cmake)
