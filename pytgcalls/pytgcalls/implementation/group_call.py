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
from abc import ABC
from typing import Callable, Optional

import tgcalls

from pytgcalls.dispatcher import Action, DispatcherMixin
from pytgcalls.exceptions import GroupCallNotFoundError, NotConnectedError
from pytgcalls.implementation import GroupCallNative
from pytgcalls.mtproto.data import GroupCallDiscardedWrapper
from pytgcalls.mtproto.data.update import UpdateGroupCallParticipantsWrapper, UpdateGroupCallWrapper
from pytgcalls.mtproto.exceptions import GroupcallSsrcDuplicateMuch
from pytgcalls.utils import uint_ssrc

logger = logging.getLogger(__name__)


class GroupCallAction:
    NETWORK_STATUS_CHANGED = Action()
    '''When a status of network will be changed.'''
    PARTICIPANT_LIST_UPDATED = Action()
    '''When a list of participant will be updated.'''


class GroupCallDispatcherMixin(DispatcherMixin):
    def on_network_status_changed(self, func: Callable) -> Callable:
        """When a status of network will be changed.

        Args:
            func (`Callable`): A functions that accept group_call and is_connected args.

        Returns:
            `Callable`: passed to args callback function.
        """

        return self.add_handler(func, GroupCallAction.NETWORK_STATUS_CHANGED)

    def on_participant_list_updated(self, func: Callable) -> Callable:
        """When a list of participant will be updated.

        Args:
            func (`Callable`): A functions that accept group_call and participants args.

        Note:
            The `participants` arg is a `list` of `GroupCallParticipantWrapper`.
            It contains only updated participants! It's not a list of all participants!

        Returns:
            `Callable`: passed to args callback function.
        """

        return self.add_handler(func, GroupCallAction.PARTICIPANT_LIST_UPDATED)


