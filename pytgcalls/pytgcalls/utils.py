#  tgcalls - a Python binding for C++ library by Telegram
#  pytgcalls - a library connecting the Python binding with MTProto
#  Copyright (C) 2020-2021 Il`ya (Marshal) <https://github.com/MarshalX>
#
#  This file is part of tgcalls and pytgcalls.
#
#  tgcalls and pytgcalls is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  tgcalls and pytgcalls is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License v3
#  along with tgcalls. If not, see <http://www.gnu.org/licenses/>.

import os
from logging import getLogger
from queue import Empty, Queue
from threading import Lock, Thread
from typing import List, Optional

import cv2
import av


logger = getLogger(__name__)

uint_ssrc = lambda ssrc: ssrc if ssrc >= 0 else ssrc + 2 ** 32
int_ssrc = lambda ssrc: ssrc if ssrc < 2 ** 31 else ssrc - 2 ** 32

# increasing this value will increase memory usage
VIDEO_QUEUE_SIZE = 1  # 1 frame depends on FPS
AUDIO_QUEUE_SIZE = 1  # 1 frame is 10 ms

DEFAULT_COLOR_DEPTH = 4
DEFAULT_REQUESTED_AUDIO_BYTES_LENGTH = 960
DEFAULT_AUDIO_SAMPLE_RATE = 48000
REVERSED_AUDIO_SAMPLE_RATE = {
    48000: 44100,
    44100: 48000,
}

MILLIS_IN_SEC = 1000


class VideoInfo:
    def __init__(self, width: int, height: int, fps: int):
        self.width = width
        self.height = height
        self.fps = fps

    @classmethod
    def default(cls):
        return cls(1820, 720, 30)


class QueueStream:
    def __init__(self, on_end_callback, queue_size):
        self.queue_size = queue_size
        self.__queue = self.create_queue()

        self.thread = Thread(target=self._update, args=())
        self.thread.daemon = True

        self.is_running = False
        self.is_paused = False

        self._on_end_callback = on_end_callback

    def set_pause(self, pause: bool):
        self.is_paused = pause

    def create_queue(self, queue_size=None):
        if not queue_size:
            queue_size = self.queue_size

        return Queue(maxsize=queue_size)

    def start(self):
        self.is_running = True
        self.thread.start()
        return self

    def stop(self):
        self.is_running = False
        self.__queue = self.create_queue()

    def read(self):
        return self.__queue.get_nowait()

    def put(self, item, block=True):
        self.__queue.put(item, block)

    def _update(self):
        raise NotImplementedError


