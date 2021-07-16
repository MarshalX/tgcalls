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
from asyncio import BaseEventLoop
from typing import List

from pytgcalls.mtproto import MTProtoBridgeBase
from pytgcalls.mtproto.data import GroupCallParticipantWrapper


# TODO implement
class TelethonBridge(MTProtoBridgeBase):
    async def check_group_call(self) -> bool:
        pass

    async def get_group_call_participants(self) -> List['GroupCallParticipantWrapper']:
        pass

    async def leave_current_group_call(self):
        pass

    async def edit_group_call_member(self, peer, volume: int = None, muted=False):
        pass

    async def get_and_set_self_peer(self):
        pass

    async def get_and_set_group_call(self, group):
        pass

    def unregister_update_handlers(self):
        pass

    def register_update_handlers(self):
        pass

    async def resolve_and_set_join_as(self, join_as):
        pass

    async def send_speaking_group_call_action(self):
        pass

    async def join_group_call(self, invite_hash: str, params: dict, muted: bool):
        pass

    def get_event_loop(self) -> BaseEventLoop:
        pass
