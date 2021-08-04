add_library(libevent OBJECT EXCLUDE_FROM_ALL)
init_target(libevent)
add_library(tg_owt::libevent ALIAS libevent)

set(libevent_loc ${webrtc_loc}/base/third_party/libevent)

target_compile_definitions(libevent
PRIVATE
    HAVE_CONFIG_H
)

if (APPLE)
    target_include_directories(libevent
    PRIVATE
        ${libevent_loc}/mac
    )
else()
    target_include_directories(libevent
    PRIVATE
        ${libevent_loc}/linux
    )
endif()

nice_target_sources(libevent ${libevent_loc}
PRIVATE
    buffer.c
    epoll.c
    evbuffer.c
    evdns.c
    event.c
    event_tagging.c
    evrpc.c
    evutil.c
    http.c
    log.c
    poll.c
    select.c
    signal.c
    strlcpy.c
)

target_include_directories(libevent
PUBLIC
    $<BUILD_INTERFACE:${libevent_loc}>
PRIVATE
    ${webrtc_loc}
)
