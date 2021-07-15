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

import tgcalls


uint_ssrc = lambda ssrc: ssrc if ssrc >= 0 else ssrc + 2 ** 32
int_ssrc = lambda ssrc: ssrc if ssrc < 2 ** 31 else ssrc - 2 ** 32


def parse_call_participant(participant_data):
    native_participant = tgcalls.GroupParticipantDescription()

    native_participant.audioSsrc = uint_ssrc(participant_data.source)
    native_participant.isRemoved = participant_data.left

    return native_participant
