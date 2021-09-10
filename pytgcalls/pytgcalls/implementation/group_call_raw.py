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

from typing import Callable

import tgcalls
from pytgcalls.implementation import GroupCallBase
from pytgcalls.utils import DEFAULT_COLOR_DEPTH, VideoInfo


class GroupCallRaw(GroupCallBase):
    def __init__(
        self,
        mtproto_bridge,
        on_audio_played_data: Callable[['GroupCallRaw', int], bytes] = None,
        on_audio_recorded_data: Callable[['GroupCallRaw', bytes, int], None] = None,
        on_video_played_data: Callable[['GroupCallRaw'], bytes] = None,
        enable_logs_to_console=False,
        path_to_log_file=None,
        outgoing_audio_bitrate_kbit=128,
    ):
        super().__init__(mtproto_bridge, enable_logs_to_console, path_to_log_file, outgoing_audio_bitrate_kbit)

        self.__is_playout_paused = False
        self.__is_recording_paused = False

        self.__raw_audio_device_descriptor = None

        self.on_audio_played_data = on_audio_played_data
        self.on_audio_recorded_data = on_audio_recorded_data

        self.on_video_played_data = on_video_played_data

    def __create_and_return_raw_audio_device_descriptor(self):
        self.__raw_audio_device_descriptor = tgcalls.RawAudioDeviceDescriptor()
        self.__raw_audio_device_descriptor.getPlayedBufferCallback = self.__get_played_audio_buffer_callback
        self.__raw_audio_device_descriptor.setRecordedBufferCallback = self.__set_recorded_audio_buffer_callback
        self.__raw_audio_device_descriptor.isPlayoutPaused = self.__is_playout_paused_callback
        self.__raw_audio_device_descriptor.isRecordingPaused = self.__is_recording_paused_callback

        return self.__raw_audio_device_descriptor

    def _setup_and_start_group_call(self):
        self._start_native_group_call(self.__create_and_return_raw_audio_device_descriptor())
        self._configure_video_capture(VideoInfo.default())

    def _configure_video_capture(self, video_info: VideoInfo):
        self._set_video_capture(
            self.__get_played_video_buffer_callback, video_info.width, video_info.height, video_info.fps
        )

    def __get_played_video_buffer_callback(self):
        frame = b''
        if self.on_video_played_data:
            data = self.on_video_played_data(self)
            if data:
                frame = data

        video_info = VideoInfo.default()
        if self._video_stream:
            video_info = self._video_stream.get_video_info()

        frame_size = video_info.width * video_info.width * DEFAULT_COLOR_DEPTH
        return frame.ljust(frame_size, b'\0')

    def __get_played_audio_buffer_callback(self, length: int):
        frame = b''
        if self.on_audio_played_data:
            data = self.on_audio_played_data(self, length)
            if data:
                frame = data

        return frame.ljust(length, b'\0')

    def __set_recorded_audio_buffer_callback(self, frame: bytes, length: int):
        if self.on_audio_recorded_data:
            self.on_audio_recorded_data(self, frame, length)

    def __is_playout_paused_callback(self):
        # native pausing from cpp side. old way to impl it
        return self.__is_playout_paused

    def __is_recording_paused_callback(self):
        # native pausing from cpp side. old way to impl it
        return self.__is_recording_paused
