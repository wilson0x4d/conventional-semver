# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-CopyrightText: (c) 2024 sw4k
# SPDX-License-Identifier: MIT

"""Parse raw git-log output into :class:`~conventional_semver.git_entry` objects.

Splits ``tformat``-encoded git log text on delimiter bytes, extracts hash, refs, subject line, body, and footers per the Conventional Commits specification: footers appear one blank line after the body, each consisting of a word token (hyphens in place of whitespace, ``BREAKING CHANGE`` excepted) followed by a ``:<space>`` or ``<space>#`` separator and a value that spans lines until the next valid token/separator pair.
"""

from __future__ import annotations

import re

from .git_entry import GitEntry


class GitEntryParser:
    """Parse raw git-log output into :class:`~conventional_semver.git_entry` objects.

    Splits ``tformat``-encoded git log text on delimiter bytes, extracts hash, refs (comma-separated), subject line, body, and footers.  The subject runs from the third line to the first blank line; the footer section begins at the earliest subsequent line that is preceded by a blank line (or is the first line of the remainder, which directly follows the blank line after the subject) and matches a Conventional Commits footer token/separator pair (a word token using hyphens in place of whitespace, ``BREAKING CHANGE`` excepted, followed by a ``:<space>`` or ``<space>#`` separator).  Lines before the footer section, however many blank-line-separated paragraphs, remain the body, and a footer's value continues across lines until the next valid token/separator pair is observed.  A block whose first line is not a full 40-character lowercase hex hash is rejected as malformed (e.g. when a raw delimiter byte embedded in a commit message has desynchronized the entry stream).
    """

    __commit_hash_pattern = re.compile(r'[0-9a-f]{40}')
    __footer_token_pattern = re.compile(r'^(?:[A-Za-z0-9-]+|BREAKING CHANGE)(: | #)')

    def __find_footer_section_start(self, lines: list[str]) -> int | None:
        """Locate the first line of the footer section within *lines*.

        The footer section MUST appear one blank line after the body, so the section starts at the earliest line that is preceded by a blank line (or is the first line of the remainder, which directly follows the blank line after the subject) and matches a footer token/separator pair.

        :param lines: The lines after the subject (body and any footers).
        :returns: The index of the first footer line, or ``None`` when the remainder contains no footer section.
        """
        for index, line in enumerate(lines):
            if (index == 0 or lines[index - 1] == '') and self.__footer_token_pattern.match(line):
                return index
        return None

    def __parse_footer_section(self, lines: list[str]) -> list[str]:
        """Split footer-section lines into individual footer strings.

        A line matching a footer token/separator pair begins a new footer; any other line is a continuation of the current footer's value, per the specification which allows values to contain newlines and terminates a value when the next valid token/separator pair is observed.

        :param lines: The lines of the footer section, beginning with a valid footer token/separator line.
        :returns: A list of footer strings, one per token/separator pair, with trailing blank lines stripped.
        """
        footers: list[str] = []
        current: str | None = None
        for line in lines:
            if self.__footer_token_pattern.match(line):
                if current is not None:
                    footers.append(current.rstrip('\n'))
                current = line
            elif current is not None:
                current += '\n' + line
        if current is not None:
            footers.append(current.rstrip('\n'))
        return footers

    def parse(self, input_str: str) -> GitEntry:
        """Parse a block of ``tformat``-encoded git log output.

        Extracts hash, refs (comma-separated), subject line, body, and footers.  The subject runs from the third line to the first blank line; the remainder is split into body and footers per the Conventional Commits specification as described in the class docstring.

        :param input_str: Raw git log text with hash, refs, subject, body, and footers.
        :returns: A populated entry object, or an empty one when *input_str* is falsy or the leading commit hash is malformed.
        """
        if not input_str:
            return GitEntry()

        lines = input_str.split('\n')

        if not self.__commit_hash_pattern.fullmatch(lines[0]):
            return GitEntry()

        entry = GitEntry()
        entry.commit_hash = lines[0]

        if len(lines) > 1:
            refs_raw = lines[1]
            if refs_raw:
                entry.refs = [
                    ref.strip()
                    for ref in refs_raw.split(',')
                    if ref
                ]

            if len(lines) > 2:
                try:
                    subject_end = lines.index('', 2)
                except ValueError:
                    subject_end = len(lines)

                entry.subject = '\n'.join(lines[2:subject_end])

                remainder = lines[subject_end + 1:]
                footer_start = self.__find_footer_section_start(remainder)

                if footer_start is None:
                    entry.body = '\n'.join(remainder).rstrip('\n')
                    entry.footers = []
                else:
                    entry.body = '\n'.join(remainder[:footer_start]).rstrip('\n')
                    entry.footers = self.__parse_footer_section(
                        remainder[footer_start:]
                    )
            else:
                entry.subject = ''
                entry.body = ''
                entry.footers = []

        return entry
