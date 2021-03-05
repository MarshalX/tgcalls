#  tgcalls - Python binding for tgcalls (c++ lib by Telegram)
#  pytgcalls - library connecting python binding for tgcalls and pyrogram
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

from typing import Union

import pyrogram

from pytgcalls import GroupCallNative


class GroupCall(GroupCallNative):

    def __init__(
            self,
            client: pyrogram.Client,
            input_filename: str = '',
            output_filename: str = '',
            enable_logs_to_console=False,
            path_to_log_file='group_call.log'
    ):
        super().__init__(client, enable_logs_to_console, path_to_log_file)
        self.__use_file_audio_device = True

        self._input_filename = input_filename
        self._output_filename = output_filename

    async def start(self, group: Union[str, int], enable_action=True):
        self.enable_action = enable_action

        await self.get_me()
        await self.get_group_call(group)

        if self.group_call is None:
            raise RuntimeError('Chat without voice chat')

        await self._start_group_call(
            self.__use_file_audio_device, self.__get_input_filename_callback, self.__get_output_filename_callback
        )

    async def reconnect(self):
        await self.stop()

        # TODO remove magic when .stop() will be fixed
        # <-- magic part
        self.client.remove_handler(self._update_handler, -1)

        chat_peer = self.chat_peer
        enable_action = self.enable_action

        self = GroupCall(
            self.client, self._input_filename, self._output_filename, self.enable_logs_to_console, self.path_to_log_file
        )
        # --> magic part

        await self.start(chat_peer, enable_action)

    def stop_playout(self):
        self.input_filename = ''

    def stop_output(self):
        self.output_filename = ''

    @property
    def input_filename(self):
        return self._input_filename

    @input_filename.setter
    def input_filename(self, filename):
        self._input_filename = filename
        if self.is_connected:
            self.restart_playout()

    @property
    def output_filename(self):
        return self._output_filename

    @output_filename.setter
    def output_filename(self, filename):
        self._output_filename = filename
        if self.is_connected:
            self.restart_recording()

    def __get_input_filename_callback(self):
        return self._input_filename

    def __get_output_filename_callback(self):
        return self._output_filename
