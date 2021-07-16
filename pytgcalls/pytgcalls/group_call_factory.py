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

from typing import Callable, Optional

from pytgcalls.group_call_type import GroupCallType
from pytgcalls.mtproto_client_type import MTProtoClientType
from pytgcalls.implementation.group_call_file import GroupCallFile
from pytgcalls.implementation.group_call_device import GroupCallDevice
from pytgcalls.implementation.group_call_raw import GroupCallRaw

from pytgcalls.mtproto import PyrogramBridge, TelethonBridge


class GroupCallFactory:
    MTPROTO_CLIENT_TYPE = MTProtoClientType
    GROUP_CALL_TYPE = GroupCallType

    GROUP_CALL_CLASS_TO_TYPE = {
        GROUP_CALL_TYPE.FILE: GroupCallFile,
        GROUP_CALL_TYPE.DEVICE: GroupCallDevice,
        GROUP_CALL_TYPE.RAW: GroupCallRaw,
    }

    def __init__(
        self, client, mtproto_backend=MTProtoClientType.PYROGRAM, enable_logs_to_console=False, path_to_log_file=None
    ):
        if mtproto_backend is MTProtoClientType.PYROGRAM:
            self.mtproto_bride = PyrogramBridge(client)
        elif mtproto_backend is MTProtoClientType.TELETHON:
            self.mtproto_bride = TelethonBridge(client)
            raise NotImplementedError('Telethon bridge not ready yet. Soon.')
        else:
            raise RuntimeError('Unknown MTProto client type')

        self.enable_logs_to_console = enable_logs_to_console
        self.path_to_log_file = path_to_log_file

    def get(self, group_call_type: GroupCallType, **kwargs):
        return GroupCallFactory.GROUP_CALL_CLASS_TO_TYPE[group_call_type](
            mtproto_bridge=self.mtproto_bride,
            enable_logs_to_console=self.enable_logs_to_console,
            path_to_log_file=self.path_to_log_file,
            **kwargs,
        )

    def get_file_group_call(
        self, input_filename: Optional[str] = None, output_filename: Optional[str] = None, play_on_repeat=True
    ):
        return GroupCallFile(
            self.mtproto_bride,
            input_filename,
            output_filename,
            play_on_repeat,
            self.enable_logs_to_console,
            self.path_to_log_file,
        )

    def get_device_group_call(
        self, audio_input_device: Optional[str] = None, audio_output_device: Optional[str] = None
    ):
        return GroupCallDevice(
            self.mtproto_bride,
            audio_input_device,
            audio_output_device,
            self.enable_logs_to_console,
            self.path_to_log_file,
        )

    def get_raw_group_call(
        self,
        on_played_data: Callable[['GroupCallRaw', int], bytes] = None,
        on_recorded_data: Callable[['GroupCallRaw', bytes, int], None] = None,
    ):
        return GroupCallRaw(
            self.mtproto_bride, on_played_data, on_recorded_data, self.enable_logs_to_console, self.path_to_log_file
        )
