# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from __future__ import annotations
from typing import Optional


class GitEntry:

    def __init__(
        self,
        commit_hash: str = '',
        body: str = '',
        footers: Optional[list[str]] = None,
        refs: Optional[list[str]] = None,
        subject: str = '',
    ) -> None:
        self.commit_hash = commit_hash
        self.body = body
        self.footers = footers if footers is not None else []
        self.refs = refs if refs is not None else []
        self.subject = subject

    def is_empty(self) -> bool:
        """Return ``True`` when the entry contains no data."""
        return (
            not self.commit_hash
            and not self.body
            and not self.footers
            and not self.refs
            and not self.subject
        )

    def __str__(self) -> str:
        """Produce a string representation of the git entry."""
        if self.is_empty():
            return ''

        result = self.commit_hash + '\n'

        if self.refs:
            result += ', '.join(self.refs)

        result += '\n' + self.subject + '\n\n' + self.body + '\n'

        if self.footers:
            result += ','.join(self.footers)

        return result