class GroupCall(ABC, GroupCallDispatcherMixin, GroupCallNative):
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
        GroupCallNative.__init__(
            self,
            self.__emit_join_payload_callback,
            self.__network_state_updated_callback,
            enable_logs_to_console,
            path_to_log_file,
            outgoing_audio_bitrate_kbit,
        )
        GroupCallDispatcherMixin.__init__(self, GroupCallAction)

        self.mtproto = mtproto_bridge
        self.mtproto.register_group_call_native_callback(
            self._group_call_participants_update_callback, self._group_call_update_callback
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

    async def _group_call_participants_update_callback(self, update: UpdateGroupCallParticipantsWrapper):
        logger.debug('Group call participants update...')
        logger.debug(update)

        self.trigger_handlers(GroupCallAction.PARTICIPANT_LIST_UPDATED, self, update.participants)

        for participant in update.participants:
            ssrc = uint_ssrc(participant.source)

            # maybe (if needed) set unmute status on server side after allowing to speak by admin
            # also mb there is need a some delay after getting update cuz server sometimes cant handle editing properly
            if participant.is_self and participant.can_self_unmute:
                if not self.__is_muted:
                    await self.edit_group_call(muted=False)

            if participant.peer == self.mtproto.join_as and ssrc != self.mtproto.my_ssrc:
                logger.debug(f'Not equal ssrc. Expected: {ssrc}. Actual: {self.mtproto.my_ssrc}.')
                await self.reconnect()

    async def _group_call_update_callback(self, update: UpdateGroupCallWrapper):
        logger.debug('Group call update...')
        logger.debug(update)

        if isinstance(update.call, GroupCallDiscardedWrapper):
            logger.debug('Group call discarded.')
            await self.stop()
        elif update.call.params:
            self.__set_join_response_payload(update.call.params.data)

    def __set_join_response_payload(self, payload):
        logger.debug('Set join response payload...')

        if self.__is_stop_requested:
            logger.debug('Set payload rejected by a stop request.')
            return

        self._set_connection_mode(tgcalls.GroupConnectionMode.GroupConnectionModeRtc)
        self._set_join_response_payload(payload)
        logger.debug('Join response payload was set.')

    def __emit_join_payload_callback(self, payload):
        logger.debug('Emit join payload callback...')

        if self.__is_stop_requested:
            logger.debug('Join group call rejected by a stop request.')
            return

        if self.mtproto.group_call is None:
            logger.debug('Group Call is None.')
            return

        async def _():
            try:

                def pre_update_processing():
                    logger.debug(f'Set my ssrc to {payload.audioSsrc}.')
                    self.mtproto.set_my_ssrc(payload.audioSsrc)

                await self.mtproto.join_group_call(
                    self.invite_hash, payload.json, muted=True, pre_update_processing=pre_update_processing
                )

                if self.__emit_join_payload_event:
                    self.__emit_join_payload_event.set()

                logger.debug(
                    f'Successfully connected to VC with '
                    f'ssrc={self.mtproto.my_ssrc} '
                    f'as {type(self.mtproto.join_as).__name__}.'
                )
            except GroupcallSsrcDuplicateMuch:
                logger.debug('Duplicate SSRC.')
                await self.reconnect()

        asyncio.ensure_future(_(), loop=self.mtproto.get_event_loop())

    def __network_state_updated_callback(self, state: bool):
        logger.debug('Network state updated...')

        if self.is_connected == state:
            logger.debug('Network state is same. Do nothing.')
            return

        self.is_connected = state
        if self.is_connected:
            asyncio.ensure_future(self.set_is_mute(False), loop=self.mtproto.get_event_loop())
            if self.enable_action:
                self.__start_status_worker()

        self.trigger_handlers(GroupCallAction.NETWORK_STATUS_CHANGED, self, state)

        logger.debug(f'New network state is {self.is_connected}.')

    def __start_status_worker(self):
        async def worker():
            logger.debug('Start status (call action) worker...')
            while self.is_connected:
                await self.mtproto.send_speaking_group_call_action()
                await asyncio.sleep(self.SEND_ACTION_UPDATE_EACH)

        asyncio.ensure_future(worker(), loop=self.mtproto.get_event_loop())

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

        group_call = await self.mtproto.get_and_set_group_call(group)
        if group_call is None:
            raise GroupCallNotFoundError('Chat without a voice chat')

        # mb move in other place. save plain join_as arg and use it in JoinGroupCall
        # but for now it works  as optimization of requests
        # we resolve join_as only when try to connect
        # it doesnt call resolve on reconnect
        await self.mtproto.resolve_and_set_join_as(join_as)

        self.invite_hash = invite_hash

        self.mtproto.re_register_update_handlers()

        # when trying to connect to another chat or with another join_as
        if self.is_group_call_native_created():
            await self.reconnect()
        # the first start
        else:
            self._setup_and_start_group_call()

    async def stop(self):
        """Properly stop tgcalls, remove MTProto handler, leave from server side."""
        if not self.is_group_call_native_created():
            logger.debug('Group call is not started, so there\'s nothing to stop.')
            return

        self.__is_stop_requested = True
        logger.debug('Stop requested.')

        self.mtproto.unregister_update_handlers()
        # to bypass recreating of outgoing audio channel
        self._set_is_mute(True)
        self._set_connection_mode(tgcalls.GroupConnectionMode.GroupConnectionModeNone)

        on_disconnect_event = asyncio.Event()

        async def post_disconnect():
            await self.leave_current_group_call()
            self.mtproto.reset()
            self.__is_stop_requested = False

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

            obj.remove_handler(on_disconnect, GroupCallAction.NETWORK_STATUS_CHANGED)
            on_disconnect_event.set()

        if self.is_connected:
            self.add_handler(on_disconnect, GroupCallAction.NETWORK_STATUS_CHANGED)
            await asyncio.wait_for(on_disconnect_event.wait(), timeout=self.__ASYNCIO_TIMEOUT)
        else:
            await post_disconnect()

        logger.debug('GroupCall stopped properly.')

    async def reconnect(self):
        """Connect to voice chat using the same native instance."""
        logger.debug('Reconnecting...')
        if not self.mtproto.group_call:
            raise NotConnectedError("You don't connected to voice chat.")

        self._set_connection_mode(tgcalls.GroupConnectionMode.GroupConnectionModeNone)
        self._emit_join_payload(self.__emit_join_payload_callback)

        # during the .stop we stop audio device module. Need to restart
        self.restart_recording()
        self.restart_playout()

        # cuz native instance doesnt block python
        self.__emit_join_payload_event = asyncio.Event()
        await asyncio.wait_for(self.__emit_join_payload_event.wait(), timeout=self.__ASYNCIO_TIMEOUT)

    async def leave_current_group_call(self):
        """Leave group call from server side (MTProto part)."""
        logger.debug('Try to leave the current group call...')
        try:
            await self.mtproto.leave_current_group_call()
        except Exception as e:
            logger.warning("Couldn't leave the group call. But no worries, you'll get removed from it in seconds.")
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

        await self.edit_group_call_member(self.mtproto.join_as, volume, muted)

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
        await self.mtproto.edit_group_call_member(peer, volume, muted)

    async def set_is_mute(self, is_muted: bool):
        """Set is mute.

        Args:
            is_muted (`bool`): Is muted.
        """

        self.__is_muted = is_muted
        self._set_is_mute(is_muted)

        logger.debug(f'Set is muted on server side. New value: {is_muted}.')
        await self.edit_group_call(muted=is_muted)

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
        self._set_volume(uint_ssrc(self.mtproto.my_ssrc), volume / 100)

    # shortcuts for easy access in callbacks of events

    @property
    def client(self):
        return self.mtproto.client

    @property
    def full_chat(self):
        return self.mtproto.full_chat

    @property
    def chat_peer(self):
        return self.mtproto.chat_peer

    @property
    def group_call(self):
        return self.mtproto.group_call

    @property
    def my_ssrc(self):
        return self.mtproto.my_ssrc

    @property
    def my_peer(self):
        return self.mtproto.my_peer

    @property
    def join_as(self):
        return self.mtproto.join_as
