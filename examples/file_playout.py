import os
import asyncio

import pytgcalls
import pyrogram

# EDIT VALUES!
API_HASH = None
API_ID = None
CHAT_ID = '@tgcallschat'
INPUT_FILENAME = 'input.raw'
OUTPUT_FILENAME = 'output.raw'


async def main(client):
    await client.start()
    while not client.is_connected:
        await asyncio.sleep(1)

    # you can pass init filenames in the constructor
    group_call = pytgcalls.GroupCallFactory(client).get_file_group_call(INPUT_FILENAME, OUTPUT_FILENAME)
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
    pyro_client = pyrogram.Client(
        os.environ.get('SESSION_NAME', 'pytgcalls'),
        api_hash=os.environ.get('API_HASH', API_HASH),
        api_id=os.environ.get('API_ID', API_ID),
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(pyro_client))
