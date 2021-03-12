import os

import ffmpeg   # pip install ffmpeg-python
from pyrogram import Client, filters
from pyrogram.types import Message

from pytgcalls import GroupCall     # pip install pytgcalls

main_filter = filters.text & filters.outgoing & ~filters.edited
cmd_filter = lambda cmd: filters.command(cmd, prefixes='!')

group_call = GroupCall(None, path_to_log_file='')


def init_client_and_delete_message(func):
    async def wrapper(client, message):
        group_call.client = client
        await message.delete()

        return await func(client, message)

    return wrapper


@Client.on_message(main_filter & cmd_filter('play'))
async def start_playout(client, message: Message):
    group_call.client = client

    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.delete()
        return

    input_filename = 'input.raw'

    status = '- Downloading... \n'
    await message.edit_text(status)
    audio_original = await message.reply_to_message.download()

    status += '- Converting... \n'

    ffmpeg.input(audio_original).output(
        input_filename,
        format='s16le',
        acodec='pcm_s16le',
        ac=2,
        ar='48k'
    ).overwrite_output().run()

    os.remove(audio_original)

    status += f'- Playing **{message.reply_to_message.audio.title}**...'
    await message.edit_text(status)

    group_call.input_filename = input_filename


@Client.on_message(main_filter & cmd_filter('volume'))
@init_client_and_delete_message
async def volume(_, message):
    if len(message.command) < 2:
        await message.reply_text('You forgot to pass volume (1-200)')

    await group_call.set_my_volume(message.command[1])


@Client.on_message(main_filter & cmd_filter('join'))
@init_client_and_delete_message
async def start(_, message: Message):
    await group_call.start(message.chat.id, False)


@Client.on_message(main_filter & cmd_filter('leave'))
@init_client_and_delete_message
async def stop(*_):
    await group_call.stop()


@Client.on_message(main_filter & cmd_filter('rejoin'))
@init_client_and_delete_message
async def reconnect(*_):
    await group_call.reconnect()


@Client.on_message(main_filter & cmd_filter('replay'))
@init_client_and_delete_message
async def restart_playout(*_):
    group_call.restart_playout()


@Client.on_message(main_filter & cmd_filter('stop'))
@init_client_and_delete_message
async def stop_playout(*_):
    group_call.stop_playout()


@Client.on_message(main_filter & cmd_filter('mute'))
@init_client_and_delete_message
async def mute(*_):
    group_call.set_is_mute(True)


@Client.on_message(main_filter & cmd_filter('unmute'))
@init_client_and_delete_message
async def unmute(*_):
    group_call.set_is_mute(False)


@Client.on_message(main_filter & cmd_filter('pause'))
@init_client_and_delete_message
async def pause(*_):
    group_call.pause_playout()


@Client.on_message(main_filter & cmd_filter('resume'))
@init_client_and_delete_message
async def resume(*_):
    group_call.resume_playout()
