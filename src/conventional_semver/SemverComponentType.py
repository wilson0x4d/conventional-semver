# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-CopyrightText: (c) 2024 sw4k
# SPDX-License-Identifier: MIT

"""SEMVER Component precedence levels for conventional commit parsing.

Provides the :class:`SemverComponentType` enum with values representing each component of a SEMVER version; ``NONE`` exists as a placeholder when no change is detected during computation.
"""

from enum import IntEnum


class SemverComponentType(IntEnum):
    """SEMVER Component precedence levels for conventional commit parsing.

    Values represent each component of a SEMVER; ``MAJOR``, ``MINOR``, ``PATCH``.
    ``NONE`` exists as a placeholder when no change is detected during computation.
    """

    NONE = 0
    PATCH = 1
    MINOR = 2
    MAJOR = 3
