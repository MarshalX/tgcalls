ARG MANYLINUX_PLATFORM
FROM quay.io/pypa/$MANYLINUX_PLATFORM AS builder

ENV PKG_CONFIG_PATH /usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:/usr/local/share/pkgconfig
ENV OPENSSL_PREFIX /usr/local/desktop-app/openssl-1.1.1

RUN yum -y install epel-release

RUN yum -y install wget git cmake3 meson ninja-build autoconf automake libtool \
	zlib-devel alsa-lib-devel pulseaudio-libs-devel pkgconfig bison \
	yasm file which devtoolset-8-make devtoolset-8-gcc \
	devtoolset-8-gcc-c++ devtoolset-8-binutils

SHELL [ "scl", "enable", "devtoolset-8", "--", "bash", "-c" ]
RUN ln -s cmake3 /usr/bin/cmake

ENV MainPath /usr/src
ENV LibrariesPath ${MainPath}/Libraries
WORKDIR $LibrariesPath

FROM builder AS mozjpeg
RUN git clone -b v4.0.1-rc2 --depth=1 https://github.com/mozilla/mozjpeg.git

WORKDIR mozjpeg
RUN cmake -B build . \
	-DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_INSTALL_PREFIX=/usr/local \
	-DCMAKE_POSITION_INDEPENDENT_CODE=ON \
	-DWITH_JAVA=OFF \
    -DWITH_JPEG8=ON \
    -DPNG_SUPPORTED=OFF

RUN cmake --build build -j$(nproc)
RUN DESTDIR="$LibrariesPath/mozjpeg-cache" cmake --install build

WORKDIR ..

FROM builder AS opus
RUN git clone -b v1.3 --depth=1 https://github.com/xiph/opus.git

WORKDIR opus
RUN ./autogen.sh
RUN ./configure --with-pic
RUN make -j$(nproc)
RUN make DESTDIR="$LibrariesPath/opus-cache" install

FROM builder AS openssl
ENV opensslDir openssl_1_1_1
RUN git clone -b OpenSSL_1_1_1-stable --depth=1 \
	https://github.com/openssl/openssl.git $opensslDir

WORKDIR ${opensslDir}
RUN ./config \
	--prefix="$OPENSSL_PREFIX" \
	--openssldir=/etc/ssl \
	no-tests \
	no-dso

RUN make -j$(nproc)
RUN make DESTDIR="$LibrariesPath/openssl-cache" install_sw

WORKDIR ..

FROM builder AS ffmpeg
COPY --from=opus ${LibrariesPath}/opus-cache /
RUN git clone -b release/4.4 --depth=1 https://github.com/FFmpeg/FFmpeg.git ffmpeg

