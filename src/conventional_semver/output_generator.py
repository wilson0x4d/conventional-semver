# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-CopyrightText: (c) 2024 sw4k
# SPDX-License-Identifier: MIT

"""Define the protocol that all output generators must implement.

Provides the :class:`OutputGenerator` Protocol which specifies the two required methods: ``handle_commit_entry`` for streaming commit data and ``generate_output`` for producing the final result.
"""

from __future__ import annotations
from typing import Protocol, runtime_checkable

from .git_entry import GitEntry


@runtime_checkable
class OutputGenerator(Protocol):
    """Protocol for objects that accumulate commit entries and produce output.

    Concrete generators receive every parsed :class:`~conventional_semver.GitEntry` as it streams out of git, then produce their final output once the log is fully processed.

    Usage
    -----

    .. code-block:: python
        class MyGenerator(OutputGenerator):
            def handle_commit_entry(self, entry: GitEntry) -> None:
                ...

            def generate_output(self) -> None:
                ...
    """

    def handle_commit_entry(self, entry: GitEntry) -> None:
        """Process a single parsed git commit entry.

        :param entry: A :class:`~conventional_semver.git_entry` containing commit metadata.
        """
        ...

    def generate_output(self) -> None:
        """Produce the final output (e.g. stdout or file)."""
        ...
