# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Represent a single conventional-commit parsed from git log output.

Provides :class:`GitEntry` with fields for commit metadata and helper methods for extracting the type, scope, and header portions of a conventional commit subject line.
"""

from __future__ import annotations
import re
from typing import Optional

from .SemverComponentType import SemverComponentType


class GitEntry:
    """Represent a single conventional-commit parsed from git log output.

    Matches conventional commit format: ``type(scope): header`` (e.g. ``feat(cli): add help``, ``fix: crash``, ``chore: update deps``).
    """

    __subject_pattern = re.compile(r'^([^!:(\s]+)(?:\(([^)]+)\))?!?:(.*)')

    def __init__(
        self,
        commit_hash: str = '',
        body: str = '',
        footers: Optional[list[str]] = None,
        refs: Optional[list[str]] = None,
        subject: str = '',
        commit_date: str = '',
        semver: str = '',
    ) -> None:
        """Initialize with git log fields and defaults.

        :param commit_hash: Full hash of the commit.
        :param body: Multi-line commit body text.
        :param footers: Conventional commit footers (e.g. ``Co-Authored-By``).
        :param refs: Git references (tags, branch names) pointing to the commit.
        :param subject: Single-line commit subject line.
        :param commit_date: Date of the commit in ISO format.
        :param semver: Semantic version string associated with this commit.
        """
        self.commit_hash = commit_hash
        self.body = body
        self.footers = footers if footers is not None else []
        self.refs = refs if refs is not None else []
        self.subject = subject
        self.commit_date = commit_date
        self.semver = semver
        # semver_change is set centrally during git processing so all generators
        # see the same change-level without duplicating matching logic.
        self.semver_change: SemverComponentType = SemverComponentType.NONE

    def is_empty(self) -> bool:
        """Return ``True`` when the entry contains no data."""
        return (
            not self.commit_hash
            and not self.body
            and not self.footers
            and not self.refs
            and not self.subject
        )

    def _extract_type(self) -> str:
        """Return the conventional commit type (e.g. ``'feat'``)."""
        match = self.__subject_pattern.match(self.subject)
        return match.group(1) if match else ''

    def _extract_scope(self) -> str:
        """Return the conventional commit scope, or empty string."""
        match = self.__subject_pattern.match(self.subject)
        return match.group(2) if match and match.group(2) else ''

    def _extract_header(self) -> str:
        """Return the conventional commit header text (after ``': '``)."""
        match = self.__subject_pattern.match(self.subject)
        return match.group(3).strip() if match else ''

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
