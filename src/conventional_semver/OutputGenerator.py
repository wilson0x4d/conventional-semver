# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-CopyrightText: (c) 2024 sw4k
# SPDX-License-Identifier: MIT

"""Define the protocol that all output generators must implement.

Provides the :class:`OutputGenerator` Protocol which specifies the two required methods: ``handle_commit_entry`` for streaming commit data and ``generate_output`` for producing the final result.
"""

from __future__ import annotations
from typing import Protocol, runtime_checkable

from .GitEntry import GitEntry


@runtime_checkable
class OutputGenerator(Protocol):
    """Protocol for objects that accumulate commit entries and produce output."""

    def handle_commit_entry(self, entry: GitEntry) -> None:
        """Process a single parsed git commit entry.

        :param entry: A :class:`~conventional_semver.GitEntry` containing commit metadata.
        """
        ...

    def generate_output(self) -> None:
        """Produce the final output (e.g. stdout or file)."""
        ...
