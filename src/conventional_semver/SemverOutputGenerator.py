# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Track semver change levels and print the final version to STDOUT.

Processes each commit entry to determine the appropriate major, minor, or patch increment based on conventional commit type patterns, then outputs the computed version string on demand.
"""

from __future__ import annotations

from .Configuration import Configuration
from .GitEntry import GitEntry
from .OutputGenerator import OutputGenerator
from .SemverComponentType import SemverComponentType


class SemverOutputGenerator(OutputGenerator):
    """Track semver change levels and print the final version to STDOUT."""

    __config: Configuration
    __major: int
    __minor: int
    __patch: int

    def __init__(self, config: Configuration) -> None:
        """Initialize with start values from configuration.

        :param config: Provides the initial major, minor, and patch baseline values.
        """
        self.__config = config
        self.__major = config.major_start
        self.__minor = config.minor_start
        self.__patch = config.patch_start

    def handle_commit_entry(self, entry: GitEntry) -> None:
        """Update tracked SEMVER based on the processed entry.

        Inspects the entry's ``semver_change`` and increments the appropriate major/minor/patch counter (resetting lower components per semver rules).  Skips empty entries.

        :param entry: A :class:`~conventional_semver.GitEntry` with a populated ``semver_change`` attribute.
        """
        if entry.is_empty():
            return

        # Use the change level set during processing.
        semver_component = entry.semver_change or SemverComponentType.NONE

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
        """Print the computed semver version to STDOUT."""
        print(f'{self.__major}.{self.__minor}.{self.__patch}')
