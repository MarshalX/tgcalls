import signal

import ffmpeg  # pip install ffmpeg-python
from pyrogram import Client, filters
from pyrogram.types import Message

from pytgcalls import GroupCall  # pip install pytgcalls

# Example of pinned message in a chat:
'''
Radio stations:

1. https://hls-01-regions.emgsound.ru/11_msk/playlist.m3u8

To start replay to this message with command !start <ID>
To stop use !stop command
'''


# Commands available only for anonymous admins
async def anon_filter(_, __, m: Message):
    return bool(m.from_user is None and m.sender_chat)

anonymous = filters.create(anon_filter)

GROUP_CALLS = {}
FFMPEG_PROCESSES = {}


@Client.on_message(anonymous & filters.command('start', prefixes='!'))
async def start(client, message: Message):
    input_filename = f'radio-{message.chat.id}.raw'

    group_call = GROUP_CALLS.get(message.chat.id)
    if group_call is None:
        group_call = GroupCall(client, input_filename, path_to_log_file='')
        GROUP_CALLS[message.chat.id] = group_call

    if not message.reply_to_message or len(message.command) < 2:
        await message.reply_text('You forgot to replay list of stations or pass a station ID')
        return

    process = FFMPEG_PROCESSES.get(message.chat.id)
    if process:
        process.send_signal(signal.SIGTERM)

    station_stream_url = None
    station_id = message.command[1]
    msg_lines = message.reply_to_message.text.split('\n')
    for line in msg_lines:
        line_prefix = f'{station_id}. '
        if line.startswith(line_prefix):
            station_stream_url = line.replace(line_prefix, '').replace('\n', '')
            break

    if not station_stream_url:
        await message.reply_text(f'Can\'t find a station with id {station_id}')
        return

    await group_call.start(message.chat.id)

    process = ffmpeg.input(station_stream_url).output(
        input_filename,
        format='s16le',
        acodec='pcm_s16le',
        ac=2,
        ar='48k'
    ).overwrite_output().run_async()
    FFMPEG_PROCESSES[message.chat.id] = process

    await message.reply_text(f'Radio #{station_id} is playing...')


@Client.on_message(anonymous & filters.command('stop', prefixes='!'))
async def stop(_, message: Message):
    group_call = GROUP_CALLS.get(message.chat.id)
    if group_call:
        await group_call.stop()

    process = FFMPEG_PROCESSES.get(message.chat.id)
    if process:
        process.send_signal(signal.SIGTERM)
