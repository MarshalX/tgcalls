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
from enum import Enum
from typing import Callable, List, Union

import pyrogram
from pyrogram import raw
from pyrogram.errors import BadRequest
from pyrogram.handlers import RawUpdateHandler
from pyrogram.raw import functions, types
from pyrogram.raw.types import InputPeerChannel, InputPeerChat

import tgcalls
from .dispatcher_mixin import DispatcherMixin

logger = logging.getLogger(__name__)

uint_ssrc = lambda ssrc: ssrc if ssrc >= 0 else ssrc + 2 ** 32
int_ssrc = lambda ssrc: ssrc if ssrc < 2 ** 31 else ssrc - 2 ** 32


class GroupCallAction(Enum):
    NETWORK_STATUS_CHANGED = 0


class GroupCallDispatcherMixin(DispatcherMixin):

    def on_network_status_changed(self, func: callable):
        return self.add_handler(func, GroupCallAction.NETWORK_STATUS_CHANGED)


def parse_call_participant(participant_data):
    native_participant = tgcalls.GroupParticipantDescription()

    native_participant.audioSsrc = uint_ssrc(participant_data.source)
    native_participant.isRemoved = participant_data.left

    return native_participant


class GroupCallNative(GroupCallDispatcherMixin):
    SEND_ACTION_UPDATE_EACH = 0.45

    def __init__(
            self,
            client: pyrogram.Client,
            enable_logs_to_console: bool,
            path_to_log_file: str
    ):
        super().__init__(GroupCallAction)
        self.client = client

        self.__native_instance = None

        self.my_user_id = None
        self.group_call = None

        self.chat_peer = None
        self.full_chat = None

        self.my_ssrc = None

        self.enable_action = True
        self.enable_logs_to_console = enable_logs_to_console
        self.path_to_log_file = path_to_log_file

        self.is_connected = False

        self._update_to_handler = {
            types.UpdateGroupCallParticipants: self._process_group_call_participants_update,
            types.UpdateGroupCall: self._process_group_call_update,
        }

        self._handler_group = None
        self._update_handler = RawUpdateHandler(self._process_update)

    def __deinit_native_instance(self):
        tmp = self.__native_instance
        self.__native_instance = None
        del tmp
        logger.debug('Native instance destroyed.')

    def __setup_native_instance(self):
        logger.debug('Create a new native instance..')
        native_instance = tgcalls.NativeInstance()
        logger.debug('Native instance created.')

        return native_instance

    async def _process_group_call_participants_update(self, update):
        logger.debug('Group call participants update..')

        ssrcs_to_remove = []
        for participant in update.participants:
            ssrc = uint_ssrc(participant.source)

            if participant.left:
                ssrcs_to_remove.append(ssrc)
            elif participant.user_id == self.my_user_id and ssrc != self.my_ssrc:
                logger.debug('Reconnect. Not equal ssrc.')
                await self.reconnect()

        if ssrcs_to_remove:
            logger.debug(f'Remove ssrcs {ssrcs_to_remove}.')
            self.__native_instance and self.__native_instance.removeSsrcs(ssrcs_to_remove)

    async def _process_group_call_update(self, update):
        logger.debug('Group call update..')
        if update.call.params:
            await self.__set_join_response_payload(json.loads(update.call.params.data))

    async def _process_update(self, _, update, users, chats):
        if type(update) not in self._update_to_handler.keys() or not self.__native_instance:
            raise pyrogram.ContinuePropagation

        if not self.group_call or not update.call or update.call.id != self.group_call.id:
            raise pyrogram.ContinuePropagation
        self.group_call = update.call

        await self._update_to_handler[type(update)](update)

    async def check_group_call(self) -> bool:
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

    async def get_group_participants(self):
        return (await (self.client.send(functions.phone.GetGroupCall(
            call=self.full_chat.call
        )))).participants

    async def leave_current_group_call(self):
        if not self.full_chat.call or not self.my_ssrc:
            return

        response = await self.client.send(functions.phone.LeaveGroupCall(
            call=self.full_chat.call,
            source=int_ssrc(self.my_ssrc)
        ))
        await self.client.handle_updates(response)

    async def edit_group_call(self, volume: int = None, muted=False):
        user_id = await self.client.storage.get_peer_by_id(self.my_user_id)
        await self.edit_group_call_member(user_id, volume, muted)

    async def edit_group_call_member(self, user_id, volume: int = None, muted=False):
        # there is bug in telegram. can't accept volume = 100 :D

        response = await self.client.send(functions.phone.EditGroupCallMember(
            call=self.full_chat.call,
            user_id=user_id,
            muted=muted,
            volume=max(1, volume * 100) if volume is not None else None
        ))
        await self.client.handle_updates(response)

    async def get_group_call(self, group: Union[str, int, InputPeerChannel, InputPeerChat]):
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
        if self._handler_group:
            self.client.remove_handler(self._update_handler, self._handler_group)
            self._handler_group = None

    async def stop(self):
        await self.leave_current_group_call()

        self.my_ssrc = self.group_call = self.chat_peer = self.full_chat = None
        self.is_connected = False

        self.remove_update_handler()
        self.__deinit_native_instance()
        logger.debug('GroupCall stop.')

    async def start(self, group: Union[str, int], enable_action=True):
        if self.is_connected:
            await self.stop()

        await self.get_group_call(group)

        if self.group_call is None:
            raise RuntimeError('Chat without a voice chat')

        handler_group = await self.__set_and_get_handler_group()
        self.client.add_handler(self._update_handler, handler_group)
        self.__native_instance = self.__setup_native_instance()

        self.enable_action = enable_action
        self.my_user_id = await self.client.storage.user_id()

    async def reconnect(self):
        chat_peer = self.chat_peer
        enable_action = self.enable_action

        await self.stop()
        await self.start(chat_peer, enable_action)

    async def _start_group_call(
            self,
            use_file_audio_device: bool,
            get_input_filename_callback: Callable,
            get_output_filename_callback: Callable
    ):
        logger.debug('Start native group call..')
        # TODO move callbacks to __setup_native_instance
        self.__native_instance.startGroupCall(
            self.enable_logs_to_console,
            self.path_to_log_file,

            use_file_audio_device,

            self.__emit_join_payload_callback,
            self.__network_state_updated_callback,
            self.__participant_descriptions_required_callback,
            get_input_filename_callback,
            get_output_filename_callback
        )

    def set_is_mute(self, is_muted: bool):
        logger.debug(f'Set is muted. New value: {is_muted}.')
        self.__native_instance.setIsMuted(is_muted)

    def __set_volume(self, ssrc, volume):
        self.__native_instance.setVolume(ssrc, volume)

    async def set_my_volume(self, volume):
        # Required "Manage Voice Chats" admin permission

        volume = max(1, min(int(volume), 200))
        logger.debug(f'Set my value. New value: {volume}.')

        await self.edit_group_call(volume)
        self.__native_instance.setVolume(uint_ssrc(self.my_ssrc), volume / 100)

    def restart_playout(self):
        self.__native_instance.reinitAudioInputDevice()

    def restart_recording(self):
        self.__native_instance.reinitAudioOutputDevice()

    def __participant_descriptions_required_callback(self, ssrcs_list: List[int]):
        logger.debug('Participant descriptions required..')

        def _(future):
            filtered_participants = [p for p in future.result() if uint_ssrc(p.source) in ssrcs_list]
            participants = [parse_call_participant(p) for p in filtered_participants]
            self.__native_instance and self.__native_instance.addParticipants(participants)

            logger.debug(f'Add description of {len(participants)} participant(s).')

        call_participants = asyncio.ensure_future(self.get_group_participants(), loop=self.client.loop)
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

        self.trigger_handlers(GroupCallAction.NETWORK_STATUS_CHANGED, self, state)

        logger.debug(f'New network state is {self.is_connected}.')

    async def audio_levels_updated_callback(self):
        pass  # TODO

    def __start_status_worker(self):
        async def worker():
            logger.debug('Start status (call action) worker..')
            while self.is_connected:
                await self.send_speaking_group_call_action()
                await asyncio.sleep(self.SEND_ACTION_UPDATE_EACH)

        asyncio.ensure_future(worker(), loop=self.client.loop)

    async def send_speaking_group_call_action(self):
        await self.client.send(
            raw.functions.messages.SetTyping(
                peer=self.chat_peer,
                action=raw.types.SpeakingInGroupCallAction()
            )
        )

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

        participants = [parse_call_participant(p) for p in await self.get_group_participants()]

        # TODO video payload
        self.__native_instance and self.__native_instance.setJoinResponsePayload(payload, participants)
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
            response = await self.client.send(functions.phone.JoinGroupCall(
                call=self.group_call,
                params=types.DataJSON(data=json.dumps(params)),
                muted=True
            ))
            await self.client.handle_updates(response)
            logger.debug(f'Successfully connected to VC with ssrc={self.my_ssrc}.')

        asyncio.ensure_future(_(), loop=self.client.loop)
