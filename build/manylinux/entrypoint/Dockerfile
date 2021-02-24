ARG MANYLINUX_PLATFORM
FROM ghcr.io/marshalx/tgcalls/$MANYLINUX_PLATFORM-webrtc:latest

ENV PLATFORM MANYLINUX_PLATFORM

COPY entrypoint.sh /entrypoint.sh

RUN ["chmod", "+x", "/entrypoint.sh"]
ENTRYPOINT ["/entrypoint.sh"]