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

import asyncio
import logging
from typing import Callable, Optional

import tgcalls

from pytgcalls.dispatcher import Action, DispatcherMixin
from pytgcalls.mtproto.data import GroupCallDiscardedWrapper
from pytgcalls.mtproto.data.update import UpdateGroupCallParticipantsWrapper, UpdateGroupCallWrapper
from pytgcalls.mtproto.exceptions import GroupcallSsrcDuplicateMuch
from pytgcalls.utils import uint_ssrc

logger = logging.getLogger(__name__)


class GroupCallNativeAction:
    NETWORK_STATUS_CHANGED = Action()
    '''When a status of network will be changed.'''


class GroupCallNativeDispatcherMixin(DispatcherMixin):
    def on_network_status_changed(self, func: Callable) -> Callable:
        """When a status of network will be changed.

        Args:
            func (`Callable`): A functions that accept group_call and is_connected args.

        Returns:
            `Callable`: passed to args callback function.
        """

        return self.add_handler(func, GroupCallNativeAction.NETWORK_STATUS_CHANGED)


class GroupCallNative(GroupCallNativeDispatcherMixin):
    SEND_ACTION_UPDATE_EACH = 0.45
    '''How often to send speaking action to chat'''

    __ASYNCIO_TIMEOUT = 10

    def __init__(
        self,
        mtproto_bridge,
        enable_logs_to_console: bool,
        path_to_log_file: str,
        outgoing_audio_bitrate_kbit: int,
    ):
        super().__init__(GroupCallNativeAction)

        self.mtproto_bridge = mtproto_bridge
        self.mtproto_bridge.register_group_call_native_callback(
            self._group_call_participants_update_callback, self._group_call_update_callback
        )

        self.__native_instance = self.__create_and_setup_native_instance(
            enable_logs_to_console, path_to_log_file, outgoing_audio_bitrate_kbit
        )

        self.invite_hash = None
        '''Hash from invite link to join as speaker'''

        self.enable_action = True
        '''Is enable sending of speaking action'''

        self.is_connected = False
        '''Is connected to voice chat via tgcalls'''

        self.__is_stop_requested = False
        self.__emit_join_payload_event = None

        self.__is_muted = True

    def __create_and_setup_native_instance(
        self, enable_logs_to_console: bool, path_to_log_file='group_call.log', outgoing_audio_bitrate_kbit=128
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
        native_instance = tgcalls.NativeInstance(enable_logs_to_console, path_to_log_file)

        native_instance.setupGroupCall(
            self.__emit_join_payload_callback,
            self.__network_state_updated_callback,
            outgoing_audio_bitrate_kbit,
        )

        logger.debug('Native instance created.')

        return native_instance

    async def _group_call_participants_update_callback(self, update: UpdateGroupCallParticipantsWrapper):
        logger.debug('Group call participants update...')
        logger.debug(update)

        for participant in update.participants:
            ssrc = uint_ssrc(participant.source)

            # maybe (if needed) set unmute status on server side after allowing to speak by admin
            # also mb there is need a some delay after getting update cuz server sometimes cant handle editing properly
            if participant.is_self and participant.can_self_unmute:
                if not self.__is_muted:
                    await self.edit_group_call(muted=False)

            if participant.peer == self.mtproto_bridge.join_as and ssrc != self.mtproto_bridge.my_ssrc:
                logger.debug(f'Not equal ssrc. Expected: {ssrc}. Actual: {self.mtproto_bridge.my_ssrc}.')
                await self.reconnect()

    async def _group_call_update_callback(self, update: UpdateGroupCallWrapper):
        logger.debug('Group call update...')
        logger.debug(update)

        if isinstance(update.call, GroupCallDiscardedWrapper):
            logger.debug('Group call discarded.')
            await self.stop()
        elif update.call.params:
            await self.__set_join_response_payload(update.call.params.data)

    async def check_group_call(self) -> bool:
        return await self.mtproto_bridge.check_group_call()

    async def leave_current_group_call(self):
        """Leave group call from server side (MTProto part)."""
        logger.debug('Try to leave the current group call...')
        try:
            await self.mtproto_bridge.leave_current_group_call()
        except Exception as e:
            logger.warning('Couldn\'t leave the group call. But no worries, you\'ll get removed from it in seconds.')
            logger.debug(e)
        else:
            logger.debug('Completely left the current group call.')

    async def edit_group_call(self, volume: int = None, muted=False):
        """Edit own settings of group call.

        Note:
            There is bug where you can try to pass `volume=100`.

        Args:
            volume (`int`): Volume.
            muted (`bool`): Is muted.
        """

        await self.edit_group_call_member(self.mtproto_bridge.join_as, volume, muted)

    async def edit_group_call_member(self, peer, volume: int = None, muted=False):
        """Edit setting of user in voice chat (required voice chat management permission).

        Note:
            There is bug where you can try to pass `volume=100`.

        Args:
            peer (`InputPeer`): Participant of voice chat.
            volume (`int`): Volume.
            muted (`bool`): Is muted.
        """

        volume = max(1, volume * 100) if volume is not None else None
        await self.mtproto_bridge.edit_group_call_member(peer, volume, muted)

    async def get_group_call(self, group):
        return await self.mtproto_bridge.get_and_set_group_call(group)

    def unregister_update_handlers(self):
        """Remove pytgcalls handler in MTProto client."""
        self.mtproto_bridge.unregister_update_handlers()

    def register_update_handlers(self):
        """Add pytgcalls handler in MTProto client."""
        self.mtproto_bridge.register_update_handlers()

    def re_register_update_handlers(self):
        """Delete and add pytgcalls handler in MTProto client."""
        self.unregister_update_handlers()
        self.register_update_handlers()

    async def stop(self):
        """Properly stop tgcalls, remove MTProto handler, leave from server side."""
        if not self.__native_instance.isGroupCallStarted():
            logger.debug('Group call is not started, so there\'s nothing to stop.')
            return

        self.__is_stop_requested = True
        logger.debug('Stop requested.')

        self.unregister_update_handlers()
        # to bypass recreating of outgoing audio channel
        self.__set_is_mute(True)
        self.__set_connection_mode(tgcalls.GroupConnectionMode.GroupConnectionModeNone)

        on_disconnect_event = asyncio.Event()

        async def post_disconnect():
            await self.leave_current_group_call()
            self.mtproto_bridge.reset()

        async def on_disconnect(obj, is_connected):
            if is_connected:
                return

            obj._stop_audio_device_module()

            # need for normal waiting of stopping audio devices
            # destroying of webrtc client during .stop not needed yet
            # because we a working in the same native instance
            # and can reuse tis client for another connections.
            # In any case now its possible to reset group call ptr
            # self.__native_instance.stopGroupCall()

            await post_disconnect()

            obj.remove_handler(on_disconnect, GroupCallNativeAction.NETWORK_STATUS_CHANGED)
            on_disconnect_event.set()

        if self.is_connected:
            self.add_handler(on_disconnect, GroupCallNativeAction.NETWORK_STATUS_CHANGED)
            await asyncio.wait_for(on_disconnect_event.wait(), timeout=self.__ASYNCIO_TIMEOUT)
        else:
            await post_disconnect()

        logger.debug('GroupCall stopped properly.')

    async def start(self, group, join_as=None, invite_hash: Optional[str] = None, enable_action=True):
        """Start voice chat (join and play/record from initial values).

        Note:
            Disconnect from current voice chat and connect to the new one.
            Multiple instances of `GroupCall` must be created for multiple voice chats at the same time.
            Join as by default is personal account.

        Args:
            group (`InputPeerChannel` | `InputPeerChat` | `str` | `int`): Chat ID in any form.
            join_as (`InputPeer` | `str` | `int`, optional): How to present yourself in participants list.
            invite_hash (`str`, optional): Hash from speaker invite link.
            enable_action (`bool`, optional): Is enables sending of speaking action.
        """
        self.__is_stop_requested = False
        self.enable_action = enable_action

        group_call = await self.get_group_call(group)
        if group_call is None:
            raise RuntimeError('Chat without a voice chat')

        # mb move in other place. save plain join_as arg and use it in JoinGroupCall
        # but for now it works  as optimization of requests
        # we resolve join_as only when try to connect
        # it doesnt call resolve on reconnect
        await self.mtproto_bridge.resolve_and_set_join_as(join_as)

        self.invite_hash = invite_hash

        self.re_register_update_handlers()

        # when trying to connect to another chat or with another join_as
        if self.__native_instance.isGroupCallStarted():
            await self.reconnect()
        # the first start
        else:
            self._setup_and_start_group_call()

    def _setup_and_start_group_call(self):
        raise NotImplementedError()

    async def reconnect(self):
        """Connect to voice chat using the same native instance."""
        logger.debug('Reconnecting...')

        self.__set_connection_mode(tgcalls.GroupConnectionMode.GroupConnectionModeNone)
        self.__native_instance.emitJoinPayload(self.__emit_join_payload_callback)

        # during the .stop we stop audio device module. Need to restart
        self.restart_recording()
        self.restart_playout()

        # cuz native instance doesnt block python
        self.__emit_join_payload_event = asyncio.Event()
        await asyncio.wait_for(self.__emit_join_payload_event.wait(), timeout=self.__ASYNCIO_TIMEOUT)

    def _start_native_group_call(self, *args):
        logger.debug('Start native group call...')
        self.__native_instance.startGroupCall(*args)

    def __set_is_mute(self, is_muted: bool):
        logger.debug(f'Set is muted on native instance side. New value: {is_muted}.')
        self.__native_instance.setIsMuted(is_muted)

    async def set_is_mute(self, is_muted: bool):
        """Set is mute.

        Args:
            is_muted (`bool`): Is muted.
        """

        self.__is_muted = is_muted
        self.__set_is_mute(is_muted)

        logger.debug(f'Set is muted on server side. New value: {is_muted}.')
        await self.edit_group_call(muted=is_muted)

    def __set_volume(self, ssrc, volume):
        self.__native_instance.setVolume(ssrc, volume)

    async def set_my_volume(self, volume):
        """Set volume for current client.

        Note:
            Volume value only can be in 1-200 range. There is auto normalization.

        Args:
            volume (`int` | `str` | `float`): Volume.
        """
        # Required "Manage Voice Chats" admin permission

        volume = max(1, min(int(volume), 200))
        logger.debug(f'Set volume to: {volume}.')

        await self.edit_group_call(volume)
        self.__set_volume(uint_ssrc(self.mtproto_bridge.my_ssrc), volume / 100)

    def print_available_playout_devices(self):
        """Print name and guid of available playout audio devices in system. Just helper method

        Note:
            You should use this method after calling .start()!
        """

        self.__native_instance.printAvailablePlayoutDevices()

    def print_available_recording_devices(self):
        """Print name and guid of available recording audio devices in system. Just helper method

        Note:
            You should use this method after calling .start()!
        """

        self.__native_instance.printAvailableRecordingDevices()

    def set_audio_input_device(self, name: Optional[str] = None):
        """Set audio input device.

        Note:
            If `name` is `None`, will use default system device.
            And this is works only at first device initialization time!

        Args:
            name (`str`): Name or GUID of device.
        """

        self.__native_instance.setAudioInputDevice(name or '')

    def set_audio_output_device(self, name: Optional[str] = None):
        """Set audio output device.

        Note:
            If `name` is `None`, will use default system device.
            And this is works only at first device initialization time!

        Args:
            name (`str`): Name or GUID of device.
        """

        self.__native_instance.setAudioOutputDevice(name or '')

    def _stop_audio_device_module(self):
        logger.debug(f'Stop audio device module.')
        self.__native_instance.stopAudioDeviceModule()

    def _start_audio_device_module(self):
        logger.debug(f'Start audio device module.')
        self.__native_instance.startAudioDeviceModule()

    def restart_playout(self):
        """Start play current input file from start or just reload file audio device.

        Note:
            Device restart needed to apply new filename in tgcalls.
        """

        self.__native_instance.restartAudioInputDevice()

    def restart_recording(self):
        """Start recording to output file from begin or just restart recording device.

        Note:
            Device restart needed to apply new filename in tgcalls.
        """

        self.__native_instance.restartAudioOutputDevice()

    def __network_state_updated_callback(self, state: bool):
        logger.debug('Network state updated...')

        if self.is_connected == state:
            logger.debug('Network state is same. Do nothing.')
            return

        self.is_connected = state
        if self.is_connected:
            asyncio.ensure_future(self.set_is_mute(False), loop=self.mtproto_bridge.get_event_loop())
            if self.enable_action:
                self.__start_status_worker()

        self.trigger_handlers(GroupCallNativeAction.NETWORK_STATUS_CHANGED, self, state)

        logger.debug(f'New network state is {self.is_connected}.')

    def __start_status_worker(self):
        async def worker():
            logger.debug('Start status (call action) worker...')
            while self.is_connected:
                await self.send_speaking_group_call_action()
                await asyncio.sleep(self.SEND_ACTION_UPDATE_EACH)

        asyncio.ensure_future(worker(), loop=self.mtproto_bridge.get_event_loop())

    async def send_speaking_group_call_action(self):
        """Send speaking action to current chat."""
        await self.mtproto_bridge.send_speaking_group_call_action()

    def __set_connection_mode(self, mode: tgcalls.GroupConnectionMode, keep_broadcast_if_was_enabled=False):
        logger.debug(f'Set connection mode {mode}.')
        self.__native_instance.setConnectionMode(mode, keep_broadcast_if_was_enabled)

    async def __set_join_response_payload(self, payload):
        logger.debug('Set join response payload...')

        if self.__is_stop_requested:
            logger.debug('Set payload rejected by a stop request.')
            return

        self.__set_connection_mode(tgcalls.GroupConnectionMode.GroupConnectionModeRtc)
        self.__native_instance.setJoinResponsePayload(payload)
        logger.debug('Join response payload was set.')

    def __emit_join_payload_callback(self, payload):
        logger.debug('Emit join payload...')

        if self.__is_stop_requested:
            logger.debug('Join group call rejected by a stop request.')
            return

        if self.mtproto_bridge.group_call is None:
            return

        async def _():
            try:
                await self.mtproto_bridge.join_group_call(self.invite_hash, payload.json, muted=True)

                # TODO move before handle updates from join GC
                self.mtproto_bridge.set_my_ssrc(payload.audioSsrc)
                if self.__emit_join_payload_event:
                    self.__emit_join_payload_event.set()

                logger.debug(
                    f'Successfully connected to VC with '
                    f'ssrc={self.mtproto_bridge.my_ssrc} '
                    f'as {type(self.mtproto_bridge.join_as).__name__}.'
                )
            except GroupcallSsrcDuplicateMuch:
                logger.debug('Duplicate SSRC.')
                await self.reconnect()

        asyncio.ensure_future(_(), loop=self.mtproto_bridge.get_event_loop())

    # backward compatibility below

    @property
    def client(self):
        return self.mtproto_bridge.client

    @property
    def full_chat(self):
        return self.mtproto_bridge.full_chat

    @property
    def chat_peer(self):
        return self.mtproto_bridge.chat_peer

    @property
    def group_call(self):
        return self.mtproto_bridge.group_call

    @property
    def my_ssrc(self):
        return self.mtproto_bridge.my_ssrc

    @property
    def my_peer(self):
        return self.mtproto_bridge.my_peer

    @property
    def join_as(self):
        return self.mtproto_bridge.join_as