class VideoStream(QueueStream):
    def __init__(self, source, repeat, on_end_callback, queue_size=VIDEO_QUEUE_SIZE):
        super().__init__(on_end_callback, queue_size)

        self.source = source
        self.video_capture = None
        if source:
            self.video_capture = cv2.VideoCapture(source)
            self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.repeat = repeat

        self.__pts = 0
        self.__last_frame = None
        self.__lock = Lock()

    def start(self):
        return super().start()

    def get_video_info(self) -> VideoInfo:
        if self.video_capture and self.video_capture.isOpened():
            return VideoInfo(
                round(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                round(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                self.video_capture.get(cv2.CAP_PROP_FPS),
            )

        return VideoInfo.default()

    def read(self):
        try:
            if self.is_paused:
                raise Empty

            return super().read()
        except Empty:
            if self.__last_frame:
                return self.__last_frame

    def get_pts(self):
        return self.__pts

    def skip_next_frame(self):
        self.__lock.acquire(True)

    def get_next_frame(self) -> Optional[bytes]:
        # when video file hasn't been passed
        if not self.video_capture:
            return

        if self.video_capture and self.video_capture.isOpened():
            grabbed, frame = self.video_capture.read()
            if not grabbed or frame is None:
                self._on_end_callback(self.source)
                if self.repeat:
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 1)
                    return
                else:
                    self.stop()
                    return

            self.__pts = self.video_capture.get(cv2.CAP_PROP_POS_MSEC)

            if self.__lock.locked():
                self.__lock.release()
                return

            rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            rgba_bytes = rgba.tobytes()

            return rgba_bytes

    def _update(self):
        while True:
            if not self.is_running:
                break

            frame = self.get_next_frame()
            # if it was rewind
            if frame is None:
                continue

            self.__last_frame = frame
            # its necessary for thread blocking
            self.put(frame)

        if self.video_capture:
            self.video_capture.release()


class AudioStream(QueueStream):
    __REQUESTED_AUDIO_BYTES_LENGTH = DEFAULT_REQUESTED_AUDIO_BYTES_LENGTH

    def __init__(
        self,
        source: str,
        repeat: bool,
        on_end_callback,
        queue_size=AUDIO_QUEUE_SIZE,
        video_stream: Optional[VideoStream] = None,
    ):
        super().__init__(on_end_callback, queue_size)

        self.source = source
        self.__input_container = av.open(source)
        if not len(self.__input_container.streams.audio):
            raise RuntimeError('Cant find audio stream')

        codec_context = self.__input_container.streams.audio[0].codec_context

        self.__input_container.no_buffer = True
        self.__input_container.flush_packets = True
        codec_context.low_delay = True

        # TODO so strange dirty fix
        audio_rate = codec_context.sample_rate
        rate = REVERSED_AUDIO_SAMPLE_RATE.get(audio_rate, DEFAULT_AUDIO_SAMPLE_RATE)

        self.__audio_resampler = av.AudioResampler(format='s16', layout='mono', rate=rate)
        self.__audio_stream_iter = iter(self.__input_container.decode(audio=0))

        self.__video_stream = video_stream

        self.repeat = repeat

        self.__pts = 0
        self.__pts_offset = None

        self.__frame_tail = b''

    def read(self, length: int):
        self.__REQUESTED_AUDIO_BYTES_LENGTH = length

        try:
            if self.is_paused:
                raise Empty

            return super().read()
        except Empty:
            pass

    def get_pts(self):
        return self.__pts - self.__pts_offset

    def get_next_frame(self) -> Optional[List[bytes]]:
        try:
            frame = next(self.__audio_stream_iter)

            if self.__pts_offset is None:
                self.__pts_offset = frame.time * MILLIS_IN_SEC
            self.__pts = frame.time * MILLIS_IN_SEC

            if self.__video_stream:
                pts_diff = self.__video_stream.get_pts() - self.get_pts()
                if os.environ.get('DEBUG'):
                    if pts_diff < 0:
                        logger.debug(f'Video behind the audio {-pts_diff}')
                    if pts_diff > 0:
                        logger.debug(f'Audio behind the video {pts_diff}')

                # welcome to my magic values
                if pts_diff > 100:
                    logger.debug(f'Skip 1 audio frame')
                    frame = next(self.__audio_stream_iter)
                if pts_diff < -100:
                    logger.debug('Skip 1 video frame')
                    self.__video_stream.skip_next_frame()

            frame.pts = None
        except StopIteration:
            self._on_end_callback(self.source)
            if self.repeat:
                # TODO it doesnt work with live streams and will crash on the end of stream
                self.__input_container.seek(0)
                self.__audio_stream_iter = iter(self.__input_container.decode(audio=0))
                self.__frame_tail = b''
                return
            else:
                self.stop()
                return

        resampled_frame = self.__audio_resampler.resample(frame)

        frame_bytes = self.__frame_tail
        if resampled_frame:
            if isinstance(resampled_frame, list):
                # for av 9.0+
                frame_bytes += resampled_frame[0].to_ndarray().tobytes()
            else:
                # for av 8
                frame_bytes += resampled_frame.to_ndarray().tobytes()

        cut_frames = [
            frame_bytes[i : i + self.__REQUESTED_AUDIO_BYTES_LENGTH]
            for i in range(0, len(frame_bytes), self.__REQUESTED_AUDIO_BYTES_LENGTH)
        ]

        frames_to_return = []
        for frame in cut_frames:
            if len(frame) == self.__REQUESTED_AUDIO_BYTES_LENGTH:
                frames_to_return.append(frame)
            else:
                self.__frame_tail = frame

        return frames_to_return

    def _update(self):
        while True:
            if not self.is_running:
                break

            frame_list = self.get_next_frame()
            if frame_list is None:
                continue

            for frame in frame_list:
                self.put(frame)

        self.__input_container.close()
