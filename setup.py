# -*- coding: utf-8 -*-

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

import os
import re
import sys
import subprocess
from os import path

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

# Convert distutils Windows platform specifiers to CMake -A arguments
PLAT_TO_CMAKE = {
    'win32': 'Win32',
    'win-amd64': 'x64',
    'win-arm32': 'ARM',
    'win-arm64': 'ARM64',
}

base_path = path.abspath(path.dirname(__file__))


# A CMakeExtension needs a sourcedir instead of a file list.
class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        # This is optional - will print a nicer error if CMake is missing.
        # Since we force CMake via PEP 518 in the pyproject.toml, this should
        # never happen and this whole method can be removed in your code if you
        # want.
        try:
            subprocess.check_output(['cmake', '--version'])
        except OSError:
            msg = 'CMake missing - probably upgrade to a newer version of Pip?'
            raise RuntimeError(msg)

        # To support Python 2, we have to avoid super(), since distutils is all
        # old-style classes.
        build_ext.run(self)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        # required for auto-detection of auxiliary 'native' libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        cfg = 'Debug' if self.debug else 'Release'

        # CMake lets you override the generator - we need to check this.
        # Can be set with Conda-Build, for example.
        cmake_generator = os.environ.get('CMAKE_GENERATOR', '')

        # Set Python_EXECUTABLE instead if you use PYBIND11_FINDPYTHON
        # EXAMPLE_VERSION_INFO shows you how to pass a value into the C++ code
        # from Python.
        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={}'.format(extdir),
            '-DPYTHON_EXECUTABLE={}'.format(sys.executable),
            '-DCMAKE_BUILD_TYPE={}'.format(cfg),  # not used on MSVC, but no harm
        ]

        if self.plat_name == 'win-amd64':
            cmake_args.append(
                '-DDESKTOP_APP_SPECIAL_TARGET=win64'
            )

        build_args = []

        if self.compiler.compiler_type != 'msvc':
            # Using Ninja-build since it a) is available as a wheel and b)
            # multithreads automatically. MSVC would require all variables be
            # exported for Ninja to pick it up, which is a little tricky to do.
            # Users can override the generator with CMAKE_GENERATOR in CMake
            # 3.15+.
            if not cmake_generator:
                cmake_args += ['-GNinja']

        else:

            # Single config generators are handled 'normally'
            single_config = any(x in cmake_generator for x in {'NMake', 'Ninja'})

            # CMake allows an arch-in-generator style for backward compatibility
            contains_arch = any(x in cmake_generator for x in {'ARM', 'Win64'})

            # Specify the arch if using MSVC generator, but only if it doesn't
            # contain a backward-compatibility arch spec already in the
            # generator name.
            if not single_config and not contains_arch:
                cmake_args += ['-A', PLAT_TO_CMAKE[self.plat_name]]

            # Multi-config generators have a different way to specify configs
            if not single_config:
                cmake_args += [
                    '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)
                ]
                build_args += ['--config', cfg]

        # Set CMAKE_BUILD_PARALLEL_LEVEL to control the parallel build level
        # across all generators.
        if 'CMAKE_BUILD_PARALLEL_LEVEL' not in os.environ:
            # self.parallel is a Python 3 only way to set parallel jobs by hand
            # using -j in the build_ext call, not supported by pip or PyPA-build.
            if hasattr(self, 'parallel') and self.parallel:
                # CMake 3.12+ only.
                build_args += ['-j{}'.format(self.parallel)]

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        subprocess.check_call(
            ['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp
        )
        subprocess.check_call(
            ['cmake', '--build', '.'] + build_args, cwd=self.build_temp
        )


with open(path.join(base_path, 'CMakeLists.txt'), 'r', encoding='utf-8') as f:
    regex = re.compile(r'VERSION "([A-Za-z0-9.]+)"$', re.MULTILINE)
    version = re.findall(regex, f.read())[0]

    if version.count('.') == 3:
        major, minor, path_, tweak = version.split('.')
        version = f'{major}.{minor}.{path_}.dev{tweak}'

with open(path.join(base_path, 'README.md'), 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name='tgcalls',
    version=version,
    author='Il`ya Semyonov',
    author_email='ilya@marshal.dev',
    license='LGPLv3',
    url='https://github.com/MarshalX/tgcalls',
    keywords='python, library, telegram, async, asynchronous, webrtc, lib, voice-chat, '
    'voip, group-chat, video-call, calls, pyrogram, telethon, pytgcalls, tgcalls',
    description='a Python binding for tgcalls C++ library',
    long_description=readme,
    long_description_content_type='text/markdown',
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
        'Programming Language :: C++',
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
    python_requires="~=3.6",
    ext_modules=[CMakeExtension('tgcalls')],
    cmdclass={'build_ext': CMakeBuild},
    zip_safe=False,
    project_urls={
        'Telegram Channel': 'https://t.me/tgcallslib',
        'Telegram Chat': 'https://t.me/tgcallschat',
        'Author': 'https://github.com/MarshalX',
    }
)

# build pls