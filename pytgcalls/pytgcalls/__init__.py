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


from pytgcalls.exceptions import PytgcallsError
from pytgcalls.group_call_factory import GroupCallFactory
from pytgcalls.implementation.group_call_file import GroupCallFileAction
from pytgcalls.implementation.group_call_base import GroupCallBaseAction


__all__ = [
    'GroupCallFactory',
    'GroupCallFileAction',
    'GroupCallBaseAction',
]
__version__ = '3.0.0.dev15'
__pdoc__ = {
    # files
    'utils': False,
    'dispatcher': False,
}
