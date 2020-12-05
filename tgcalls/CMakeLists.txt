add_executable(tgcalls WIN32 MACOSX_BUNDLE)
init_target(tgcalls)

target_link_libraries(tgcalls
        PRIVATE
        lib_tgcalls
        )

nice_target_sources(tgcalls ${src_loc}
        PRIVATE
        main.cpp
        )

include(cmake/lib_tgcalls.cmake)
