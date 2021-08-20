import asyncio
import os
from typing import Optional

from pytgcalls import GroupCallFactory

# choose one of this
import telethon
import pyrogram

# EDIT VALUES!
API_HASH = None
API_ID = None
PEER_ID = '@tgcallschat'  # chat or channel where you want to get audio
PEER_ID2 = '@tgcallslib'  # chat or channel where you want to play audio
CLIENT_TYPE = GroupCallFactory.MTPROTO_CLIENT_TYPE.PYROGRAM
# for Telethon uncomment line below
# CLIENT_TYPE = pytgcalls.GroupCallFactory.MTPROTO_CLIENT_TYPE.TELETHON

# global variable to transfer audio data between voice chats
# it's not a good implementation, but its works and so easy to understand
LAST_RECORDED_DATA = None


def on_played_data(_, length: int) -> Optional[bytes]:
    return LAST_RECORDED_DATA


def on_recorded_data(_, data: bytes, length: int) -> None:
    global LAST_RECORDED_DATA
    LAST_RECORDED_DATA = data


async def main(client):
    # its for Pyrogram
    await client.start()
    while not client.is_connected:
        await asyncio.sleep(1)
    # for Telethon you can use this one:
    # client.start()

    group_call_factory = GroupCallFactory(client, CLIENT_TYPE)

    # handle input audio data from the first peer
    group_call_from = group_call_factory.get_raw_group_call(on_recorded_data=on_recorded_data)
    await group_call_from.start(PEER_ID)
    # transfer input audio from the first peer to the second using handlers
    group_call_to = group_call_factory.get_raw_group_call(on_played_data=on_played_data)
    await group_call_to.start(PEER_ID2)

    await pyrogram.idle()


if __name__ == '__main__':
    tele_client = telethon.TelegramClient(
        os.environ.get('SESSION_NAME', 'pytgcalls'),
        int(os.environ['API_ID']),
        os.environ['API_HASH']
    )
    pyro_client = pyrogram.Client(
        os.environ.get('SESSION_NAME', 'pytgcalls'),
        api_hash=os.environ.get('API_HASH', API_HASH),
        api_id=os.environ.get('API_ID', API_ID),
    )

    # set your client (Pyrogram or Telethon)
    main_client = pyro_client

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(main_client))
