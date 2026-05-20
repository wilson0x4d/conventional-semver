# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from __future__ import annotations

from .Configuration import Configuration
from .GitEntry import GitEntry
from .OutputGenerator import OutputGenerator
from .SemverComponentType import SemverComponentType


class SemverOutputGenerator(OutputGenerator):

    __config: Configuration
    __major: int
    __minor: int
    __patch: int

    def __init__(self, config: Configuration) -> None:
        self.__config = config
        self.__major = config.major_start
        self.__minor = config.minor_start
        self.__patch = config.patch_start

    def handle_commit_entry(self, entry: GitEntry) -> None:
        if entry.is_empty():
            return

        semver_component = SemverComponentType.NONE

        for regex, comp in self.__config.types:
            if comp.value > semver_component.value:
                if regex.search(entry.subject):
                    semver_component = comp

        for regex, comp in self.__config.footers:
            if comp.value > semver_component.value:
                for footer in entry.footers:
                    if regex.search(footer):
                        semver_component = comp
                        break

        if semver_component == SemverComponentType.MAJOR:
            self.__major += 1
            self.__minor = 0
            self.__patch = 0
        elif semver_component == SemverComponentType.MINOR:
            self.__minor += 1
            self.__patch = 0
        elif semver_component == SemverComponentType.PATCH:
            self.__patch += 1

    def generate_output(self) -> None:
        print(f'{self.__major}.{self.__minor}.{self.__patch}')
