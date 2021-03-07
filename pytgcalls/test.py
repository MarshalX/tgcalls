import asyncio
import hashlib
import os
from random import randint
from typing import Union

import pyrogram
from pyrogram import errors, filters
from pyrogram.handlers import RawUpdateHandler
from pyrogram.raw import functions, types

import pytgcalls
import tgcalls
from helpers import b2i, calc_fingerprint, check_g, generate_visualization, i2b


class DH:
    def __init__(self, dhc: types.messages.DhConfig):
        self.p = b2i(dhc.p)
        self.g = dhc.g
        self.resp = dhc

    def __repr__(self):
        return f'<DH p={self.p} g={self.g} resp={self.resp}>'


class Call:

    def __init__(self, client: pyrogram.Client):
        if not client.is_connected:
            raise RuntimeError('Client must be started first')

        self.client = client
        self.native_instance = None

        self.call = None
        self.call_access_hash = None

        self.peer = None
        self.call_peer = None

        self.state = None

        self.dhc = None
        self.a = None
        self.g_a = None
        self.g_a_hash = None
        self.b = None
        self.g_b = None
        self.g_b_hash = None
        self.auth_key = None
        self.key_fingerprint = None

        self.auth_key_visualization = None

        self.init_encrypted_handlers = []

        self._update_handler = RawUpdateHandler(self.process_update)
        self.client.add_handler(self._update_handler, -1)

    async def process_update(self, _, update, users, chats):
        if isinstance(update, types.UpdatePhoneCallSignalingData) and self.native_instance:
            print('receiveSignalingData')
            self.native_instance.receiveSignalingData([x for x in update.data])

        if not isinstance(update, types.UpdatePhoneCall):
            raise pyrogram.ContinuePropagation

        call = update.phone_call
        if not self.call or not call or call.id != self.call.id:
            raise pyrogram.ContinuePropagation
        self.call = call

        if hasattr(call, 'access_hash') and call.access_hash:
            self.call_access_hash = call.access_hash
            self.call_peer = types.InputPhoneCall(id=self.call_id, access_hash=self.call_access_hash)
            try:
                await self.received_call()
            except Exception as e:
                print(e)

        if isinstance(call, types.PhoneCallDiscarded):
            self.call_discarded()
            raise pyrogram.StopPropagation

    @property
    def auth_key_bytes(self) -> bytes:
        return i2b(self.auth_key) if self.auth_key is not None else b''

    @property
    def call_id(self) -> int:
        return self.call.id if self.call else 0

    @staticmethod
    def get_protocol() -> types.PhoneCallProtocol:
        return types.PhoneCallProtocol(
            min_layer=92,
            max_layer=92,
            udp_p2p=True,
            udp_reflector=True,
            library_versions=['3.0.0'],
        )

    async def get_dhc(self):
        self.dhc = DH(await self.client.send(functions.messages.GetDhConfig(version=0, random_length=256)))
        return self.dhc

    def check_g(self, g_x: int, p: int) -> None:
        try:
            check_g(g_x, p)
        except RuntimeError:
            self.call_discarded()
            raise

    def stop(self) -> None:
        async def _():
            try:
                self.client.remove_handler(self._update_handler, -1)
            except ValueError:
                pass

        asyncio.ensure_future(_())

    def update_state(self, val) -> None:
        self.state = val

    def call_ended(self) -> None:
        self.update_state('Ended')
        self.stop()

    def call_failed(self, error=None) -> None:
        print('Call', self.call_id, 'failed with error', error)
        self.update_state('FAILED')
        self.stop()

    def call_discarded(self):
        if isinstance(self.call.reason, types.PhoneCallDiscardReasonBusy):
            self.update_state('BUSY')
            self.stop()
        else:
            self.call_ended()

    async def received_call(self):
        r = await self.client.send(functions.phone.ReceivedCall(
            peer=types.InputPhoneCall(id=self.call_id, access_hash=self.call_access_hash)
        ))
        print(r)

    async def discard_call(self, reason=None):
        if not reason:
            reason = types.PhoneCallDiscardReasonDisconnect()
        try:
            r = await self.client.send(functions.phone.DiscardCall(
                peer=types.InputPhoneCall(id=self.call_id, access_hash=self.call_access_hash),
                duration=0,  # TODO
                connection_id=0,
                reason=reason
            ))
            print(self.call_id)
        except (errors.CallAlreadyDeclined, errors.CallAlreadyAccepted) as e:
            pass

        self.call_ended()

    def signalling_data_emitted_callback(self, data):
        async def _():
            await self.client.send(functions.phone.SendSignalingData(
                # peer=self.call_peer,
                peer=types.InputPhoneCall(id=self.call_id, access_hash=self.call_access_hash),
                data=bytes(data)
            ))

        asyncio.ensure_future(_(), loop=self.client.loop)

    async def _initiate_encrypted_call(self) -> None:
        await self.client.send(functions.help.GetConfig())

        self.update_state('ESTABLISHED')
        self.auth_key_visualization = generate_visualization(self.auth_key, self.g_a)

        for handler in self.init_encrypted_handlers:
            asyncio.iscoroutinefunction(handler) and asyncio.ensure_future(handler(self), loop=self.client.loop)

    def on_init_encrypted_call(self, func: callable) -> callable:
        self.init_encrypted_handlers.append(func)
        return func


