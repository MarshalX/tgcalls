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

from pytgcalls.group_call_native import GroupCallNative, GroupCallNativeAction, GroupCallNativeDispatcherMixin
from pytgcalls.action import Action
from pytgcalls.group_call import GroupCall, GroupCallAction, GroupCallDispatcherMixin
from pytgcalls.group_call_raw import GroupCallRaw
from pytgcalls.dispatcher import Dispatcher
from pytgcalls.dispatcher_mixin import DispatcherMixin

__all__ = ['GroupCallNative', 'GroupCall', 'GroupCallRaw', 'Dispatcher', 'DispatcherMixin', 'Action',
           'GroupCallNativeAction', 'GroupCallNativeDispatcherMixin', 'GroupCallAction', 'GroupCallDispatcherMixin']
__version__ = '0.0.19'
__pdoc__ = {
    'Action': False,
    'Dispatcher': False,
    'DispatcherMixin': False,
    'GroupCallDispatcherMixin': False,
    'GroupCallNativeAction': False,
    'GroupCallNativeDispatcherMixin': False,
    'GroupCallNative': False,
}
