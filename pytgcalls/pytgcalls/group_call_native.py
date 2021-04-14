#  tgcalls - Python binding for tgcalls (c++ lib by Telegram)
#  pytgcalls - Library connecting python binding for tgcalls and Pyrogram
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
import json
import logging
from typing import List, Union, Coroutine, Optional

import pyrogram
from pyrogram import raw
from pyrogram.errors import BadRequest, GroupcallSsrcDuplicateMuch
from pyrogram.handlers import RawUpdateHandler
from pyrogram.raw import functions, types
from pyrogram.raw.base import InputPeer, Peer
from pyrogram.raw.types import InputPeerChannel, InputPeerChat, InputPeerUser, GroupCallDiscarded

import tgcalls
from .action import Action
from .dispatcher_mixin import DispatcherMixin

logger = logging.getLogger(__name__)

uint_ssrc = lambda ssrc: ssrc if ssrc >= 0 else ssrc + 2 ** 32
int_ssrc = lambda ssrc: ssrc if ssrc < 2 ** 31 else ssrc - 2 ** 32


class GroupCallNativeAction:
    NETWORK_STATUS_CHANGED = Action()
    '''When a status of network will be changed.'''


class GroupCallNativeDispatcherMixin(DispatcherMixin):

    def on_network_status_changed(self, func: Coroutine) -> Coroutine:
        """When a status of network will be changed.

        Args:
            func (`Coroutine`): A functions that accept group_call and is_connected args.

        Returns:
            `Coroutine`: passed to args callback function.
        """

        return self.add_handler(func, GroupCallNativeAction.NETWORK_STATUS_CHANGED)


def parse_call_participant(participant_data):
    native_participant = tgcalls.GroupParticipantDescription()

    native_participant.audioSsrc = uint_ssrc(participant_data.source)
    native_participant.isRemoved = participant_data.left

    return native_participant


