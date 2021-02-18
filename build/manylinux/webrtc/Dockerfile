ARG MANYLINUX_PLATFORM
FROM ghcr.io/marshalx/tgcalls/$MANYLINUX_PLATFORM:latest AS builder

FROM builder AS webrtc

COPY tgcalls/third_party/webrtc ${LibrariesPath}/webrtc

WORKDIR webrtc

RUN cmake3 -B out/Release . \
	-DCMAKE_BUILD_TYPE=Release \
	-DTG_OWT_SPECIAL_TARGET=linux \
	-DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
	-DTG_OWT_LIBJPEG_INCLUDE_PATH=/usr/local/include \
	-DTG_OWT_OPENSSL_INCLUDE_PATH=$OPENSSL_PREFIX/include \
	-DTG_OWT_OPUS_INCLUDE_PATH=/usr/local/include/opus \
	-DTG_OWT_FFMPEG_INCLUDE_PATH=/usr/local/include
RUN cmake --build out/Release -- -j$(nproc)

RUN cmake3 -B out/Debug . \
	-DCMAKE_BUILD_TYPE=Debug \
	-DTG_OWT_SPECIAL_TARGET=linux \
	-DCMAKE_POSITION_INDEPENDENT_CODE=ON \
	-DTG_OWT_LIBJPEG_INCLUDE_PATH=/usr/local/include \
	-DTG_OWT_OPENSSL_INCLUDE_PATH=$OPENSSL_PREFIX/include \
	-DTG_OWT_OPUS_INCLUDE_PATH=/usr/local/include/opus \
	-DTG_OWT_FFMPEG_INCLUDE_PATH=/usr/local/include
RUN cmake --build out/Debug -- -j$(nproc)

WORKDIR ..

FROM builder

COPY --from=webrtc ${LibrariesPath}/webrtc tg_owt
