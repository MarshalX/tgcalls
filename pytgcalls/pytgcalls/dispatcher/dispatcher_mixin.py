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

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from . import GroupCallNative

from .dispatcher import Dispatcher


class DispatcherMixin:
    def __init__(self, actions):
        self._dispatcher = Dispatcher(actions)

    def add_handler(self, callback: Callable, action: str) -> Callable:
        """Register new handler.

        Args:
            callback (`Callable`): Callback function.
            action (`str`): Action.

        Returns:
            `Callable`: original callback.
        """

        return self._dispatcher.add_handler(callback, action)

    def remove_handler(self, callback: Callable, action: str) -> bool:
        """Unregister the handler.

        Args:
            callback (`Callable`): Callback function.
            action (`str`): Action.

        Returns:
            `bool`: Return `True` if success.
        """

        return self._dispatcher.remove_handler(callback, action)

    def trigger_handlers(self, action: str, instance: 'GroupCallNative', *args, **kwargs):
        """Unregister the handler.

        Args:
            action (`str`): Action.
            instance (`GroupCallNative`): Instance of GroupCallBase.
            *args (`list`, optional): Arbitrary callback arguments.
            **kwargs (`dict`, optional): Arbitrary callback arguments.
        """

        self._dispatcher.trigger_handlers(action, instance, *args, **kwargs)
