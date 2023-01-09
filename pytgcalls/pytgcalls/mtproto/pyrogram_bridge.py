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
from typing import Callable

from pyrogram.errors import (
    BadRequest as PyrogramBadRequest,
    GroupcallSsrcDuplicateMuch as PyrogramGroupcallSsrcDuplicateMuch,
)
from pyrogram.handlers import RawUpdateHandler
from pyrogram.raw import functions, types
from pyrogram.raw.types import (
    GroupCallDiscarded as PyrogramGroupCallDiscarded,
    InputPeerChannel,
    InputPeerChat,
    UpdateGroupCallConnection,
)
from pyrogram.utils import get_peer_id

from pytgcalls import PytgcallsError
from pytgcalls.mtproto.data import GroupCallDiscardedWrapper, GroupCallWrapper, GroupCallParticipantWrapper
from pytgcalls.mtproto.data.update import UpdateGroupCallWrapper, UpdateGroupCallParticipantsWrapper
from pytgcalls.mtproto.exceptions import BadRequest, GroupcallSsrcDuplicateMuch
from pytgcalls.utils import int_ssrc

from pyrogram import Client, ContinuePropagation

from pytgcalls.mtproto import MTProtoBridgeBase


class PyrogramBridge(MTProtoBridgeBase):
    def __init__(self, client: Client):
        super().__init__(client)

        # compatibility with pyro > 2.0
        if getattr(client, 'send', None) is None:
            setattr(client, 'send', getattr(client, 'invoke'))

        self._update_to_handler = {
            types.UpdateGroupCallParticipants: self._process_group_call_participants_update,
            types.UpdateGroupCall: self._process_group_call_update,
        }

        self._handler_group = None
        self._update_handler = RawUpdateHandler(self._process_update)

    async def _process_update(self, _, update, users, chats):
        if type(update) not in self._update_to_handler.keys():
            raise ContinuePropagation

        if not self.group_call or not update.call or update.call.id != self.group_call.id:
            raise ContinuePropagation
        self.group_call = update.call

        await self._update_to_handler[type(update)](update)

    async def _process_group_call_participants_update(self, update):
        participants = [GroupCallParticipantWrapper.create(p) for p in update.participants]
        wrapped_update = UpdateGroupCallParticipantsWrapper(participants)

        await self.group_call_participants_update_callback(wrapped_update)

    async def _process_group_call_update(self, update):
        if not isinstance(update.call, PyrogramGroupCallDiscarded):
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
            in_group_call = await (
                self.client.send(functions.phone.CheckGroupCall(call=self.group_call, source=int_ssrc(self.my_ssrc)))
            )
        except PyrogramBadRequest as e:
            # compatibility with pyro > 2.0
            if getattr(e, 'x', None) is None:
                setattr(e, 'x', getattr(e, 'value'))

            if e.x != '[400 GROUPCALL_JOIN_MISSING]':
                raise BadRequest(e.x)

            in_group_call = False

        return in_group_call

    async def leave_current_group_call(self):
        if not self.full_chat or not self.full_chat.call or not self.my_ssrc:
            return

        response = await self.client.send(
            functions.phone.LeaveGroupCall(call=self.full_chat.call, source=int_ssrc(self.my_ssrc))
        )
        await self.handle_updates(response)

    async def edit_group_call_member(
        self, peer, volume: int = None, muted=False, video_stopped=True, video_paused=False
    ):
        response = await self.client.send(
            functions.phone.EditGroupCallParticipant(
                call=self.full_chat.call,
                participant=peer,
                muted=muted,
                volume=volume,
                video_stopped=video_stopped,
                video_paused=video_paused,
            )
        )
        await self.handle_updates(response)

    async def get_and_set_self_peer(self):
        self.my_peer = await self.client.resolve_peer(await self.client.storage.user_id())

        return self.my_peer

    async def get_and_set_group_call(self, group):
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
            self.full_chat = (
                await (self.client.send(functions.channels.GetFullChannel(channel=self.chat_peer)))
            ).full_chat
        elif isinstance(self.chat_peer, InputPeerChat):
            self.full_chat = (
                await (self.client.send(functions.messages.GetFullChat(chat_id=self.chat_peer.chat_id)))
            ).full_chat

        if self.full_chat is None:
            raise PytgcallsError(f'Can\'t get full chat by {group}')

        self.group_call = self.full_chat.call

        return self.group_call

    def unregister_update_handlers(self):
        if self._handler_group:
            self.client.remove_handler(self._update_handler, self._handler_group)
            self._handler_group = None

    def register_update_handlers(self):
        if self.group_call.id > 0:
            self._handler_group = -self.group_call.id
        self._handler_group = self.group_call.id

        self.client.add_handler(self._update_handler, self._handler_group)

    async def resolve_and_set_join_as(self, join_as):
        my_peer = await self.get_and_set_self_peer()

        if join_as is None:
            self.join_as = self.full_chat.groupcall_default_join_as
            if self.join_as:
                # convert Peer to InputPeer
                self.join_as = await self.client.resolve_peer(get_peer_id(self.join_as))
            else:
                self.join_as = my_peer
        elif isinstance(join_as, str) or isinstance(join_as, int):
            self.join_as = await self.client.resolve_peer(join_as)
        else:
            self.join_as = join_as

    async def send_speaking_group_call_action(self):
        await self.client.send(
            functions.messages.SetTyping(peer=self.chat_peer, action=types.SpeakingInGroupCallAction())
        )

    async def join_group_call(
        self, invite_hash: str, params: str, muted: bool, video_stopped: bool, pre_update_processing: Callable
    ):
        try:
            response = await self.client.send(
                functions.phone.JoinGroupCall(
                    call=self.group_call,
                    join_as=self.join_as,
                    invite_hash=invite_hash,
                    params=types.DataJSON(data=params),
                    muted=muted,
                    video_stopped=video_stopped,
                )
            )

            pre_update_processing()

            # it is here cuz we need to associate params for connection with group call
            for update in response.updates:
                if isinstance(update, UpdateGroupCallConnection):
                    await self._process_group_call_connection(update)

            await self.handle_updates(response)
        except PyrogramGroupcallSsrcDuplicateMuch as e:
            # compatibility with pyro > 2.0
            if getattr(e, 'x', None) is None:
                setattr(e, 'x', getattr(e, 'value'))

            raise GroupcallSsrcDuplicateMuch(e.x)

    async def handle_updates(self, updates):
        await self.client.handle_updates(updates)
