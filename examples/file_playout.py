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
INPUT_FILENAME = 'input.raw'
OUTPUT_FILENAME = 'output.raw'
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

    # you can pass init filenames in the constructor
    group_call = pytgcalls.GroupCallFactory(client, CLIENT_TYPE)\
        .get_file_group_call(INPUT_FILENAME, OUTPUT_FILENAME)
    await group_call.start(CHAT_ID)

    # to change audio file you can do this:
    # group_call.input_filename = 'input2.raw'

    # to change output file:
    # group_call.output_filename = 'output2.raw'

    # to restart play from start:
    # group_call.restart_playout()

    # to stop play:
    # group_call.stop_playout()

    # same with output (recording)
    # .restart_recording, .stop_output

    # to mute yourself:
    # group_call.set_is_mute(True)

    # to leave a VC
    # group_call.stop()

    # to rejoin
    # group_call.reconnect()

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
