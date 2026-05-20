# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from __future__ import annotations

from .GitEntry import GitEntry
from .GitEntryParser import GitEntryParser


class GitLogStream:

    __git_entry_parser: GitEntryParser
    __buffer: bytearray

    def __init__(
        self,
        git_entry_parser: GitEntryParser
    ) -> None:
        self.__buffer = bytearray()
        self.__git_entry_parser = git_entry_parser

    def write(self, buf: bytes, count: int) -> None:
        self.__buffer.extend(buf[:count])

    def readentry(self) -> GitEntry:
        terminator = 0xEF
        try:
            term_index = self.__buffer.index(terminator)
        except ValueError:
            return GitEntry()

        entry_bytes = self.__buffer[:term_index]
        del self.__buffer[: term_index + 2]

        try:
            entry_str = entry_bytes.decode('utf-8')
        except UnicodeDecodeError:
            entry_str = entry_bytes.decode('utf-8', errors='replace')
        return self.__git_entry_parser.parse(entry_str)
