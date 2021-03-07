import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class GroupCallAction(Enum):
    NETWORK_STATUS_CHANGED = 0


class Dispatcher:

    def __init__(self, available_actions):
        self.actions = available_actions
        self.__action_to_handlers = self.__build_handler_storage()

    def __build_handler_storage(self):
        logger.debug('Build storage of handlers for dispatcher.')
        return {action: [] for action in self.actions}

    def add_handler(self, callback, action) -> bool:
        logger.debug('Add handler..')
        if not asyncio.iscoroutinefunction(callback):
            raise RuntimeError('Sync callback does not supported')

        try:
            handlers = self.__action_to_handlers[action]
            if callback in handlers:
                logger.debug('Handler already exists.')
                return False

            handlers.append(callback)
        except KeyError:
            raise RuntimeError('Invalid action')

        logger.debug('Handler added.')
        return True

    def remove_handler(self, callback, action) -> bool:
        logger.debug('Remove handler..')
        try:
            handlers = self.__action_to_handlers[action]
            for i in range(len(handlers)):
                if handlers[i] == callback:
                    del handlers[i]
                    return True
        except KeyError:
            raise RuntimeError('Invalid action')

        return False

    def remove_all(self):
        self.__action_to_handlers = self.__build_handler_storage()

    def get_handlers(self, action):
        try:
            logger.debug(f'Get handlers of {action}')
            return self.__action_to_handlers[action]
        except KeyError:
            raise RuntimeError('Invalid action')

    def trigger_handlers(self, action, instance, *args, **kwargs):
        logger.debug(f'Trigger handlers of {action}')

        for handler in self.get_handlers(action):
            asyncio.ensure_future(handler(instance, *args, **kwargs), loop=instance.client.loop)
