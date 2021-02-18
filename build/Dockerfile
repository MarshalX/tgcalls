FROM ghcr.io/marshalx/tgcalls/manylinux2014_x86_64:latest

ENV PLATFORM manylinux2014_x86_64

COPY entrypoint.sh /entrypoint.sh

RUN ["chmod", "+x", "/entrypoint.sh"]
ENTRYPOINT ["/entrypoint.sh"]