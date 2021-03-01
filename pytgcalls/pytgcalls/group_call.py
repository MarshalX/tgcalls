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

import asyncio
import json
from typing import Union

import pyrogram
from pyrogram import raw
from pyrogram.handlers import RawUpdateHandler
from pyrogram.raw import functions, types

import tgcalls


class GroupCall:
    SEND_ACTION_UPDATE_EACH = 0.45

    def __init__(self, client: pyrogram.Client, input_filename: str = None, output_filename: str = None):
        self.client = client

        self.native_instance = tgcalls.NativeInstance()
        self.native_instance.setEmitJoinPayloadCallback(self.emit_join_payload_callback)

        self.me = None
        self.group_call = None

        self.chat_peer = None
        self.my_ssrc = None

        self.enable_action = True
        self.is_connected = False

        # feature of impl tgcalls
        self._input_filename = ''
        if input_filename:
            self._input_filename = input_filename
        self._output_filename = ''
        if output_filename:
            self._output_filename = output_filename

        self.update_to_handler = {
            types.UpdateGroupCallParticipants: self._process_group_call_participants_update,
            types.UpdateGroupCall: self._process_group_call_update,
        }

        self._update_handler = RawUpdateHandler(self.process_update)
        self.client.add_handler(self._update_handler, -1)

    async def _process_group_call_participants_update(self, update):
        ssrcs_to_remove = []
        for participant in update.participants:
            ssrcs = participant.source
            uint_ssrcs = ssrcs if ssrcs >= 0 else ssrcs + 2 ** 32
            # tg r u kidding me? sometimes send int instead of uint

            if participant.left:
                ssrcs_to_remove.append(uint_ssrcs)
            elif participant.user_id == self.me.id and uint_ssrcs != self.my_ssrc:
                # reconnect
                await self._start_group_call()

        if ssrcs_to_remove:
            self.native_instance.removeSsrcs(ssrcs_to_remove)

    async def _process_group_call_update(self, update):
        if update.call.params:
            await self.set_join_response_payload(json.loads(update.call.params.data))

    async def process_update(self, _, update, users, chats):
        if type(update) not in self.update_to_handler.keys():
            raise pyrogram.ContinuePropagation

        if not self.group_call or not update.call or update.call.id != self.group_call.id:
            raise pyrogram.ContinuePropagation
        self.group_call = update.call

        await self.update_to_handler[type(update)](update)

    async def _get_me(self):
        self.me = await self.client.get_me()

        return self.me

    async def get_group_call(self, group: Union[str, int]):
        self.chat_peer = await self.client.resolve_peer(group)
        self.group_call = (await (self.client.send(functions.channels.GetFullChannel(
            channel=self.chat_peer
        )))).full_chat.call

        return self.group_call

    async def stop(self):
        self.native_instance.stopGroupCall()

    async def start(self, group: Union[str, int], enable_action=True):
        self.enable_action = enable_action

        await self._get_me()
        await self.get_group_call(group)

        if self.group_call is None:
            raise RuntimeError('Chat without voice chat')

        await self._start_group_call()

    async def _start_group_call(self):
        self.native_instance.startGroupCall(
            True, self.network_state_updated_callback,
            self.__get_input_filename_callback, self.__get_output_filename_callback
        )

    def set_is_mute(self, is_muted: bool):
        self.native_instance.setIsMuted(is_muted)

    def stop_playout(self):
        self.input_filename = ''

    def stop_output(self):
        self.output_filename = ''

    def restart_playout(self):
        self.native_instance.reinitAudioInputDevice()

    def restart_recording(self):
        self.native_instance.reinitAudioOutputDevice()

    @property
    def input_filename(self):
        return self._input_filename

    @input_filename.setter
    def input_filename(self, filename):
        self._input_filename = filename
        self.restart_playout()

    @property
    def output_filename(self):
        return self._output_filename

    @output_filename.setter
    def output_filename(self, filename):
        self._output_filename = filename
        self.restart_recording()

    def __get_input_filename_callback(self):
        return self._input_filename

    def __get_output_filename_callback(self):
        return self._output_filename

    def network_state_updated_callback(self, state: bool):
        self.is_connected = state

        if self.is_connected:
            self.set_is_mute(False)
            if self.enable_action:
                self.start_status_worker()

    async def audio_levels_updated_callback(self):
        pass  # TODO

    def start_status_worker(self):
        async def worker():
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

    async def set_join_response_payload(self, params):
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

        self.native_instance.setJoinResponsePayload(payload)

    def emit_join_payload_callback(self, payload):
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

        asyncio.ensure_future(_(), loop=self.client.loop)
