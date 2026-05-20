# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from enum import IntEnum


class SemverComponentType(IntEnum):
    NONE = 0
    PATCH = 1
    MINOR = 2
    MAJOR = 3
