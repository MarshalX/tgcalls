<p align="center">
    <a href="https://github.com/MarshalX/tgcalls">
        <img src="https://github.com/MarshalX/tgcalls/raw/main/.github/images/logo.png" alt="tgcalls">
    </a>
    <br>
    <b>Voice chats, private incoming and outgoing calls in Telegram for Developers</b>
    <br>
    <a href="https://github.com/MarshalX/tgcalls/tree/main/examples">
        Examples
    </a>
    •
    <a href="https://tgcalls.org">
        Documentation
    </a>
    •
    <a href="https://t.me/tgcallslib">
        Channel
    </a>
    •
    <a href="https://t.me/tgcallschat">
        Chat
    </a>
</p>

## Telegram WebRTC (VoIP)

```python
from pyrogram import Client, filters
from pyrogram.utils import MAX_CHANNEL_ID

from pytgcalls import GroupCall

app = Client('pytgcalls')
group_call = GroupCall(app, 'input.raw')


@group_call.on_network_status_changed
async def on_network_changed(gc: GroupCall, is_connected: bool):
    chat_id = MAX_CHANNEL_ID - gc.full_chat.id
    if is_connected:
        await app.send_message(chat_id, 'Successfully joined!')
    else:
        await app.send_message(chat_id, 'Disconnected from voice chat..')


@app.on_message(filters.outgoing & filters.command('join'))
async def join(_, message):
    await group_call.start(message.chat.id)


app.run()
```

