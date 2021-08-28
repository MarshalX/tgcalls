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

from queue import Queue
from threading import Thread

import cv2


uint_ssrc = lambda ssrc: ssrc if ssrc >= 0 else ssrc + 2 ** 32
int_ssrc = lambda ssrc: ssrc if ssrc < 2 ** 31 else ssrc - 2 ** 32

# increasing this value will increase memory usage
QUEUE_SIZE = 64


class VideoStream:
    def __init__(self, source, queue_size=QUEUE_SIZE):
        # TODO detect fps, h, w
        self.video_capture = cv2.VideoCapture(source)
        self.queue = Queue(maxsize=queue_size)

        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True

        self.is_running = False

    def start(self):
        self.is_running = True
        self.thread.start()
        return self

    def read(self):
        return self.queue.get()

    def stop(self):
        self.is_running = False

    def update(self):
        while True:
            if not self.is_running:
                return

            if not self.queue.full():
                grabbed, frame = self.video_capture.read()
                if not grabbed:
                    self.stop()
                    return

                rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                self.queue.put(rgba.tobytes())
