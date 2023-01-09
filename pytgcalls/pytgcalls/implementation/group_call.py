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

from enum import Enum
from typing import Callable, Optional

from pytgcalls.dispatcher import Action, DispatcherMixin
from pytgcalls.implementation import GroupCallRaw, GroupCallBaseAction
from pytgcalls.utils import AudioStream, VideoStream


class MediaType(Enum):
    VIDEO = 'video'
    AUDIO = 'audio'


class GroupCallAction(GroupCallBaseAction):
    VIDEO_PLAYOUT_ENDED = Action()
    '''When a video playout will be ended.'''
    AUDIO_PLAYOUT_ENDED = Action()
    '''When a audio playout will be ended.'''
    PLAYOUT_ENDED = MEDIA_PLAYOUT_ENDED = Action()
    '''When a audio or video playout will be ended.'''


class GroupCallDispatcherMixin(DispatcherMixin):
    def on_video_playout_ended(self, func: Callable) -> Callable:
        """When a video playout will be ended.

        Args:
            func (`Callable`): A functions that accept group_call and source args.

        Returns:
            `Callable`: passed to args callback function.
        """

        return self.add_handler(func, GroupCallAction.VIDEO_PLAYOUT_ENDED)

    def on_audio_playout_ended(self, func: Callable) -> Callable:
        """When a audio playout will be ended.

        Args:
            func (`Callable`): A functions that accept group_call and source args.

        Returns:
            `Callable`: passed to args callback function.
        """

        return self.add_handler(func, GroupCallAction.AUDIO_PLAYOUT_ENDED)

    def on_media_playout_ended(self, func: Callable) -> Callable:
        """When a audio or video playout will be ended.

        Args:
            func (`Callable`): A functions that accept group_call source and media type args.

        Returns:
            `Callable`: passed to args callback function.
        """

        return self.add_handler(func, GroupCallAction.MEDIA_PLAYOUT_ENDED)

    # alias
    on_playout_ended = on_media_playout_ended