class GroupCallNative(GroupCallNativeDispatcherMixin):
    SEND_ACTION_UPDATE_EACH = 0.45
    '''How often to send speaking action to chat'''

    def __init__(
            self,
            client: Union[pyrogram.Client, None],
            enable_logs_to_console: bool,
            path_to_log_file,
    ):
        super().__init__(GroupCallNativeAction)
        self.client = client
        '''Client of Pyrogram'''

        self.__native_instance = self.__create_and_setup_native_instance(
            enable_logs_to_console, path_to_log_file or 'group_call.log'
        )

        self.join_as = None
        '''How to present yourself in participants list'''
        self.invite_hash = None
        '''Hash from invite link to join as speaker'''
        self.my_peer = None
        '''Client user peer'''
        self.group_call = None
        '''Instance of Pyrogram's group call'''

        self.chat_peer = None
        '''Chat peer where bot is now'''
        self.full_chat = None
        '''Full chat information'''

        self.my_ssrc = None
        '''Client SSRC (Synchronization Source)'''

        self.enable_action = True
        '''Is enable sending of speaking action'''

        self.is_connected = False
        '''Is connected to voice chat via tgcalls'''

        self._update_to_handler = {
            types.UpdateGroupCallParticipants: self._process_group_call_participants_update,
            types.UpdateGroupCall: self._process_group_call_update,
        }

        self._handler_group = None
        self._update_handler = RawUpdateHandler(self._process_update)

    def __create_and_setup_native_instance(self, enable_logs_to_console: bool, path_to_log_file='group_call.log'):
        """Create NativeInstance of tgcalls C++ part.

        Args:
            enable_logs_to_console (`bool`): Is enable logs to stderr from tgcalls.
            path_to_log_file (`str`, optional): Path to log file for logs of tgcalls.
        """

        # bypass None value
        if not path_to_log_file:
            path_to_log_file = ''

        logger.debug('Create a new native instance..')
        native_instance = tgcalls.NativeInstance(enable_logs_to_console, path_to_log_file)

        native_instance.setupGroupCall(
            self.__emit_join_payload_callback,
            self.__network_state_updated_callback,
            self.__participant_descriptions_required_callback
        )

        logger.debug('Native instance created.')

        return native_instance

    async def _process_group_call_participants_update(self, update):
        logger.debug('Group call participants update..')

        ssrcs_to_remove = []
        for participant in update.participants:
            ssrc = uint_ssrc(participant.source)

            if participant.left:
                ssrcs_to_remove.append(ssrc)
            elif participant.peer == self.join_as and ssrc != self.my_ssrc:
                logger.debug('Reconnect. Not equal ssrc.')
                await self.reconnect()

        if ssrcs_to_remove:
            logger.debug(f'Remove ssrcs {ssrcs_to_remove}.')
            self.__native_instance.removeSsrcs(ssrcs_to_remove)

    async def _process_group_call_update(self, update):
        logger.debug('Group call update..')

        if isinstance(update.call, GroupCallDiscarded):
            logger.debug('Group call discarded.')
            await self.stop()
        elif update.call.params:
            await self.__set_join_response_payload(json.loads(update.call.params.data))

    async def _process_update(self, _, update, users, chats):
        if type(update) not in self._update_to_handler.keys() or not self.__native_instance:
            raise pyrogram.ContinuePropagation

        if not self.group_call or not update.call or update.call.id != self.group_call.id:
            raise pyrogram.ContinuePropagation
        self.group_call = update.call

        await self._update_to_handler[type(update)](update)

    async def check_group_call(self) -> bool:
        """Check if client is in a voice chat.

        Returns:
            `bool`: Is in voice chat by opinion of Telegram server.
        """

        if not self.group_call or not self.my_ssrc:
            return False

        try:
            in_group_call = (await (self.client.send(functions.phone.CheckGroupCall(
                call=self.group_call,
                source=int_ssrc(self.my_ssrc)
            ))))
        except BadRequest as e:
            if e.x != '[400 GROUPCALL_JOIN_MISSING]':
                raise e

            in_group_call = False

        return in_group_call

    async def get_group_call_participants(self):
        """Get group call participants of current chat."""
        return (await (self.client.send(functions.phone.GetGroupCall(
            call=self.full_chat.call
        )))).participants

    async def leave_current_group_call(self):
        """Leave group call from server side (MTProto part)."""
        logger.debug('Try to leave current group call.')

        if not self.full_chat.call or not self.my_ssrc:
            return

        response = await self.client.send(functions.phone.LeaveGroupCall(
            call=self.full_chat.call,
            source=int_ssrc(self.my_ssrc)
        ))
        await self.client.handle_updates(response)

        logger.debug('Completely leave current group call.')

    async def edit_group_call(self, volume: int = None, muted=False):
        """Edit own settings of group call.

        Note:
            There is bug where you can try to pass `volume=100`.

        Args:
            volume (`int`): Volume.
            muted (`bool`): Is muted.
        """

        await self.edit_group_call_member(self.join_as, volume, muted)

    async def edit_group_call_member(self, peer: Peer, volume: int = None, muted=False):
        """Edit setting of user in voice chat (required voice chat management permission).

        Note:
            There is bug where you can try to pass `volume=100`.

        Args:
            peer (`InputPeer`): Participant of voice chat.
            volume (`int`): Volume.
            muted (`bool`): Is muted.
        """

        response = await self.client.send(functions.phone.EditGroupCallParticipant(
            call=self.full_chat.call,
            participant=peer,
            muted=muted,
            volume=max(1, volume * 100) if volume is not None else None
        ))
        await self.client.handle_updates(response)

    async def get_group_call(self, group: Union[str, int, InputPeerChannel, InputPeerChat]):
        """Get group call input of chat.

        Args:
            group (`InputPeerChannel` | `InputPeerChat` | `str` | `int`): Chat ID in any form.

        Returns:
            `InputGroupCall`.
        """

        self.chat_peer = group
        if type(group) not in [InputPeerChannel, InputPeerChat]:
            self.chat_peer = await self.client.resolve_peer(group)

        if isinstance(self.chat_peer, InputPeerChannel):
            self.full_chat = (await (self.client.send(functions.channels.GetFullChannel(
                channel=self.chat_peer
            )))).full_chat
        elif isinstance(self.chat_peer, InputPeerChat):
            self.full_chat = (await (self.client.send(functions.messages.GetFullChat(
                chat_id=self.chat_peer.chat_id
            )))).full_chat

        if self.full_chat is None:
            raise RuntimeError(f'Can\'t get full chat by {group}')

        self.group_call = self.full_chat.call

        return self.group_call

    async def __set_and_get_handler_group(self) -> int:
        if self.group_call.id > 0:
            self._handler_group = -self.group_call.id
        self._handler_group = self.group_call.id

        return self._handler_group

    def remove_update_handler(self):
        """Remove pytgcalls handler in pyrogram client."""

        if self._handler_group:
            self.client.remove_handler(self._update_handler, self._handler_group)
            self._handler_group = None

    async def stop(self):
        """Properly stop tgcalls, remove pyrogram handler, leave from server side."""
        logger.debug('Stop requested.')

        if not self.is_connected:
            logger.error('Cant stop during connection.')

        self.remove_update_handler()
        self.__set_connection_mode(tgcalls.GroupConnectionMode.GroupConnectionModeNone)

        async def on_disconnect_handler(_, is_connected):
            if not is_connected:
                self.remove_handler(on_disconnect_handler, GroupCallNativeAction.NETWORK_STATUS_CHANGED)

                self.__native_instance.stopGroupCall()
                logger.debug('GroupCall properly stop.')

                await self.leave_current_group_call()

        self.add_handler(on_disconnect_handler, GroupCallNativeAction.NETWORK_STATUS_CHANGED)

    async def start(
            self,
            group: Union[str, int, InputPeerChannel, InputPeerChat],
            join_as: Optional[Union[str, int, InputPeerChannel, InputPeerChat, InputPeerUser]] = None,
            invite_hash: Optional[str] = None,
            enable_action=True
    ):
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

        self.my_peer = await self.client.resolve_peer(await self.client.storage.user_id())
        self.enable_action = enable_action

        await self.get_group_call(group)
        if self.group_call is None:
            raise RuntimeError('Chat without a voice chat')

        if join_as is None:
            self.join_as = self.my_peer
        elif isinstance(join_as, str) or isinstance(join_as, int):
            self.join_as = await self.client.resolve_peer(join_as)
        else:
            self.join_as = join_as

        self.invite_hash = invite_hash

        self.remove_update_handler()
        handler_group = await self.__set_and_get_handler_group()
        self.client.add_handler(self._update_handler, handler_group)

        # when trying to connect to another chat or with another join_as without calling .stop() before
        if self.__native_instance.isGroupCallStarted():
            await self.reconnect()
        # the first start or start after .stop() with the same NativeInstance
        else:
            self._setup_and_start_group_call()

    def _setup_and_start_group_call(self):
        raise NotImplementedError()

    async def reconnect(self):
        """Connect to voice chat using the same native instance."""

        self.__set_connection_mode(tgcalls.GroupConnectionMode.GroupConnectionModeNone)
        self.__native_instance.emitJoinPayload(self.__emit_join_payload_callback)

        await self.leave_current_group_call()

    def _start_native_group_call(self, *args):
        logger.debug('Start native group call..')
        self.__native_instance.startGroupCall(*args)

    def set_is_mute(self, is_muted: bool):
        """Set is mute.

        Args:
            is_muted (`bool`): Is muted.
        """

        logger.debug(f'Set is muted. New value: {is_muted}.')
        self.__native_instance.setIsMuted(is_muted)

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
        logger.debug(f'Set my value. New value: {volume}.')

        await self.edit_group_call(volume)
        self.__set_volume(uint_ssrc(self.my_ssrc), volume / 100)

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

    def __participant_descriptions_required_callback(self, ssrcs_list: List[int]):
        # TODO optimize
        # optimization:
        # - try to find ssrc in current (cached) list of participants
        # - add description if they exists
        # - if we cant find ssrc we need to update participants list by mtproto request
        # current impl. request actual part. list from server each method call

        logger.debug('Participant descriptions required..')

        def _(future):
            filtered_participants = [p for p in future.result() if uint_ssrc(p.source) in ssrcs_list]
            participants = [parse_call_participant(p) for p in filtered_participants]
            self.__native_instance.addParticipants(participants)

            logger.debug(f'Add description of {len(participants)} participant(s).')

        call_participants = asyncio.ensure_future(self.get_group_call_participants(), loop=self.client.loop)
        call_participants.add_done_callback(_)

    def __network_state_updated_callback(self, state: bool):
        logger.debug('Network state updated..')

        if self.is_connected == state:
            logger.debug('Network state is same. Do nothing.')
            return

        self.is_connected = state
        if self.is_connected:
            self.set_is_mute(False)
            if self.enable_action:
                self.__start_status_worker()

        self.trigger_handlers(GroupCallNativeAction.NETWORK_STATUS_CHANGED, self, state)

        logger.debug(f'New network state is {self.is_connected}.')

    def __start_status_worker(self):
        async def worker():
            logger.debug('Start status (call action) worker..')
            while self.is_connected:
                await self.send_speaking_group_call_action()
                await asyncio.sleep(self.SEND_ACTION_UPDATE_EACH)

        asyncio.ensure_future(worker(), loop=self.client.loop)

    async def send_speaking_group_call_action(self):
        """Send speaking action to current chat."""
        await self.client.send(
            raw.functions.messages.SetTyping(
                peer=self.chat_peer,
                action=raw.types.SpeakingInGroupCallAction()
            )
        )

    def __set_connection_mode(self, mode: tgcalls.GroupConnectionMode, keep_broadcast_if_was_enabled=False):
        logger.debug(f'Set connection mode {mode}')
        self.__native_instance.setConnectionMode(mode, keep_broadcast_if_was_enabled)

    async def __set_join_response_payload(self, params):
        logger.debug('Set join response payload..')
        params = params['transport']

        candidates = []
        for row_candidates in params.get('candidates', []):
            candidate = tgcalls.GroupJoinResponseCandidate()
            for key, value in row_candidates.items():
                setattr(candidate, key, value)

            candidates.append(candidate)

        fingerprints = []
        for row_fingerprint in params.get('fingerprints', []):
            fingerprint = tgcalls.GroupJoinPayloadFingerprint()
            for key, value in row_fingerprint.items():
                setattr(fingerprint, key, value)

            fingerprints.append(fingerprint)

        payload = tgcalls.GroupJoinResponsePayload()
        payload.ufrag = params.get('ufrag')
        payload.pwd = params.get('pwd')
        payload.fingerprints = fingerprints
        payload.candidates = candidates

        participants = [parse_call_participant(p) for p in await self.get_group_call_participants()]

        # TODO video payload

        self.__set_connection_mode(tgcalls.GroupConnectionMode.GroupConnectionModeRtc)
        self.__native_instance.setJoinResponsePayload(payload, participants)
        logger.debug('Join response payload was set.')

    def __emit_join_payload_callback(self, payload):
        logger.debug('Emit join payload..')
        if self.group_call is None:
            return

        self.my_ssrc = payload.ssrc

        fingerprints = [{
            'hash': f.hash,
            'setup': f.setup,
            'fingerprint': f.fingerprint
        } for f in payload.fingerprints]

        params = {
            'ufrag': payload.ufrag,
            'pwd': payload.pwd,
            'fingerprints': fingerprints,
            'ssrc': payload.ssrc
        }

        async def _():
            try:
                response = await self.client.send(functions.phone.JoinGroupCall(
                    call=self.group_call,
                    join_as=self.join_as,
                    invite_hash=self.invite_hash,
                    params=types.DataJSON(data=json.dumps(params)),
                    muted=True
                ))

                await self.client.handle_updates(response)
                logger.debug(f'Successfully connected to VC with ssrc={self.my_ssrc} as {type(self.join_as).__name__}.')
            except GroupcallSsrcDuplicateMuch:
                logger.debug('Reconnect. Duplicate SSRC')
                await self.reconnect()

        asyncio.ensure_future(_(), loop=self.client.loop)
