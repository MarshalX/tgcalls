ARG MANYLINUX_PLATFORM
FROM ghcr.io/marshalx/tgcalls/$MANYLINUX_PLATFORM-webrtc:latest

COPY build/manylinux/entrypoint/entrypoint.sh /entrypoint.sh

RUN ["chmod", "+x", "/entrypoint.sh"]
ENTRYPOINT ["/entrypoint.sh"]
