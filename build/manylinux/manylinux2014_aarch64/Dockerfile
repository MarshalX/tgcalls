FROM ghcr.io/marshalx/tgcalls/manylinux2014_aarch64-webrtc:latest

ENV PLATFORM manylinux2014_aarch64

COPY ../entrypoint.sh /entrypoint.sh

RUN ["chmod", "+x", "/entrypoint.sh"]
ENTRYPOINT ["/entrypoint.sh"]