class GroupCall(GroupCallRaw, GroupCallDispatcherMixin):
    def __init__(
        self,
        mtproto_bridge,
        enable_logs_to_console=False,
        path_to_log_file=None,
        outgoing_audio_bitrate_kbit=128,
    ):
        super().__init__(
            mtproto_bridge,
            self.__on_audio_played_data,
            self.__on_audio_recorded_data,
            self.__on_video_played_data,
            enable_logs_to_console,
            path_to_log_file,
            outgoing_audio_bitrate_kbit,
        )
        super(GroupCallDispatcherMixin, self).__init__(GroupCallAction)

    def __trigger_on_video_playout_ended(self, source):
        self.trigger_handlers(GroupCallAction.VIDEO_PLAYOUT_ENDED, self, source)

    def __trigger_on_audio_playout_ended(self, source):
        self.trigger_handlers(GroupCallAction.AUDIO_PLAYOUT_ENDED, self, source)

    def __trigger_on_media_playout_ended(self, source, media_type: MediaType):
        self.trigger_handlers(GroupCallAction.MEDIA_PLAYOUT_ENDED, self, source, media_type)

    def __combined_video_trigger(self, source):
        self.__trigger_on_video_playout_ended(source)
        self.__trigger_on_media_playout_ended(source, MediaType.VIDEO)

    def __combined_audio_trigger(self, source):
        self.__trigger_on_audio_playout_ended(source)
        self.__trigger_on_media_playout_ended(source, MediaType.AUDIO)

    @staticmethod
    def __on_video_played_data(self: 'GroupCallRaw') -> bytes:
        if self._video_stream:
            return self._video_stream.read()

    @staticmethod
    def __on_audio_played_data(self: 'GroupCallRaw', length: int) -> bytes:
        if self._audio_stream:
            return self._audio_stream.read(length)

    @staticmethod
    def __on_audio_recorded_data(self, data, length):
        # TODO
        pass

    async def join(self, group, join_as=None, invite_hash: Optional[str] = None, enable_action=True):
        return await self.start(group, join_as, invite_hash, enable_action)

    async def leave(self):
        return await self.stop()

    async def start_video(
        self, source: Optional[str] = None, with_audio=True, repeat=True, enable_experimental_lip_sync=False
    ):
        """Enable video playing for current group call.

        Note:
            Source is video file or image file sequence or a
            capturing device or a IP video stream for video capturing.

            To use device camera you need to pass device index as int to the `source` arg.

        Args:
            source (`str`): Path to filename or device index or URL with some protocol. For example RTCP.
            with_audio (`bool`): Get and play audio stream from video source.
            repeat (`bool`): rewind video when end of file.
            enable_experimental_lip_sync (`bool`): enable experimental lip sync feature.
        """

        if self._video_stream and self._video_stream.is_running:
            self._video_stream.stop()

        self._video_stream = VideoStream(source, repeat, self.__combined_video_trigger)
        self._configure_video_capture(self._video_stream.get_video_info())

        if with_audio:
            await self.start_audio(source, repeat, self._video_stream if enable_experimental_lip_sync else None)
        self._video_stream.start()

        self._is_video_stopped = False
        if self.is_connected:
            await self.edit_group_call(video_stopped=False)

    async def start_audio(self, source: Optional[str] = None, repeat=True, video_stream: Optional[VideoStream] = None):
        """Enable audio playing for current group call.

        Note:
            Source is audio file or direct URL to file or audio live stream.

            If the source is None then empty bytes will be sent.

        Args:
            source (`str`, optional): Path to filename or URL to audio file or URL to live stream.
            repeat (`bool`, optional): rewind audio when end of file.
            video_stream (`VideoStream`, optional): stream to sync.
        """

        if self._audio_stream and self._audio_stream.is_running:
            self._audio_stream.stop()

        if source is not None:
            self._audio_stream = AudioStream(
                source, repeat, self.__combined_audio_trigger, video_stream=video_stream
            ).start()

        if self.is_connected:
            await self.edit_group_call(muted=False)

    async def start_audio_record(self, path):
        # TODO
        pass

    async def set_video_pause(self, pause: bool, with_mtproto=True):
        self._is_video_paused = pause
        if self.is_connected and with_mtproto:
            await self.edit_group_call(video_paused=pause)
        if self._video_stream:
            self._video_stream.set_pause(pause)

    async def set_audio_pause(self, pause: bool, with_mtproto=True):
        self._is_muted = pause
        if self.is_connected and with_mtproto:
            await self.edit_group_call(muted=pause)
        if self._audio_stream:
            self._audio_stream.set_pause(pause)

    async def set_pause(self, pause: bool):
        await self.set_video_pause(pause, False)
        await self.set_audio_pause(pause, False)

        if self.is_connected:
            # optimize 2 queries into 1
            await self.edit_group_call(muted=pause, video_paused=pause)

    async def stop_audio(self, with_mtproto=True):
        if self._audio_stream and self._audio_stream.is_running:
            self._audio_stream.stop()

        if self.is_connected and with_mtproto:
            await self.edit_group_call(muted=True)

    async def stop_video(self, with_mtproto=True):
        if self._video_stream and self._video_stream.is_running:
            self._video_stream.stop()

        if self.is_connected and with_mtproto:
            await self.edit_group_call(video_stopped=True)

    async def stop_media(self):
        await self.stop_video(False)
        await self.stop_audio(False)

        if self.is_connected:
            # optimize 2 queries into 1
            await self.edit_group_call(video_stopped=True, muted=True)

    @property
    def is_video_paused(self):
        return self._video_stream and self._video_stream.is_paused

    @property
    def is_audio_paused(self):
        return self._audio_stream and self._audio_stream.is_paused

    @property
    def is_paused(self):
        return self.is_video_paused and self.is_audio_paused

    @property
    def is_video_running(self):
        return self._video_stream and self._video_stream.is_running

    @property
    def is_audio_running(self):
        return self._audio_stream and self._audio_stream.is_running

    @property
    def is_running(self):
        return self.is_video_running and self.is_audio_running
