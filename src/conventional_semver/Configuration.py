# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Manage application settings loaded from disk or defaults.

Provides :class:`Configuration` which loads settings from ``conventional-semver.json`` or environment paths, builds regex patterns for commit-type detection, and resolves the git repository path when processing is required.
"""

from __future__ import annotations

import hanaro
import logging
import os
from pathlib import Path
import re

from .GitEntry import GitEntry
from .SemverComponentType import SemverComponentType


class Configuration:
    """Manage application settings loaded from disk or defaults.

    Loads configuration from ``conventional-semver.json`` or environment paths, builds regex patterns for commit-type detection, and resolves the git repository path when processing is required.

    Usage
    -----

    .. code-block:: python
        config = Configuration()
        config.process_configuration()
        assert config.repo_path is not None
    """

    changelog_output_file: str
    changelog_template: str | None
    commit_url: str | None
    config_file: str
    disable_semver_output: bool
    footers: list[tuple[re.Pattern, SemverComponentType]]
    git_path: str
    major_start: int
    minor_start: int
    patch_start: int
    start_commit_hash: str
    start_tag: str
    types: list[tuple[re.Pattern, SemverComponentType]]
    repo_path: str

    __logger: logging.Logger

    def __init__(self) -> None:
        """Initialize with default configuration values.

        Sets all attributes to their defaults and creates the logger instance.
        """
        self.__logger = hanaro.get_logger()

        self.changelog_output_file = ''
        self.changelog_template = None
        self.commit_url = None
        self.config_file = ''
        self.disable_semver_output = False
        self.footers = []
        self.git_path = ''
        self.major_start = 0
        self.minor_start = 0
        self.patch_start = 0
        self.start_commit_hash = ''
        self.start_tag = ''
        self.types = []
        self.repo_path = ''

    @staticmethod
    def _match_patterns(
        items: list[tuple[re.Pattern, SemverComponentType]],
        subject_or_line: str,
        current_best: SemverComponentType,
    ) -> SemverComponentType:
        """Return the highest-component-type match for *subject_or_line*.

        Iterates over *items* and replaces *current_best* whenever a pattern matches and the new component's precedence is strictly greater.

        :param items: List of (pattern, component) tuples to check against.
        :param subject_or_line: The string to search within.
        :param current_best: The best match found so far.
        :returns: The highest-precedence matching component type.
        """
        best = current_best
        for pattern, comp in items:
            if comp.value > best.value:
                if pattern.search(subject_or_line):
                    best = comp
        return best

    @staticmethod
    def compute_semver_change(entry: GitEntry, config: Configuration) -> SemverComponentType:
        """Return the highest SemverComponentType matching this entry.

        This is a shared utility so both generators use exactly the same matching logic — no duplication.  Call once per entry during git processing (see ``__main__.py``) and attach the result to ``entry.semver_change``.

        :param entry: A parsed git commit entry with subject and footers.
        :param config: The active project configuration with type/footers patterns.
        :returns: The highest-precedence :class:`SemverComponentType` matched against the entry.
        """
        component_type: SemverComponentType = SemverComponentType.NONE

        # Match subject against type patterns.
        component_type = Configuration._match_patterns(config.types, entry.subject, component_type)

        # Match each footer line against footer patterns.
        for footer_line in entry.footers:
            component_type = Configuration._match_patterns(
                config.footers, footer_line, component_type
            )

        return component_type

    def __build_footer_regex(self, input_str: str) -> re.Pattern:
        """Build a regex pattern that matches *input_str* with any surrounding content.

        :param input_str: The substring to match between arbitrary preceding and trailing text.
        :returns: A compiled regex pattern.
        """
        pattern = r'[\S\s]*' + input_str + r'[\S\s]*'
        return re.compile(pattern, re.MULTILINE | re.IGNORECASE)

    def __build_type_regex(self, input_str: str) -> re.Pattern:
        """Build a regex pattern that matches *input_str* at the start of a line.

        :param input_str: The substring to match at the beginning of a line.
        :returns: A compiled regex pattern.
        """
        pattern = r'^' + input_str + r':[\S\s]*'
        return re.compile(pattern, re.MULTILINE | re.IGNORECASE)

    def __create_entry(self, entry: str, entry_code: str) -> bool:
        """Parse a single ``key=value`` config entry and append its pattern to *types* or *footers*.

        :param entry: A string in the form ``kind=key`` where *kind* is converted to a regex.
        :param entry_code: Either ``'t'`` for types or ``'f'`` for footers.
        :returns: True if the entry was valid and processed, False otherwise.
        """
        idx = entry.find('=')
        if idx == -1:
            return False

        regex = self.__build_type_regex(entry[:idx].strip())

        value_part = entry[idx + 1 :].strip()
        if not value_part:
            return False
        component_code = value_part[0].lower()

        component_type = None
        if component_code == 'j':
            component_type = SemverComponentType.MAJOR
        elif component_code == 'n':
            component_type = SemverComponentType.MINOR
        elif component_code == 't':
            component_type = SemverComponentType.PATCH
        else:
            return False

        if entry_code == 't':
            self.types.append((regex, component_type))
        elif entry_code == 'f':
            self.footers.append((regex, component_type))
        else:
            return False

        return True

    def __process_configuration_file(self, path: str) -> bool:
        """Load and process a configuration file at *path*, returning success status.

        Reads the file line-by-line, parsing ``[types]`` and ``[footers]`` sections.

        :param path: Filesystem path to the configuration file.
        :returns: True if the file was successfully processed, False otherwise.
        """
        config_path = Path(path).expanduser()
        if not config_path.is_file():
            return False

        entry_type = '?'  # tracks whether we are inside [types] or [footers]

        with config_path.open('r', encoding='utf-8') as stream:
            for raw_line in stream:
                line = raw_line.rstrip('\n')
                if not line or line.startswith('#'):
                    continue
                if line == '[types]':
                    entry_type = 't'
                elif line == '[footers]':
                    entry_type = 'f'
                else:
                    if not self.__create_entry(line, entry_type):
                        self.__logger.warning('Could not configure entry from: ' + line)
        return True

    def __print_configuration_summary(self) -> None:
        """Print a summary of the active configuration to stdout.

        Currently a no-op placeholder for future implementation.
        """
        # TODO:
        pass

    def process_configuration(self) -> None:
        """Load configuration from disk or apply defaults.

        Searches for a configuration file in order of precedence, then falls back to building default commit-type detection regexes and resolving the git repository path when no config is found.  Sets ``repo_path``, ``git_path``, and ``changelog_output_file`` to sensible defaults when not already configured.
        """
        config_processed = False

        if self.config_file:
            config_processed = self.__process_configuration_file(self.config_file)
            if not config_processed:
                raise RuntimeError(
                    f'Failed to process expected configuration file: {self.config_file}'
                )
        else:
            candidate_paths = [
                './conventional-semver.json',
                os.path.expanduser('~/.config/conventional-semver/settings.json'),
                '/etc/conventional-semver/settings.json',
            ]
            for cand in candidate_paths:
                if self.__process_configuration_file(cand):
                    config_processed = True
                    break

            if not config_processed:
                # apply a default set of regexes
                self.types.append(
                    (self.__build_type_regex('.*!'), SemverComponentType.MAJOR)
                )
                self.types.append(
                    (self.__build_type_regex('feat.*'), SemverComponentType.MINOR)
                )
                self.types.append(
                    (self.__build_type_regex('.*'), SemverComponentType.PATCH)
                )
                self.footers.append(
                    (
                        self.__build_footer_regex(r'BREAKING[\-\.]CHANGE'),
                        SemverComponentType.MAJOR,
                    )
                )

        if not self.repo_path:
            self.repo_path = str(Path.cwd())

        if (self.start_commit_hash or self.start_tag) and not self.changelog_output_file:
            self.changelog_output_file = str(Path.cwd() / 'CHANGELOG.md')

        # Default changelog output when no config file exists and --changelog was given
        if not config_processed and not self.changelog_output_file:
            self.changelog_output_file = 'CHANGELOG.md'

        if not self.git_path:
            self.git_path = 'git'

        self.__print_configuration_summary()
