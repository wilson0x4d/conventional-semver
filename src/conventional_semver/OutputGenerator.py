# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from __future__ import annotations
from typing import Protocol, runtime_checkable

from .GitEntry import GitEntry


@runtime_checkable
class OutputGenerator(Protocol):

    def handle_commit_entry(self, entry: GitEntry) -> None:
        ...

    def generate_output(self) -> None:
        ...
