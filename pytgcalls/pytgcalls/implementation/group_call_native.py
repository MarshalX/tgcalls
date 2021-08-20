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

import logging
import warnings
from typing import Optional, List

import tgcalls
from pytgcalls.exceptions import CallBeforeStartError

logger = logging.getLogger(__name__)


def if_native_instance_created(func):
    def wrapper(self, *args, **kwargs):
        if self.is_group_call_native_created():
            return func(self, *args, **kwargs)
        else:
            raise CallBeforeStartError("You can't use this method before calling .start()")

    return wrapper


class GroupCallNative:
    def __init__(
        self,
        emit_join_payload_callback,
        network_state_updated_callback,
        enable_logs_to_console: bool,
        path_to_log_file: str,
        outgoing_audio_bitrate_kbit: int,
    ):
        """Create NativeInstance of tgcalls C++ part.

        Args:
            enable_logs_to_console (`bool`): Is enable logs to stderr from tgcalls.
            path_to_log_file (`str`, optional): Path to log file for logs of tgcalls.
        """

        # bypass None value
        if not path_to_log_file:
            path_to_log_file = ''

        logger.debug('Create a new native instance...')
        self.__native_instance = tgcalls.NativeInstance(enable_logs_to_console, path_to_log_file)

        self.__native_instance.setupGroupCall(
            emit_join_payload_callback,
            network_state_updated_callback,
            outgoing_audio_bitrate_kbit,
        )

        logger.debug('Native instance created.')

    def is_group_call_native_created(self):
        return self.__native_instance.isGroupCallNativeCreated()

    def _setup_and_start_group_call(self):
        raise NotImplementedError()

    @if_native_instance_created
    def _set_connection_mode(self, mode: tgcalls.GroupConnectionMode, keep_broadcast_if_was_enabled=False):
        logger.debug(f'Set native connection mode {mode}.')
        self.__native_instance.setConnectionMode(mode, keep_broadcast_if_was_enabled)

    @if_native_instance_created
    def _emit_join_payload(self, callback):
        logger.debug(f'Trigger native emit join payload.')
        self.__native_instance.emitJoinPayload(callback)

    def _start_native_group_call(self, *args):
        logger.debug('Start native group call...')
        self.__native_instance.startGroupCall(*args)

    @if_native_instance_created
    def _emit_join_payload(self, callback):
        logger.debug('Emit native join payload.')
        self.__native_instance.emitJoinPayload(callback)

    @if_native_instance_created
    def _set_join_response_payload(self, payload):
        logger.debug('Set native join response payload...')
        self.__native_instance.setJoinResponsePayload(payload)

    @if_native_instance_created
    def _set_is_mute(self, is_muted: bool):
        logger.debug(f'Set is muted on native instance side. New value: {is_muted}.')
        self.__native_instance.setIsMuted(is_muted)

    @if_native_instance_created
    def _set_volume(self, ssrc, volume):
        logger.debug(f'Set native volume for {ssrc} to {volume}.')
        self.__native_instance.setVolume(ssrc, volume)

    @if_native_instance_created
    def _stop_audio_device_module(self):
        logger.debug(f'Stop audio device module.')
        self.__native_instance.stopAudioDeviceModule()

    @if_native_instance_created
    def _start_audio_device_module(self):
        logger.debug(f'Start audio device module.')
        self.__native_instance.startAudioDeviceModule()

    @if_native_instance_created
    def get_playout_devices(self) -> List['tgcalls.AudioDevice']:
        """Get available playout audio devices in the system.

        Note:
            `tgcalls.AudioDevice` have 2 attributes: name, guid.
        """

        logger.debug('Get native playout devices.')
        return self.__native_instance.getPlayoutDevices()

    @if_native_instance_created
    def get_recording_devices(self) -> List['tgcalls.AudioDevice']:
        """Get available recording audio devices in the system.

        Note:
            `tgcalls.AudioDevice` have 2 attributes: name, guid.
        """

        logger.debug('Get native recording devices.')
        return self.__native_instance.getRecordingDevices()

    @if_native_instance_created
    def set_audio_input_device(self, name: Optional[str] = None):
        """Set audio input device.

        Note:
            If `name` is `None`, will use default system device.
            And this is works only at first device initialization time!

        Args:
            name (`str`): Name or GUID of device.
        """

        logger.debug(f'Set native audio input device to {name}.')
        self.__native_instance.setAudioInputDevice(name or '')

    @if_native_instance_created
    def set_audio_output_device(self, name: Optional[str] = None):
        """Set audio output device.

        Note:
            If `name` is `None`, will use default system device.
            And this is works only at first device initialization time!

        Args:
            name (`str`): Name or GUID of device.
        """

        logger.debug(f'Set native audio output device to {name}.')
        self.__native_instance.setAudioOutputDevice(name or '')

    @if_native_instance_created
    def restart_playout(self):
        """Start play current input file from start or just reload file audio device.

        Note:
            Device restart needed to apply new filename in tgcalls.
        """

        logger.debug(f'Restart native audio input device.')
        self.__native_instance.restartAudioInputDevice()

    @if_native_instance_created
    def restart_recording(self):
        """Start recording to output file from begin or just restart recording device.

        Note:
            Device restart needed to apply new filename in tgcalls.
        """

        logger.debug(f'Restart native audio output device.')
        self.__native_instance.restartAudioOutputDevice()

    # legacy below

    def print_available_playout_devices(self):
        """Print name and guid of available playout audio devices in system. Just helper method

        Note:
            You should use this method after calling .start()!
        """

        warnings.warn("It's a deprecated method. Use .get_recording_devices() instead", DeprecationWarning, 2)

        for device in self.get_playout_devices():
            print(f'Playout device \n name: {device.name} \n guid: {device.guid}')

    def print_available_recording_devices(self):
        """Print name and guid of available recording audio devices in system. Just helper method

        Note:
            You should use this method after calling .start()!
        """

        warnings.warn("It's a deprecated method. Use .get_playout_devices() instead", DeprecationWarning, 2)

        for device in self.get_recording_devices():
            print(f'Recording device \n name: {device.name} \n guid: {device.guid}')
