# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-CopyrightText: (c) 2024 sw4k
# SPDX-License-Identifier: MIT

"""Buffer raw bytes from ``git log`` and stream parsed entries.

Reads delimited byte blocks (terminated by the ``0xEF`` delimiter byte), decodes them as UTF-8, and passes the result to a :class:`~conventional_semver.git_entry_parser` for structured extraction.
"""

from __future__ import annotations

from .git_entry import GitEntry
from .git_entry_parser import GitEntryParser


class GitLogStream:
    """Buffer raw bytes from ``git log`` and stream parsed entries.

    Accumulates raw bytes written to the internal buffer and yields one :class:`~conventional_semver.GitEntry` per ``0xEF``-delimited block.

    Usage
    -----

    .. code-block:: python
        stream = GitLogStream(GitEntryParser())
        stream.write(raw_bytes, len(raw_bytes))
        entry = stream.readentry()
    """

    __buffer: bytearray
    __git_entry_parser: GitEntryParser

    def __init__(
        self,
        git_entry_parser: GitEntryParser
    ) -> None:
        """Initialize an empty buffer bound to the given parser.

        :param git_entry_parser: Parser used to convert each delimited byte block into a :class:`~conventional_semver.git_entry`.
        """
        self.__buffer = bytearray()
        self.__git_entry_parser = git_entry_parser

    def write(self, buf: bytes, count: int) -> None:
        """Append up to *count* bytes from *buf* to the internal buffer.

        :param buf: Raw byte data from ``git log`` stdout.
        :param count: Number of bytes from *buf* to append (may be less than len(buf)).
        """
        self.__buffer.extend(buf[:count])

    def readentry(self) -> GitEntry:
        """Read and return the next entry, or an empty one if none is available.

        Locates the delimiter byte (0xEF), extracts the preceding bytes, decodes them as UTF-8, and passes the result to the internal parser.  Consumes the read bytes from the buffer.

        :returns: A parsed :class:`~conventional_semver.git_entry` when a complete delimited block is found; otherwise an empty entry.
        """
        terminator = 0xEF
        try:
            term_index = self.__buffer.index(terminator)
        except ValueError:
            return GitEntry()

        entry_bytes = self.__buffer[:term_index]
        del self.__buffer[:term_index + 2]

        try:
            entry_str = entry_bytes.decode('utf-8')
        except UnicodeDecodeError:
            entry_str = entry_bytes.decode('utf-8', errors='replace')
        return self.__git_entry_parser.parse(entry_str)
