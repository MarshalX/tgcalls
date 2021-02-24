ARG MANYLINUX_PLATFORM
FROM quay.io/pypa/$MANYLINUX_PLATFORM AS builder

ENV MANYLINUX_PLATFORM $MANYLINUX_PLATFORM
ENV PKG_CONFIG_PATH /usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:/usr/local/share/pkgconfig
ENV GIT https://github.com
ENV OPENSSL_VER 1_1_1
ENV OPENSSL_PREFIX /usr/local/desktop-app/openssl-1.1.1

# TODO RUN if [ "$MANYLINUX_PLATFORM" == "manylinux2014_aarch64"] ; then yum -y install https://download-ib01.fedoraproject.org/pub/epel/7/aarch64/Packages/c/cmake3-3.14.6-2.el7.aarch64.rpm ; else echo nothing to install ; fi
#RUN yum -y install epel-release
RUN yum -y install rhash libuv https://download-ib01.fedoraproject.org/pub/epel/7/aarch64/Packages/c/cmake3-data-3.14.6-2.el7.noarch.rpm
RUN yum -y install https://download-ib01.fedoraproject.org/pub/epel/7/aarch64/Packages/c/cmake3-3.14.6-2.el7.aarch64.rpm

RUN yum -y install git cmake3 meson ninja-build autoconf automake libtool \
	zlib-devel alsa-lib-devel pulseaudio-libs-devel pkgconfig bison \
	yasm file which devtoolset-8-make devtoolset-8-gcc \
	devtoolset-8-gcc-c++ devtoolset-8-binutils

SHELL [ "scl", "enable", "devtoolset-8", "--", "bash", "-c" ]
RUN ln -s cmake3 /usr/bin/cmake

ENV LibrariesPath /usr/src/Libraries
WORKDIR $LibrariesPath

FROM builder AS mozjpeg
RUN git clone -b v4.0.1-rc2 --depth=1 $GIT/mozilla/mozjpeg.git

WORKDIR mozjpeg
RUN cmake3 -B build . \
	-DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_INSTALL_PREFIX=/usr/local \
	-DCMAKE_POSITION_INDEPENDENT_CODE=ON \
	-DWITH_JPEG8=ON \
	-DPNG_SUPPORTED=OFF

RUN cmake3 --build build -j$(nproc)
RUN DESTDIR="$LibrariesPath/mozjpeg-cache" cmake3 --install build

WORKDIR ..
RUN rm -rf mozjpeg

FROM builder AS opus
RUN git clone -b v1.3 --depth=1 $GIT/xiph/opus.git

WORKDIR opus
RUN ./autogen.sh
RUN ./configure --with-pic
RUN make -j$(nproc)
RUN make DESTDIR="$LibrariesPath/opus-cache" install

WORKDIR ..
RUN rm -rf opus

FROM builder AS openssl
ENV opensslDir openssl_${OPENSSL_VER}
RUN git clone -b OpenSSL_${OPENSSL_VER}-stable --depth=1 \
	$GIT/openssl/openssl.git $opensslDir

WORKDIR ${opensslDir}
RUN ./config \
	--prefix="$OPENSSL_PREFIX" \
	--openssldir=/etc/ssl \
	no-tests \
	no-dso

RUN make -j$(nproc)
RUN make DESTDIR="$LibrariesPath/openssl-cache" install_sw

WORKDIR ..
RUN rm -rf $opensslDir

FROM builder AS ffmpeg
COPY --from=opus ${LibrariesPath}/opus-cache /
RUN git clone -b release/4.2 --depth=1 $GIT/FFmpeg/FFmpeg.git ffmpeg

WORKDIR ffmpeg
RUN ./configure \
	--disable-debug \
	--disable-programs \
	--disable-doc \
	--disable-network \
	--disable-autodetect \
	--disable-everything \
	--disable-alsa \
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

FROM builder

COPY --from=mozjpeg ${LibrariesPath}/mozjpeg-cache /
COPY --from=opus ${LibrariesPath}/opus-cache /
COPY --from=ffmpeg ${LibrariesPath}/ffmpeg ffmpeg
COPY --from=ffmpeg ${LibrariesPath}/ffmpeg-cache /
COPY --from=openssl ${LibrariesPath}/openssl-cache /
