#  tgcalls - a Python binding for C++ library by Telegram
#  pytgcalls - a library connecting the Python binding with MTProto
#  Copyright (C) 2020-2021 Il`ya (Marshal) <https://github.com/MarshalX>
#
#  This file is part of tgcalls and pytgcalls.
#
#  tgcalls and pytgcalls is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  tgcalls and pytgcalls is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License v3
#  along with tgcalls. If not, see <http://www.gnu.org/licenses/>.

from os import path
import re

from setuptools import setup, find_packages

base_path = path.abspath(path.dirname(__file__))
packages = find_packages()

with open(path.join(base_path, 'pytgcalls/__init__.py'), encoding='utf-8') as f:
    version = re.findall(r"__version__ = '(.+)'", f.read())[0]

with open(path.join(base_path, '../README.md'), 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name='pytgcalls',
    version=version,
    author='Il`ya Semyonov',
    author_email='ilya@marshal.dev',
    license='LGPLv3',
    url='https://github.com/MarshalX/tgcalls',
    keywords='python, library, telegram, async, asynchronous, webrtc, lib, voice-chat, '
    'voip, group-chat, video-call, calls, pyrogram, telethon, pytgcalls, tgcalls',
    description='a library connecting the tgcalls Python binding with MTProto',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=packages,
    install_requires=['tgcalls == 2.0.0'],
    extras_require={
        'pyrogram': ['pyrogram >= 1.2.0'],
        'telethon': ['telethon >= 1.23.0'],
    },
    python_requires="~=3.6",
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Topic :: Internet',
        'Topic :: Multimedia',
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Video :: Capture',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Capture/Recording',
        'Topic :: Communications',
        'Topic :: Communications :: Internet Phone',
        'Topic :: Communications :: Telephony',
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "Programming Language :: Python :: Implementation",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    project_urls={
        'Documentation': 'https://tgcalls.org/',
        'Telegram Channel': 'https://t.me/tgcallslib',
        'Telegram Chat': 'https://t.me/tgcallschat',
        'Author': 'https://github.com/MarshalX',
    },
)
