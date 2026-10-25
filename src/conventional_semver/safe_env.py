# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Build a scrubbed environment."""

from __future__ import annotations

import os
import re

# Git/platform control variables (GIT.*, UV.*, PYPI.*, PIP.*) and common
# secret-bearing names (anything containing TOKEN or KEY) are removed from
# the environment.
_ENV_SCRUB_RE = re.compile(
    r'GIT.*|UV.*|PYPI.*|PIP.*|.*TOKEN.*|.*KEY.*',
    re.IGNORECASE,
)


def scrubbed_env() -> dict[str, str]:
    """Return a copy of the process environment scrubbed of sensitive variables.

    :returns: A new environment mapping stripped of security critical variables.
    """
    return {
        name: value
        for name, value in os.environ.items()
        if _ENV_SCRUB_RE.search(name) is None
    }
