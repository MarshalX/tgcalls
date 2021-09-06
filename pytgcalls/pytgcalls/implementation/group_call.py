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

from typing import Optional

from pytgcalls.implementation import GroupCallRaw
from pytgcalls.utils import AudioStream, VideoStream


class GroupCall(GroupCallRaw):
    def __init__(
        self,
        mtproto_bridge,
        enable_logs_to_console=False,
        path_to_log_file=None,
        outgoing_audio_bitrate_kbit=128,
    ):
        super().__init__(
            mtproto_bridge,
            self.__on_played_data,
            self.__on_recorded_data,
            enable_logs_to_console,
            path_to_log_file,
            outgoing_audio_bitrate_kbit,
        )

    @staticmethod
    def __on_played_data(self: 'GroupCallRaw', length: int) -> bytes:
        if self._audio_stream:
            return self._audio_stream.read(length)

    @staticmethod
    def __on_recorded_data(self, data, length):
        # TODO
        pass

    async def join(self, group, join_as=None, invite_hash: Optional[str] = None, enable_action=True):
        return await self.start(group, join_as, invite_hash, enable_action)

    async def start_video(self, source: str, with_audio=True, repeat=True):
        """Enable video playing for current group call.

        Note:
            Source is video file or image file sequence or a
            capturing device or a IP video stream for video capturing.

            To use device camera you need to pass device index as int to the `source` arg.

        Args:
            source (`str`): Path to filename or device index or URL with some protocol. For example RTCP.
            with_audio (`bool`): Get and play audio stream from video source.
            repeat (`bool`): rewind video when end of file.
        """

        if with_audio:
            await self.start_audio(source, repeat)

        if self._video_stream:
            self._video_stream.stop()

        self._video_stream = VideoStream(source, repeat)
        video_info = self._video_stream.get_video_info()

        def get_next_frame_buffer():
            return self._video_stream.read()

        self._set_video_capture(get_next_frame_buffer, video_info.width, video_info.height, video_info.fps)

        self._video_stream.start()

        self._is_video_stopped = False
        if self.is_connected:
            await self.edit_group_call(video_stopped=False)

    async def start_audio(self, source: str, repeat=True):
        """Enable audio playing for current group call.

        Note:
            Source is audio file or direct URL to file or audio live stream..

        Args:
            source (`str`): Path to filename or URL to audio file or URL to live stream.
            repeat (`bool`): rewind audio when end of file.
        """

        if self._audio_stream:
            self._audio_stream.stop()

        self._audio_stream = AudioStream(source, repeat).start()

    async def start_audio_record(self, path):
        # TODO
        pass
