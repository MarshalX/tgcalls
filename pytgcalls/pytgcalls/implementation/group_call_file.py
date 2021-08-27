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
from pytgcalls.implementation import GroupCall, GroupCallAction, GroupCallDispatcherMixin
from pytgcalls.dispatcher import Action


class GroupCallFileAction(GroupCallAction):
    PLAYOUT_ENDED = Action()
    '''When a input file is ended.'''


class GroupCallFileDispatcherMixin(GroupCallDispatcherMixin):
    def on_playout_ended(self, func: Callable) -> Callable:
        """When a input file is ended.

        Args:
            func (`Callable`): A functions that accept group_call and filename args.

        Returns:
            `Callable`: passed to args callback function.
        """

        return self.add_handler(func, GroupCallFileAction.PLAYOUT_ENDED)


class GroupCallFile(GroupCall, GroupCallFileDispatcherMixin):
    def __init__(
        self,
        mtproto_bridge,
        input_filename: str = None,
        output_filename: str = None,
        play_on_repeat=True,
        enable_logs_to_console=False,
        path_to_log_file=None,
        outgoing_audio_bitrate_kbit=128,
    ):
        super().__init__(mtproto_bridge, enable_logs_to_console, path_to_log_file, outgoing_audio_bitrate_kbit)
        super(GroupCallFileDispatcherMixin, self).__init__(GroupCallFileAction)

        self.play_on_repeat = play_on_repeat
        '''When the file ends, play it again'''
        self.__is_playout_paused = False
        self.__is_recording_paused = False

        self.__input_filename = input_filename or ''
        self.__output_filename = output_filename or ''

        self.__file_audio_device_descriptor = None

    def __create_and_return_file_audio_device_descriptor(self):
        self.__file_audio_device_descriptor = tgcalls.FileAudioDeviceDescriptor()
        self.__file_audio_device_descriptor.getInputFilename = self.__get_input_filename_callback
        self.__file_audio_device_descriptor.getOutputFilename = self.__get_output_filename_callback
        self.__file_audio_device_descriptor.isEndlessPlayout = self.__is_endless_playout_callback
        self.__file_audio_device_descriptor.isPlayoutPaused = self.__is_playout_paused_callback
        self.__file_audio_device_descriptor.isRecordingPaused = self.__is_recording_paused_callback
        self.__file_audio_device_descriptor.playoutEndedCallback = self.__playout_ended_callback

        return self.__file_audio_device_descriptor

    def _setup_and_start_group_call(self):
        self._start_native_group_call(self.__create_and_return_file_audio_device_descriptor())

    def stop_playout(self):
        """Stop playing of file."""

        self.input_filename = ''

    def stop_output(self):
        """Stop recording to file."""

        self.output_filename = ''

    @property
    def input_filename(self):
        """Input filename (or path) to play."""

        return self.__input_filename

    @input_filename.setter
    def input_filename(self, filename):
        self.__input_filename = filename or ''
        if self.is_connected:
            self.restart_playout()

    @property
    def output_filename(self):
        """Output filename (or path) to record."""

        return self.__output_filename

    @output_filename.setter
    def output_filename(self, filename):
        self.__output_filename = filename or ''
        if self.is_connected:
            self.restart_recording()

    def pause_playout(self):
        """Pause playout (playing from file)."""
        self.__is_playout_paused = True

    def resume_playout(self):
        """Resume playout (playing from file)."""
        self.__is_playout_paused = False

    def pause_recording(self):
        """Pause recording (output to file)."""
        self.__is_recording_paused = True

    def resume_recording(self):
        """Resume recording (output to file)."""
        self.__is_recording_paused = False

    def __get_input_filename_callback(self):
        return self.__input_filename

    def __get_output_filename_callback(self):
        return self.__output_filename

    def __is_endless_playout_callback(self):
        return self.play_on_repeat

    def __is_playout_paused_callback(self):
        return self.__is_playout_paused

    def __is_recording_paused_callback(self):
        return self.__is_recording_paused

    def __playout_ended_callback(self, input_filename: str):
        self.trigger_handlers(GroupCallFileAction.PLAYOUT_ENDED, self, input_filename)
