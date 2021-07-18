import os
import asyncio

import pytgcalls
import pyrogram

# EDIT VALUES!
API_HASH = None
API_ID = None
CHAT_ID = '@tgcallschat'
INPUT_DEVICE_NAME = 'MacBook Air Microphone'
OUTPUT_DEVICE_NAME = 'MacBook Air Speakers'


async def main(client):
    await client.start()
    while not client.is_connected:
        await asyncio.sleep(1)

    group_call = pytgcalls.GroupCallFactory(client).get_device_group_call(INPUT_DEVICE_NAME, OUTPUT_DEVICE_NAME)
    await group_call.start(CHAT_ID)

    # to get available device names
    group_call.print_available_playout_devices()
    group_call.print_available_recording_devices()

    await pyrogram.idle()


if __name__ == '__main__':
    pyro_client = pyrogram.Client(
        os.environ.get('SESSION_NAME', 'pytgcalls'),
        api_hash=os.environ.get('API_HASH', API_HASH),
        api_id=os.environ.get('API_ID', API_ID)
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(pyro_client))
