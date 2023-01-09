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

import importlib
from importlib.util import find_spec
from typing import Callable, Optional, Union

from pytgcalls.exceptions import PytgcallsBaseException, PytgcallsError
from pytgcalls.group_call_type import GroupCallType
from pytgcalls.implementation.group_call import GroupCall
from pytgcalls.mtproto_client_type import MTProtoClientType
from pytgcalls.implementation.group_call_file import GroupCallFile
from pytgcalls.implementation.group_call_device import GroupCallDevice
from pytgcalls.implementation.group_call_raw import GroupCallRaw


def hot_load_mtproto_lib_or_exception(module):
    if find_spec(module):
        importlib.import_module(module)
    else:
        raise PytgcallsBaseException(
            f'To use this MTProto client type you need to install {module.capitalize()}. '
            f'Run this command: pip3 install -U pytgcalls[{module}]'
        )


class GroupCallFactory:
    MTPROTO_CLIENT_TYPE = MTProtoClientType
    GROUP_CALL_TYPE = GroupCallType

    GROUP_CALL_CLASS_TO_TYPE = {
        GROUP_CALL_TYPE.FILE: GroupCallFile,
        GROUP_CALL_TYPE.DEVICE: GroupCallDevice,
        GROUP_CALL_TYPE.RAW: GroupCallRaw,
    }

    def __init__(
        self,
        client,
        mtproto_backend=MTProtoClientType.PYROGRAM,
        enable_logs_to_console=False,
        path_to_log_file=None,
        outgoing_audio_bitrate_kbit=128,
    ):
        self.client = client

        if mtproto_backend is MTProtoClientType.PYROGRAM:
            hot_load_mtproto_lib_or_exception(MTProtoClientType.PYROGRAM.value)
            from pytgcalls.mtproto.pyrogram_bridge import PyrogramBridge

            self.__mtproto_bride_class = PyrogramBridge
        elif mtproto_backend is MTProtoClientType.TELETHON:
            hot_load_mtproto_lib_or_exception(MTProtoClientType.TELETHON.value)
            from pytgcalls.mtproto.telethon_bridge import TelethonBridge

            self.__mtproto_bride_class = TelethonBridge
        else:
            raise PytgcallsError('Unknown MTProto client type')

        self.enable_logs_to_console = enable_logs_to_console
        self.path_to_log_file = path_to_log_file
        self.outgoing_audio_bitrate_kbit = outgoing_audio_bitrate_kbit

    def get_mtproto_bridge(self):
        return self.__mtproto_bride_class(self.client)

    def get(self, group_call_type: GroupCallType, **kwargs) -> Union[GroupCallFile, GroupCallDevice, GroupCallRaw]:
        return GroupCallFactory.GROUP_CALL_CLASS_TO_TYPE[group_call_type](
            mtproto_bridge=self.get_mtproto_bridge(),
            enable_logs_to_console=self.enable_logs_to_console,
            path_to_log_file=self.path_to_log_file,
            outgoing_audio_bitrate_kbit=self.outgoing_audio_bitrate_kbit,
            **kwargs,
        )

    def get_group_call(self) -> GroupCall:
        return GroupCall(
            self.get_mtproto_bridge(),
            self.enable_logs_to_console,
            self.path_to_log_file,
            self.outgoing_audio_bitrate_kbit,
        )

    def get_file_group_call(
        self, input_filename: Optional[str] = None, output_filename: Optional[str] = None, play_on_repeat=True
    ) -> GroupCallFile:
        return GroupCallFile(
            self.get_mtproto_bridge(),
            input_filename,
            output_filename,
            play_on_repeat,
            self.enable_logs_to_console,
            self.path_to_log_file,
            self.outgoing_audio_bitrate_kbit,
        )

    def get_device_group_call(
        self, audio_input_device: Optional[str] = None, audio_output_device: Optional[str] = None
    ) -> GroupCallDevice:
        return GroupCallDevice(
            self.get_mtproto_bridge(),
            audio_input_device,
            audio_output_device,
            self.enable_logs_to_console,
            self.path_to_log_file,
            self.outgoing_audio_bitrate_kbit,
        )

    def get_raw_group_call(
        self,
        on_played_data: Callable[['GroupCallRaw', int], bytes] = None,
        on_recorded_data: Callable[['GroupCallRaw', bytes, int], None] = None,
        on_video_played_data: Callable[['GroupCallRaw'], bytes] = None,
    ) -> GroupCallRaw:
        return GroupCallRaw(
            self.get_mtproto_bridge(),
            on_played_data,
            on_recorded_data,
            on_video_played_data,
            self.enable_logs_to_console,
            self.path_to_log_file,
            self.outgoing_audio_bitrate_kbit,
        )