WORKDIR ffmpeg
RUN ./configure \
	--disable-debug \
	--disable-programs \
	--disable-doc \
	--disable-network \
	--disable-autodetect \
	--disable-everything \
	--disable-asm \
	--disable-iconv \
	--disable-shared \
	--enable-static \
	--enable-libopus \
	--enable-pic \
	--enable-protocol=file \
	--enable-hwaccel=h264_vaapi \
	--enable-hwaccel=h264_vdpau \
	--enable-hwaccel=mpeg4_vaapi \
	--enable-hwaccel=mpeg4_vdpau \
	--enable-decoder=aac \
	--enable-decoder=aac_fixed \
	--enable-decoder=aac_latm \
	--enable-decoder=aasc \
	--enable-decoder=alac \
	--enable-decoder=flac \
	--enable-decoder=gif \
	--enable-decoder=h264 \
	--enable-decoder=h264_vdpau \
	--enable-decoder=hevc \
	--enable-decoder=mp1 \
	--enable-decoder=mp1float \
	--enable-decoder=mp2 \
	--enable-decoder=mp2float \
	--enable-decoder=mp3 \
	--enable-decoder=mp3adu \
	--enable-decoder=mp3adufloat \
	--enable-decoder=mp3float \
	--enable-decoder=mp3on4 \
	--enable-decoder=mp3on4float \
	--enable-decoder=mpeg4 \
	--enable-decoder=mpeg4_vdpau \
	--enable-decoder=msmpeg4v2 \
	--enable-decoder=msmpeg4v3 \
	--enable-decoder=opus \
	--enable-decoder=pcm_alaw \
	--enable-decoder=pcm_f32be \
	--enable-decoder=pcm_f32le \
	--enable-decoder=pcm_f64be \
	--enable-decoder=pcm_f64le \
	--enable-decoder=pcm_lxf \
	--enable-decoder=pcm_mulaw \
	--enable-decoder=pcm_s16be \
	--enable-decoder=pcm_s16be_planar \
	--enable-decoder=pcm_s16le \
	--enable-decoder=pcm_s16le_planar \
	--enable-decoder=pcm_s24be \
	--enable-decoder=pcm_s24daud \
	--enable-decoder=pcm_s24le \
	--enable-decoder=pcm_s24le_planar \
	--enable-decoder=pcm_s32be \
	--enable-decoder=pcm_s32le \
	--enable-decoder=pcm_s32le_planar \
	--enable-decoder=pcm_s64be \
	--enable-decoder=pcm_s64le \
	--enable-decoder=pcm_s8 \
	--enable-decoder=pcm_s8_planar \
	--enable-decoder=pcm_u16be \
	--enable-decoder=pcm_u16le \
	--enable-decoder=pcm_u24be \
	--enable-decoder=pcm_u24le \
	--enable-decoder=pcm_u32be \
	--enable-decoder=pcm_u32le \
	--enable-decoder=pcm_u8 \
	--enable-decoder=pcm_zork \
	--enable-decoder=vorbis \
	--enable-decoder=wavpack \
	--enable-decoder=wmalossless \
	--enable-decoder=wmapro \
	--enable-decoder=wmav1 \
	--enable-decoder=wmav2 \
	--enable-decoder=wmavoice \
	--enable-encoder=libopus \
	--enable-parser=aac \
	--enable-parser=aac_latm \
	--enable-parser=flac \
	--enable-parser=h264 \
	--enable-parser=hevc \
	--enable-parser=mpeg4video \
	--enable-parser=mpegaudio \
	--enable-parser=opus \
	--enable-parser=vorbis \
	--enable-demuxer=aac \
	--enable-demuxer=flac \
	--enable-demuxer=gif \
	--enable-demuxer=h264 \
	--enable-demuxer=hevc \
	--enable-demuxer=m4v \
	--enable-demuxer=mov \
	--enable-demuxer=mp3 \
	--enable-demuxer=ogg \
	--enable-demuxer=wav \
	--enable-muxer=ogg \
	--enable-muxer=opus

RUN make -j$(nproc)
RUN make DESTDIR="$LibrariesPath/ffmpeg-cache" install

WORKDIR ..

FROM builder AS webrtc

COPY --from=mozjpeg ${LibrariesPath}/mozjpeg-cache /
COPY --from=opus ${LibrariesPath}/opus-cache /
COPY --from=ffmpeg ${LibrariesPath}/ffmpeg-cache /
COPY --from=openssl ${LibrariesPath}/openssl-cache /

COPY tgcalls/third_party/webrtc ${LibrariesPath}/webrtc

WORKDIR webrtc

RUN cmake -B out/Release . \
    -DCMAKE_BUILD_TYPE=Release \
    -DTG_OWT_SPECIAL_TARGET=linux \
    -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DTG_OWT_USE_PIPEWIRE=OFF \
    -DTG_OWT_LIBJPEG_INCLUDE_PATH=/usr/local/include \
    -DTG_OWT_OPENSSL_INCLUDE_PATH=$OPENSSL_PREFIX/include \
    -DTG_OWT_OPUS_INCLUDE_PATH=/usr/local/include/opus \
    -DTG_OWT_FFMPEG_INCLUDE_PATH=/usr/local/include
RUN cmake --build out/Release -- -j$(nproc)

WORKDIR ..

FROM builder

COPY --from=mozjpeg ${LibrariesPath}/mozjpeg-cache /
COPY --from=opus ${LibrariesPath}/opus-cache /
COPY --from=ffmpeg ${LibrariesPath}/ffmpeg ffmpeg
COPY --from=ffmpeg ${LibrariesPath}/ffmpeg-cache /
COPY --from=openssl ${LibrariesPath}/openssl-cache /
COPY --from=webrtc ${LibrariesPath}/webrtc tg_owt

WORKDIR ..
COPY ./ ${MainPath}/tgcalls
WORKDIR ${MainPath}/tgcalls

COPY ./build/manylinux/dev/entrypoint.sh /entrypoint.sh

RUN ["chmod", "+x", "/entrypoint.sh"]
ENTRYPOINT ["/entrypoint.sh"]
