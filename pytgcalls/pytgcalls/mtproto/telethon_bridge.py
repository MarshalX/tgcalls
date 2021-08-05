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

from asyncio import AbstractEventLoop

from telethon.errors import (
    BadRequestError as TelethonBadRequestError,
    GroupcallJoinMissingError as TelethonGroupcallJoinMissingError,
    GroupcallSsrcDuplicateMuchError as TelethonGroupcallSsrcDuplicateMuchError,
)
from telethon.events import Raw, StopPropagation
from telethon.tl import functions
from telethon.tl.types import (
    DataJSON,
    GroupCallDiscarded as TelethonGroupCallDiscarded,
    SpeakingInGroupCallAction,
    UpdateGroupCall,
    UpdateGroupCallConnection,
    UpdateGroupCallParticipants,
    InputPeerChat,
    InputPeerChannel,
)

from pytgcalls.mtproto import MTProtoBridgeBase
from pytgcalls.mtproto.data import GroupCallDiscardedWrapper, GroupCallParticipantWrapper, GroupCallWrapper
from pytgcalls.mtproto.data.update import UpdateGroupCallParticipantsWrapper, UpdateGroupCallWrapper
from pytgcalls.mtproto.exceptions import BadRequest, GroupcallSsrcDuplicateMuch
from pytgcalls.utils import int_ssrc


class TelethonBridge(MTProtoBridgeBase):
    def __init__(self, client):
        super().__init__(client)

        self._loop = client.loop

        self._update_to_handler = {
            UpdateGroupCallParticipants: self._process_group_call_participants_update,
            UpdateGroupCall: self._process_group_call_update,
        }

    async def _process_update(self, update):
        if type(update) not in self._update_to_handler.keys():
            return

        if not self.group_call or not update.call or update.call.id != self.group_call.id:
            return
        self.group_call = update.call

        await self._update_to_handler[type(update)](update)
        raise StopPropagation

    async def _process_group_call_participants_update(self, update):
        participants = [
            GroupCallParticipantWrapper(
                p.source,
                p.left,
                p.peer,
                p.muted,
                p.can_self_unmute,
                p.is_self,
            )
            for p in update.participants
        ]
        wrapped_update = UpdateGroupCallParticipantsWrapper(participants)

        await self.group_call_participants_update_callback(wrapped_update)

    async def _process_group_call_update(self, update):
        if not isinstance(update.call, TelethonGroupCallDiscarded):
            return

        call = GroupCallDiscardedWrapper()  # no info needed
        wrapped_update = UpdateGroupCallWrapper(update.chat_id, call)

        await self.group_call_update_callback(wrapped_update)

    async def _process_group_call_connection(self, update):
        # TODO update to new layer when pyrogram will release new stable version on pypi
        call = GroupCallWrapper('placeholder', update.params)
        wrapped_update = UpdateGroupCallWrapper('placeholder', call)

        await self.group_call_update_callback(wrapped_update)

    async def check_group_call(self) -> bool:
        if not self.group_call or not self.my_ssrc:
            return False

        try:
            ssrcs_in_group_call = await (
                self.client(
                    functions.phone.CheckGroupCallRequest(call=self.group_call, sources=[int_ssrc(self.my_ssrc)])
                )
            )
        except TelethonBadRequestError as e:
            if isinstance(e, TelethonGroupcallJoinMissingError):
                return False
            else:
                raise BadRequest(e)

        return int_ssrc(self.my_ssrc) in ssrcs_in_group_call

    async def leave_current_group_call(self):
        if not self.full_chat or not self.full_chat.call or not self.my_ssrc:
            return

        response = await self.client(
            functions.phone.LeaveGroupCallRequest(call=self.full_chat.call, source=int_ssrc(self.my_ssrc))
        )

        self.client._handle_update(response)

    async def edit_group_call_member(self, peer, volume: int = None, muted=False):
        response = await self.client(
            functions.phone.EditGroupCallParticipantRequest(
                call=self.full_chat.call,
                participant=peer,
                muted=muted,
                volume=volume,
            )
        )

        self.client._handle_update(response)

    async def get_and_set_self_peer(self):
        self.my_peer = await self.client.get_me(input_peer=True)

        return self.my_peer

    async def get_and_set_group_call(self, group):
        self.chat_peer = group

        if type(group) not in [InputPeerChannel, InputPeerChat]:
            self.chat_peer = await self.client.get_input_entity(group)

        if isinstance(self.chat_peer, InputPeerChannel):
            self.full_chat = (await self.client(functions.channels.GetFullChannelRequest(group))).full_chat
        elif isinstance(self.chat_peer, InputPeerChat):
            self.full_chat = (await self.client(functions.messages.GetFullChatRequest(group))).full_chat

        if self.full_chat is None:
            raise RuntimeError(f'Can\'t get full chat by {group}')

        self.group_call = self.full_chat.call

        return self.group_call

    def unregister_update_handlers(self):
        self.client.remove_event_handler(self._process_update, Raw)

    def register_update_handlers(self):
        self.client.add_event_handler(self._process_update, Raw)

    async def resolve_and_set_join_as(self, join_as):
        if join_as is None:
            self.join_as = self.full_chat.groupcall_default_join_as
            if self.join_as is None:
                self.join_as = await self.get_and_set_self_peer()
        else:
            self.join_as = join_as

    async def send_speaking_group_call_action(self):
        await self.client(functions.messages.SetTypingRequest(peer=self.chat_peer, action=SpeakingInGroupCallAction()))

    async def join_group_call(self, invite_hash: str, params: str, muted: bool):
        try:
            response = await self.client(
                functions.phone.JoinGroupCallRequest(
                    call=self.group_call,
                    join_as=self.join_as,
                    invite_hash=invite_hash,
                    params=DataJSON(data=params),
                    muted=muted,
                )
            )

            # it is here cuz we need to associate params for connection with group call
            for update in response.updates:
                if isinstance(update, UpdateGroupCallConnection):
                    await self._process_group_call_connection(update)

            self.client._handle_update(response)
        except TelethonGroupcallSsrcDuplicateMuchError as e:
            raise GroupcallSsrcDuplicateMuch(e)

    def get_event_loop(self) -> AbstractEventLoop:
        return self._loop