This project consists of two main parts: [tgcalls](#tgcalls), [pytgcalls](#pytgcalls).
The first is a C++ Python extension. 
The second uses the extension along with Pyrogram.
All together, it allows you to create userbots that can record and 
broadcast in voice chats, make and receive private calls.

### Features

- Python solution.
- Work with voice chats in channels and chats.
- [Multiply voice chats](https://github.com/MarshalX/tgcalls/blob/main/examples/radio_as_smart_plugin.py).
- [Work with data in bytes directly from Python](https://github.com/MarshalX/tgcalls/blob/main/examples/restream_using_raw_data.py).
- [Payout from file](https://github.com/MarshalX/tgcalls/blob/main/examples/playout.py).
- [Output (recording) to file](https://github.com/MarshalX/tgcalls/blob/main/examples/recorder_as_smart_plugin.py).
- Change files at runtime.
- Pause/resume.
- Stop payout/output.
- Join as channels.
- Join using invite (speaker) links.
- Speaking status with audio levels inside and outside of voice chat.
- Mute, unmute, volume control, system of handlers and more...

### Requirements

- Python 3.6 or higher.
- A [Telegram API key](https://docs.pyrogram.org/intro/setup#api-keys).
- x86_64 platform and Unix system (WSL for Windows).


### TODO list
- Incoming and Outgoing calls (already there and working, but not in release).
- Private and group video calls.
- Windows and macOS Python wheels
[and more...](https://github.com/MarshalX/tgcalls/issues)

### Installing

``` bash
pip3 install pytgcalls -U
```

<hr>
<p align="center">
    <a href="https://github.com/MarshalX/tgcalls">
        <img src="https://github.com/MarshalX/tgcalls/raw/main/.github/images/tgcalls.png" alt="tgcalls">
    </a>
    <br>
    <a href="https://pypi.org/project/tgcalls/">
        PyPi
    </a>
    •
    <a href="https://github.com/MarshalX/tgcalls/tree/main/tgcalls">
        Sources
    </a>
</p>

## tgcalls 

The first part of the project is C++ extensions for Python. [Pybind11](https://github.com/pybind/pybind11)
was used to write it. Binding occurs to the [tgcalls](https://github.com/TelegramMessenger/tgcalls)
library by Telegram, which is used in all clients. 
To implement the library, the code of official clients (tdesktop and android) was studied.
Changes have been made to the Telegram library. 
All modified code is [available as a subtree](https://github.com/MarshalX/tgcalls/tree/main/tgcalls/third_party/lib_tgcalls)
in this repository. The main idea of the changes is to add the ability to play 
from other sources (from a file, for example) and improve the sound quality by making the minimum number 
of code edits for a simple update.
In addition to changes in the Telegram library, a minimal change was made to the WebRTC,
also [available as a subtree](https://github.com/MarshalX/tgcalls/tree/main/tgcalls/third_party/webrtc).

### How to build

- [Linux](build/ubuntu).
- [macOS](build/macos).
- [Windows](build/windows).

Also you can investigate into [manylinux builds](build/manylinux).

### Documentation

Temporarily, instead of documentation, you can use [an example](pytgcalls/pytgcalls)
along with MTProto.

<hr>
<p align="center">
    <a href="https://github.com/MarshalX/tgcalls">
        <img src="https://github.com/MarshalX/tgcalls/raw/main/.github/images/pytgcalls.png" alt="pytgcalls">
    </a>
    <br>
    <a href="https://tgcalls.org">
        Documentation
    </a>
    •
    <a href="https://pypi.org/project/pytgcalls/">
        PyPi
    </a>
    •
    <a href="https://github.com/MarshalX/tgcalls/tree/main/pytgcalls">
        Sources
    </a>
</p>

## pytgcalls 

This project is implementation of using [tgcalls](#tgcalls) 
Python binding together with [MTProto](https://core.telegram.org/mtproto).
A Pyrogram was chosen as a library for working with Telegram Mobile Protocol. 
You can write your own implementation to work with Telethon or other libraries.

### Learning by example

Visit [this page](https://github.com/MarshalX/tgcalls/tree/main/examples) to discover the official examples.

### Documentation

`pytgcalls`'s documentation lives at [tgcalls.org](https://tgcalls.org).

### Audio file formats

RAW files are now used. You will have to convert to this format yourself
using ffmpeg. This procedure may [become easier in the future](https://github.com/MarshalX/tgcalls/issues/15).

From mp3 to raw (to play in voice chat):
```
ffmpeg -i input.mp3 -f s16le -ac 2 -ar 48000 -acodec pcm_s16le input.raw
```

From raw to mp3 (files with recordings):
```
ffmpeg -f s16le -ac 2 -ar 48000 -acodec pcm_s16le -i output.raw clear_output.mp3
```

For playout live stream you can use this one:
```
ffmpeg -y -i http://stream2.cnmns.net/hope-mp3 -f s16le -ac 2 -ar 48000 -acodec pcm_s16le input.raw
```

For YouTube videos and live streams you can use youtube-dl:
```
ffmpeg -i "$(youtube-dl -x -g "https://youtu.be/xhXq9BNndhw")" -f s16le -ac 2 -ar 48000 -acodec pcm_s16le input.raw
```

And set input.raw as input filename.

<hr>

### Getting help

You can get help in several ways:
- We have a community of developers helping each other in our 
[Telegram group](https://t.me/tgcallschat).
- Report bugs, request new features or ask questions by creating 
[an issue](https://github.com/MarshalX/tgcalls/issues/new) or 
[a discussion](https://github.com/MarshalX/tgcalls/discussions/new).

### Contributing

Contributions of all sizes are welcome.

### Special thanks to

- [@FrayxRulez](https://github.com/FrayxRulez) for amazing code of [Unigram](https://github.com/UnigramDev/Unigram).
- [@john-preston](https://github.com/john-preston) for [Telegram Desktop](https://github.com/telegramdesktop/tdesktop) and [tgcalls](https://github.com/TelegramMessenger/tgcalls).
- [@bakatrouble](https://github.com/bakatrouble/) for help and inspiration by [pytgvoip](https://github.com/bakatrouble/pytgvoip).
- [@delivrance](https://github.com/delivrance) for [Pyrogram](https://github.com/pyrogram/pyrogram).

### License

You may copy, distribute and modify the software provided that modifications
are described and licensed for free under [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html).
Derivatives works (including modifications or anything statically
linked to the library) can only be redistributed under LGPL-3, but
applications that use the library don't have to be.
