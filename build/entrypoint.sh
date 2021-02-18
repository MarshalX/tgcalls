#!/bin/bash
set -e -x

PYTHON_VERSIONS=$1
MANYLINUX_PLATFORM=$2

cd /github/workspace/tgcalls/tgcalls/third_party/webrtc

cmake -B out/Debug . \
	-DCMAKE_BUILD_TYPE=Debug \
	-DTG_OWT_SPECIAL_TARGET=linux \
	-DCMAKE_POSITION_INDEPENDENT_CODE=ON \
	-DTG_OWT_LIBJPEG_INCLUDE_PATH=/usr/local/include \
	-DTG_OWT_OPENSSL_INCLUDE_PATH=$OPENSSL_PREFIX/include \
	-DTG_OWT_OPUS_INCLUDE_PATH=/usr/local/include/opus \
	-DTG_OWT_FFMPEG_INCLUDE_PATH=/usr/local/include
cmake --build out/Debug -- -j$(nproc)

# TODO rewrite

#FROM builder AS webrtc
#
#COPY --from=mozjpeg ${LibrariesPath}/mozjpeg-cache /
#COPY --from=opus ${LibrariesPath}/opus-cache /
#COPY --from=ffmpeg ${LibrariesPath}/ffmpeg-cache /
#COPY --from=openssl ${LibrariesPath}/openssl-cache /
#
#COPY tgcalls/third_party/webrtc ${LibrariesPath}/webrtc
#
#WORKDIR webrtc
#
#RUN cmake -B out/Debug . \
#	-DCMAKE_BUILD_TYPE=Debug \
#	-DTG_OWT_SPECIAL_TARGET=linux \
#	-DCMAKE_POSITION_INDEPENDENT_CODE=ON \
#	-DTG_OWT_LIBJPEG_INCLUDE_PATH=/usr/local/include \
#	-DTG_OWT_OPENSSL_INCLUDE_PATH=$OPENSSL_PREFIX/include \
#	-DTG_OWT_OPUS_INCLUDE_PATH=/usr/local/include/opus \
#	-DTG_OWT_FFMPEG_INCLUDE_PATH=/usr/local/include
#RUN cmake --build out/Debug -- -j$(nproc)
#

# COPY --from=webrtc ${LibrariesPath}/webrtc tg_owt
# TODO copy

#WORKDIR ..

#WORKDIR ..
#COPY ./ tgcalls
#WORKDIR tgcalls

# RUN python3 setup.py build --debug
#RUN /opt/python/cp37-cp37m/bin/python setup.py build --debug
# TODO path from manylinux. Matrix with python versions

# for by python version from args
# build bwheel
# auditwheel
# upload to pypi/github releases/etc