class OutgoingCall(Call):
    is_outgoing = True

    def __init__(self, client, user_id: Union[int, str]):
        super().__init__(client)
        self.user_id = user_id

    async def request(self):
        self.update_state('REQUESTING')

        self.peer = await self.client.resolve_peer(self.user_id)

        await self.get_dhc()
        self.a = randint(2, self.dhc.p - 1)
        self.g_a = pow(self.dhc.g, self.a, self.dhc.p)
        self.g_a_hash = hashlib.sha256(i2b(self.g_a)).digest()

        self.call = (await self.client.send(functions.phone.RequestCall(
            user_id=self.peer,
            random_id=randint(0, 0x7fffffff - 1),
            g_a_hash=self.g_a_hash,
            protocol=self.get_protocol(),
        ))).phone_call

        self.update_state('WAITING')

    async def process_update(self, _, update, users, chats) -> None:
        await super().process_update(_, update, users, chats)

        if isinstance(self.call, types.PhoneCallAccepted) and not self.auth_key:
            await self.call_accepted()
            raise pyrogram.StopPropagation

        raise pyrogram.ContinuePropagation

    async def call_accepted(self) -> None:
        self.update_state('EXCHANGING_KEYS')

        await self.get_dhc()
        self.g_b = b2i(self.call.g_b)
        self.check_g(self.g_b, self.dhc.p)
        self.auth_key = pow(self.g_b, self.a, self.dhc.p)
        self.key_fingerprint = calc_fingerprint(self.auth_key_bytes)

        self.call = (await self.client.send(functions.phone.ConfirmCall(
            key_fingerprint=self.key_fingerprint,
            # peer=self.call_peer,
            peer=types.InputPhoneCall(id=self.call_id, access_hash=self.call_access_hash),
            g_a=i2b(self.g_a),
            protocol=self.get_protocol(),
        ))).phone_call

        await self._initiate_encrypted_call()


