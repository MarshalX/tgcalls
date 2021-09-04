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
QUEUE_SIZE = 64
FRAME_PLACEHOLDER_FILENAME = 'frame_placeholder'
FRAME_PLACEHOLDER_PATH = path.join(base_path, FRAME_PLACEHOLDER_FILENAME)

DEFAULT_REQUESTED_AUDIO_BYTES_LENGTH = 1920
BYTES_PER_AUDIO_SAMPLE = 4
SAMPLES_TO_STORE_MULTIPLIER = 2


class VideoInfo:
    def __init__(self, width: int, height: int, fps: int):
        self.width = width
        self.height = height
        self.fps = fps


class VideoStream:
    __DEFAULT_VIDEO_INFO = VideoInfo(1280, 720, 30)

    def __init__(self, source, repeat, queue_size=QUEUE_SIZE):
        self.video_capture = None
        if source is not None:
            self.video_capture = cv2.VideoCapture(source)

        self.repeat = repeat

        self.queue_size = queue_size
        self.__queue = self.create_queue()

        self.thread = Thread(target=self.__update, args=())
        self.thread.daemon = True

        self.is_running = False

        self.__frame_placeholder = None

    def create_queue(self, queue_size=None):
        if not queue_size:
            queue_size = self.queue_size

        return Queue(maxsize=queue_size)

    def start(self):
        with open(FRAME_PLACEHOLDER_PATH, 'rb') as f:
            self.__frame_placeholder = f.read()

        self.is_running = True
        self.thread.start()
        return self

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
            return self.__queue.get_nowait()
        except Empty:
            # if thread wasn't started
            return self.__frame_placeholder

    def stop(self):
        self.is_running = False

        if self.video_capture:
            self.video_capture.release()

        self.__queue = self.create_queue()

    def __add_placeholder_frame(self):
        self.__queue.put(self.__frame_placeholder)

    def __update(self):
        while True:
            if not self.is_running:
                return

            # when video file hasn't been passed
            if not self.video_capture:
                self.__add_placeholder_frame()
                continue

            if self.video_capture and self.video_capture.isOpened():
                grabbed, frame = self.video_capture.read()
                if not grabbed or frame is None:
                    if self.repeat:
                        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 1)
                    else:
                        self.__add_placeholder_frame()
                    continue

                rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                self.__queue.put(rgba.tobytes())


class AudioStream:
    __REQUESTED_AUDIO_BYTES_LENGTH = DEFAULT_REQUESTED_AUDIO_BYTES_LENGTH
    __SAMPLES_TO_STORE = __REQUESTED_AUDIO_BYTES_LENGTH // BYTES_PER_AUDIO_SAMPLE * SAMPLES_TO_STORE_MULTIPLIER

    def __init__(self, source: str, repeat: bool, queue_size=QUEUE_SIZE):
        self.__input_container = av.open(source)
        if not len(self.__input_container.streams.audio):
            raise RuntimeError('Cant find audio stream')

        self.__audio_resampler = av.AudioResampler(format='s16', layout='stereo', rate=48000)
        self.__audio_stream_iter = self.__get_decoded_iter()

        self.repeat = repeat

        self.queue_size = queue_size
        self.__queue = self.create_queue()

        self.thread = Thread(target=self.__update, args=())
        self.thread.daemon = True

        self.is_running = False

    def create_queue(self, queue_size=None):
        if not queue_size:
            queue_size = self.queue_size

        return Queue(maxsize=queue_size)

    def __get_decoded_iter(self):
        self.__input_container.seek(0)
        return iter(self.__input_container.decode(audio=0))

    def start(self):
        self.is_running = True
        self.thread.start()
        return self

    def stop(self):
        self.is_running = False

    def read(self, length: int):
        if not self.__REQUESTED_AUDIO_BYTES_LENGTH:
            self.__REQUESTED_AUDIO_BYTES_LENGTH = length
            self.__SAMPLES_TO_STORE = (
                self.__REQUESTED_AUDIO_BYTES_LENGTH // BYTES_PER_AUDIO_SAMPLE * SAMPLES_TO_STORE_MULTIPLIER
            )

        try:
            return self.__queue.get_nowait()
        except Empty:
            pass

    def __update(self):
        tail = b''

        while True:
            if not self.is_running:
                return

            try:
                frame = next(self.__audio_stream_iter)
                frame.pts = None
            except StopIteration:
                if self.repeat:
                    self.__audio_stream_iter = self.__get_decoded_iter()
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
                    self.__queue.put(frame)
                else:
                    tail = frame
