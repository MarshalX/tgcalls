# Example of processing audio using pyav: https://github.com/PyAV-Org/PyAV.
# Requires av (pip3 install av) and numpy (pip3 install numpy).


import asyncio
import os
from pytgcalls import GroupCallFactory
import pyrogram
import telethon
import av

API_HASH = None
API_ID = None

CHAT_PEER = '@tgcallschat'  # chat or channel where you want to play audio
SOURCE = 'input.mp3' # Audio file path or stream url: eg. https://file-examples-com.github.io/uploads/2017/11/file_example_MP3_700KB.mp3
CLIENT_TYPE = GroupCallFactory.MTPROTO_CLIENT_TYPE.PYROGRAM
# for Telethon uncomment line below
#CLIENT_TYPE = GroupCallFactory.MTPROTO_CLIENT_TYPE.TELETHON

fifo = av.AudioFifo(format='s16le')
resampler = av.AudioResampler(format='s16', layout='stereo', rate=48000)


def on_played_data(gc, length):
    data = fifo.read(length / 4)
    if data:
        data = data.to_ndarray().tobytes()
    return data


async def main(client):
    await client.start()
    while not client.is_connected:
        await asyncio.sleep(1)

    group_call_factory = GroupCallFactory(client, CLIENT_TYPE)
    group_call_raw = group_call_factory.get_raw_group_call(on_played_data=on_played_data)
    await group_call_raw.start(CHAT_PEER)
    while not group_call_raw.is_connected:
        await asyncio.sleep(1)

    _input = av.open(SOURCE)
    for frame in _input.decode(audio=0):
        if frame:
            frame.pts = None
            frame = resampler.resample(frame)
            fifo.write(frame)

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
