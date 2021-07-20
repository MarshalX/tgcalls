import os
import asyncio

import pytgcalls

# choose one of this
import telethon
import pyrogram

# EDIT VALUES!
API_HASH = None
API_ID = None
CHAT_ID = '@tgcallschat'
INPUT_DEVICE_NAME = 'MacBook Air Microphone'
OUTPUT_DEVICE_NAME = 'MacBook Air Speakers'
CLIENT_TYPE = pytgcalls.GroupCallFactory.MTPROTO_CLIENT_TYPE.PYROGRAM
# for Telethon uncomment line below
# CLIENT_TYPE = pytgcalls.GroupCallFactory.MTPROTO_CLIENT_TYPE.TELETHON


async def main(client):
    # its for Pyrogram
    await client.start()
    while not client.is_connected:
        await asyncio.sleep(1)
    # for Telethon you can use this one:
    # client.start()

    group_call = pytgcalls.GroupCallFactory(client, CLIENT_TYPE)\
        .get_device_group_call(INPUT_DEVICE_NAME, OUTPUT_DEVICE_NAME)
    await group_call.start(CHAT_ID)

    # to get available device names
    group_call.print_available_playout_devices()
    group_call.print_available_recording_devices()

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
