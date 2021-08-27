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
from typing import Callable, List

from typing import TYPE_CHECKING

from ..exceptions import PytgcallsError

if TYPE_CHECKING:
    from . import GroupCallNative

logger = logging.getLogger(__name__)


class Dispatcher:
    def __init__(self, available_actions: type):
        self.actions = available_actions
        self.__action_to_handlers = self.__build_handler_storage()

    def __build_handler_storage(self):
        logger.debug('Build storage of handlers for dispatcher.')
        return {action: [] for action in dir(self.actions) if not action.startswith('_')}

    def add_handler(self, callback: Callable, action: str) -> Callable:
        logger.debug(f'Add handler to {action} action...')
        if not asyncio.iscoroutinefunction(callback):
            raise PytgcallsError('Sync callback does not supported')

        try:
            handlers = self.__action_to_handlers[action]
            if callback in handlers:
                logger.debug('Handler is already set.')
                return callback

            handlers.append(callback)
        except KeyError:
            raise PytgcallsError('Invalid action')

        logger.debug('Handler added.')
        return callback

    def remove_handler(self, callback: Callable, action: str) -> bool:
        logger.debug(f'Remove handler of {action} action...')
        try:
            handlers = self.__action_to_handlers[action]
            for i in range(len(handlers)):
                if handlers[i] == callback:
                    del handlers[i]
                    return True
        except KeyError:
            raise PytgcallsError('Invalid action')

        return False

    def remove_all(self):
        self.__action_to_handlers = self.__build_handler_storage()

    def get_handlers(self, action: str) -> List[Callable]:
        try:
            logger.debug(f'Get {action} handlers...')
            return self.__action_to_handlers[action]
        except KeyError:
            raise PytgcallsError('Invalid action')

    def trigger_handlers(self, action: str, instance: 'GroupCallNative', *args, **kwargs):
        logger.debug(f'Trigger {action} handlers...')

        for handler in self.get_handlers(action):
            logger.debug(f'Trigger {handler.__name__}...')
            asyncio.ensure_future(handler(instance, *args, **kwargs), loop=instance.mtproto.get_event_loop())
