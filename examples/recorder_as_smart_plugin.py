"""Record Audio from Telegram Voice Chat

Dependencies:
- ffmpeg

Requirements (pip):
- pytgcalls[pyrogram]
- ffmpeg-python

Start the userbot and send !record to a voice chat
enabled group chat to start recording for 30 seconds
"""
import asyncio
import os
from datetime import datetime

import ffmpeg
from pyrogram import Client, filters
from pyrogram.types import Message

from pytgcalls import GroupCallFactory, GroupCallFileAction

GROUP_CALL = None
SECONDS_TO_RECORD = 30


@Client.on_message(
    filters.group & filters.text & filters.outgoing & ~filters.edited & filters.command('record', prefixes='!')
)
async def record_from_voice_chat(client: Client, m: Message):
    global GROUP_CALL
    if not GROUP_CALL:
        GROUP_CALL = GroupCallFactory(client, path_to_log_file='').get_file_group_call()

    GROUP_CALL.add_handler(network_status_changed_handler, GroupCallFileAction.NETWORK_STATUS_CHANGED)

    await GROUP_CALL.start(m.chat.id)
    await m.delete()


async def network_status_changed_handler(context, is_connected: bool):
    if is_connected:
        print('- JOINED VC')
        await record_and_send_opus_and_stop(context)
    else:
        print('- LEFT VC')


async def record_and_send_opus_and_stop(context):
    chat_id = int(f'-100{context.full_chat.id}')
    chat_info = await context.client.get_chat(chat_id)

    status_msg = await context.client.send_message(chat_id, '1/3 Recording...')

    utcnow_unix, utcnow_readable = get_utcnow()
    record_raw_filename, record_opus_filename = f'vcrec-{utcnow_unix}.raw', f'vcrec-{utcnow_unix}.opus'
    context.output_filename = record_raw_filename

    await asyncio.sleep(SECONDS_TO_RECORD)
    context.stop_output()

    await status_msg.edit_text('2/3 Transcoding...')
    ffmpeg.input(record_raw_filename, format='s16le', acodec='pcm_s16le', ac=2, ar='48k', loglevel='error').output(
        record_opus_filename
    ).overwrite_output().run()

    record_probe = ffmpeg.probe(record_opus_filename, pretty=None)

    stream = record_probe['streams'][0]
    time_base = [int(x) for x in stream['time_base'].split('/')]
    duration = round(time_base[0] / time_base[1] * int(stream['duration_ts']))

    caption = [
        f'- Format: `{stream["codec_name"]}`',
        f'- Channel(s): `{stream["channels"]}`',
        f'- Sampling rate: `{stream["sample_rate"]}`',
        f'- Bit rate: `{record_probe["format"]["bit_rate"]}`',
        f'- File size: `{record_probe["format"]["size"]}`',
    ]

    performer = chat_info.title
    if chat_info.username:
        performer = f'@{chat_info.username}'

    title = f'[VCREC] {utcnow_readable}'
    thumb_file = None
    if chat_info.photo:
        thumb_file = await context.client.download_media(chat_info.photo.big_file_id)

    await status_msg.edit_text('3/3 Uploading...')
    await context.client.send_audio(
        chat_id,
        record_opus_filename,
        caption='\n'.join(caption),
        duration=duration,
        performer=performer,
        title=title,
        thumb=thumb_file,
    )
    await status_msg.delete()

    await context.stop()

    if thumb_file:
        os.remove(thumb_file)
    [os.remove(f) for f in (record_raw_filename, record_opus_filename, thumb_file)]


def get_utcnow():
    utcnow = datetime.utcnow()
    utcnow_unix = utcnow.strftime('%s')
    utcnow_readable = utcnow.strftime('%Y-%m-%d %H:%M:%S')
    return utcnow_unix, utcnow_readable