class IncomingCall(Call):
    is_outgoing = False

    def __init__(self, call: types.PhoneCallRequested, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_accepted_handlers = []
        self.update_state('WAITING_INCOMING')
        self.call = call
        self.call_access_hash = call.access_hash

    async def process_update(self, _, update, users, chats):
        await super().process_update(_, update, users, chats)
        if isinstance(self.call, types.PhoneCall) and not self.auth_key:
            await self.call_accepted()
            raise pyrogram.StopPropagation
        raise pyrogram.ContinuePropagation

    async def on_call_accepted(self, func: callable) -> callable:
        self.call_accepted_handlers.append(func)
        return func

    async def accept(self) -> bool:
        self.update_state('EXCHANGING_KEYS')

        if not self.call:
            self.call_failed()
            raise RuntimeError('call is not set')

        if isinstance(self.call, types.PhoneCallDiscarded):
            print('Call is already discarded')
            self.call_discarded()
            return False

        await self.get_dhc()
        self.b = randint(2, self.dhc.p - 1)
        self.g_b = pow(self.dhc.g, self.b, self.dhc.p)
        self.g_a_hash = self.call.g_a_hash

        try:
            self.call = (await self.client.send(functions.phone.AcceptCall(
                peer=types.InputPhoneCall(id=self.call_id, access_hash=self.call_access_hash),
                g_b=i2b(self.g_b),
                protocol=self.get_protocol()
            ))).phone_call
        except Exception as e:
            print(e)

            await self.discard_call()

            self.stop()
            self.call_discarded()
            return False

        return True

    async def call_accepted(self) -> None:
        if not self.call.g_a_or_b:
            print('g_a is null')
            self.call_failed()
            return

        if self.g_a_hash != hashlib.sha256(self.call.g_a_or_b).digest():
            print('g_a_hash doesn\'t match')
            self.call_failed()
            return

        self.g_a = b2i(self.call.g_a_or_b)
        self.check_g(self.g_a, self.dhc.p)
        self.auth_key = pow(self.g_a, self.b, self.dhc.p)
        self.key_fingerprint = calc_fingerprint(self.auth_key_bytes)

        if self.key_fingerprint != self.call.key_fingerprint:
            print('fingerprints don\'t match')
            self.call_failed()
            return

        await self._initiate_encrypted_call()


class Tgcalls:
    incoming_call_class = IncomingCall
    outgoing_call_class = OutgoingCall

    def __init__(self, client: pyrogram.Client, receive_calls=True):
        self.client = client
        self.incoming_call_handlers = []
        if receive_calls:
            client.add_handler(RawUpdateHandler(self.update_handler), -1)
        client.on_message()

    def get_incoming_call_class(self):
        return self.incoming_call_class

    def get_outgoing_call_class(self):
        return self.outgoing_call_class

    def on_incoming_call(self, func) -> callable:
        self.incoming_call_handlers.append(func)
        return func

    async def start_call(self, user_id: Union[str, int]):
        call = self.get_outgoing_call_class()(self.client, user_id)
        await call.request()
        return call

    def update_handler(self, _, update, users, chats):
        if isinstance(update, types.UpdatePhoneCall):
            call = update.phone_call
            if isinstance(call, types.PhoneCallRequested):
                async def _():
                    voip_call = self.get_incoming_call_class()(call, client=self.client)
                    for handler in self.incoming_call_handlers:
                        asyncio.iscoroutinefunction(handler) and asyncio.ensure_future(handler(voip_call),
                                                                                       loop=self.client.loop)

                asyncio.ensure_future(_(), loop=self.client.loop)
        raise pyrogram.ContinuePropagation


def rtc_servers(connections):
    return [tgcalls.RtcServer(
        c.ip, c.ipv6, c.port, c.username, c.password, c.turn, c.stun
    ) for c in connections]


async def start(client1, client2, make_out, make_inc):
    while not client1.is_connected or not client2.is_connected:
        await asyncio.sleep(1)

    log_path1 = '/Users/marshal/projects/tgcalls/python-binding/pytgcalls/tgcalls1.txt'
    log_path2 = '/Users/marshal/projects/tgcalls/python-binding/pytgcalls/tgcalls2.txt'

    out = Tgcalls(client1, receive_calls=False)
    out_call = await out.start_call('@webrtctest') if make_out else None

    inc = Tgcalls(client2) if make_inc else None

    if inc is not None:
        @inc.on_incoming_call
        async def process_inc_call(inc_call: IncomingCall):
            await inc_call.accept()

            @inc_call.on_init_encrypted_call
            async def process_init_inc_call(call: IncomingCall):
                print('Incoming call: ', call.auth_key_visualization)
                print(rtc_servers(call.call.connections))

                call.native_instance = tgcalls.NativeInstance()
                call.native_instance.setSignalingDataEmittedCallback(call.signalling_data_emitted_callback)
                call.native_instance.startCall(
                    rtc_servers(call.call.connections),
                    [x for x in call.auth_key_bytes],
                    call.is_outgoing,
                    log_path2
                )

                # await asyncio.sleep(10)
                # await call.received_call()
                await asyncio.sleep(60)
                await call.discard_call()

    if out_call is not None:
        @out_call.on_init_encrypted_call
        async def process_call(call: Call):
            print('Outgoing call: ', call.auth_key_visualization)
            print(rtc_servers(call.call.connections))

            out_call.native_instance = tgcalls.NativeInstance()
            out_call.native_instance.setSignalingDataEmittedCallback(out_call.signalling_data_emitted_callback)
            out_call.native_instance.startCall(
                rtc_servers(call.call.connections),
                [x for x in call.auth_key_bytes],
                out_call.is_outgoing,
                log_path1
            )

            # await asyncio.sleep(10)
            # await call.received_call()
            await asyncio.sleep(60)
            await call.discard_call()


import logging
logging.basicConfig(level=logging.DEBUG)

for name, logger in logging.root.manager.loggerDict.items():
    if name.startswith('pyrogram'):
        logger.disabled = True


async def main(client1, client2, make_out, make_inc):
    # await client1.start()
    await client2.start()

    while not client2.is_connected:
        await asyncio.sleep(1)

    @client2.on_message(filters.text
                       & filters.outgoing
                       & ~filters.edited
                       & filters.command("test", prefixes="/"))
    async def test(client, message):
        group_call = pytgcalls.GroupCall(client, output_filename='output.raw')
        await group_call.start(message.chat.id)

        @group_call.on_network_status_changed
        async def network_status_changed_handler(gc: pytgcalls.GroupCall, is_connected: bool):
            if is_connected:
                await gc.reconnect()

    '''
    
    chats = ['@MarshalCm', '@MarshalCh'] * 10
    chats = ['@MarshalCm']
    group_call = pytgcalls.GroupCall(client2, 'input.raw', 'output.raw', False, '')
    for chat in chats:
        await group_call.start(chat, False)
    #
        while not group_call.is_connected:
    #         print('Wait')
            await asyncio.sleep(1)
    #
        print('Connected')

        # print(await group_call.check_group_call())

        # await asyncio.sleep(10)
        # await group_call.reconnect()
        await asyncio.sleep(10000)

        # await group_call.stop()
        # await group_call.start(chat, False)

    '''

    # group_call.native_instance.setAudioInputDevice('VB-Cable')
    # group_call.native_instance.setAudioOutputDevice('default (Built-in Output)')

    # await asyncio.sleep(60)
    # group_call.native_instance.stopGroupCall()

    # await start(client1, client2, make_out, make_inc)

    await pyrogram.idle()


if __name__ == '__main__':
    tgcalls.ping()

    c1 = pyrogram.Client(
        os.environ.get('SESSION_NAME'),
        api_hash=os.environ.get('API_HASH'),
        api_id=os.environ.get('API_ID')
    )

    c2 = pyrogram.Client(
        os.environ.get('SESSION_NAME2'),
        api_hash=os.environ.get('API_HASH'),
        api_id=os.environ.get('API_ID')
    )

    make_out = False
    make_inc = True

    # c1, c2 = c2, c1

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(c1, c2, make_out, make_inc))
