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

from os import path
from queue import Empty, Queue
from threading import Thread

import cv2
import av


base_path = path.abspath(path.dirname(__file__))

uint_ssrc = lambda ssrc: ssrc if ssrc >= 0 else ssrc + 2 ** 32
int_ssrc = lambda ssrc: ssrc if ssrc < 2 ** 31 else ssrc - 2 ** 32

# increasing this value will increase memory usage
QUEUE_SIZE = 10

DEFAULT_COLOR_DEPTH = 4
DEFAULT_REQUESTED_AUDIO_BYTES_LENGTH = 1920
DEFAULT_AUDIO_SAMPLE_RATE = 48000
REVERSED_AUDIO_SAMPLE_RATE = {
    48000: 44100,
    44100: 48000,
}


class VideoInfo:
    def __init__(self, width: int, height: int, fps: int):
        self.width = width
        self.height = height
        self.fps = fps


class QueueStream:
    def __init__(self, queue_size=QUEUE_SIZE):
        self.queue_size = queue_size
        self.__queue = self.create_queue()

        self.thread = Thread(target=self._update, args=())
        self.thread.daemon = True

        self.is_running = False

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
    __DEFAULT_VIDEO_INFO = VideoInfo(1280, 720, 30)

    def __init__(self, source, repeat, queue_size=QUEUE_SIZE):
        super().__init__(queue_size)

        self.video_capture = None
        if source is not None:
            self.video_capture = cv2.VideoCapture(source)
            self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 2)

        self.repeat = repeat

        self.__last_frame = None

    def start(self):
        return super().start()

    def get_video_info(self) -> VideoInfo:
        if self.video_capture and self.video_capture.isOpened():
            return VideoInfo(
                round(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                round(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                round(self.video_capture.get(cv2.CAP_PROP_FPS)),
            )

        return self.__DEFAULT_VIDEO_INFO

    def read(self):
        try:
            return super().read()
        except Empty:
            if self.__last_frame:
                return self.__last_frame
            # if thread wasn't started
            return self.__generate_empty_frame()

    def stop(self):
        super().stop()

        if self.video_capture:
            self.video_capture.release()

    # may be need to move in group call raw class. like audio
    def __generate_empty_frame(self):
        frame_size = self.get_video_info().width * self.get_video_info().width * DEFAULT_COLOR_DEPTH
        return b''.ljust(frame_size, b'\0')

    def _update(self):
        while True:
            if not self.is_running:
                return

            # when video file hasn't been passed
            if not self.video_capture:
                self.put(self.__generate_empty_frame())
                continue

            if self.video_capture and self.video_capture.isOpened():
                grabbed, frame = self.video_capture.read()
                if not grabbed or frame is None:
                    if self.repeat:
                        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 1)
                    else:
                        self.put(self.__generate_empty_frame())
                    continue

                rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                rgba_bytes = rgba.tobytes()

                self.__last_frame = rgba_bytes
                self.put(rgba_bytes)


class AudioStream(QueueStream):
    __REQUESTED_AUDIO_BYTES_LENGTH = DEFAULT_REQUESTED_AUDIO_BYTES_LENGTH

    def __init__(self, source: str, repeat: bool, queue_size=QUEUE_SIZE):
        super().__init__(queue_size)

        self.__input_container = av.open(source)
        if not len(self.__input_container.streams.audio):
            raise RuntimeError('Cant find audio stream')

        codec_context = self.__input_container.streams.audio[0].codec_context

        self.__input_container.no_buffer = True
        self.__input_container.flush_packets = True
        codec_context.low_delay = True

        audio_rate = codec_context.sample_rate
        rate = REVERSED_AUDIO_SAMPLE_RATE.get(audio_rate, DEFAULT_AUDIO_SAMPLE_RATE)

        self.__audio_resampler = av.AudioResampler(format='s16', layout='stereo', rate=rate)
        self.__audio_stream_iter = iter(self.__input_container.decode(audio=0))

        self.repeat = repeat

    def stop(self):
        super().stop()
        self.__input_container.close()

    def read(self, length: int):
        self.__REQUESTED_AUDIO_BYTES_LENGTH = length

        try:
            return super().read()
        except Empty:
            pass

    def _update(self):
        tail = b''

        while True:
            if not self.is_running:
                return

            try:
                frame = next(self.__audio_stream_iter)
                frame.pts = None
            except StopIteration:
                if self.repeat:
                    self.__input_container.seek(0)
                    self.__audio_stream_iter = iter(self.__input_container.decode(audio=0))
                    continue
                else:
                    self.stop()
                    continue

            resampled_frame = self.__audio_resampler.resample(frame)

            frame_bytes = tail
            if resampled_frame:
                frame_bytes += resampled_frame.to_ndarray().tobytes()

            cut_frames = [
                frame_bytes[i : i + self.__REQUESTED_AUDIO_BYTES_LENGTH]
                for i in range(0, len(frame_bytes), self.__REQUESTED_AUDIO_BYTES_LENGTH)
            ]

            for frame in cut_frames:
                if len(frame) == self.__REQUESTED_AUDIO_BYTES_LENGTH:
                    self.put(frame)
                else:
                    tail = frame
