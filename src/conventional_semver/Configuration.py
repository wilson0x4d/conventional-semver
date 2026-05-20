# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from __future__ import annotations

import hanaro
import logging
import os
from pathlib import Path
import re

from .SemverComponentType import SemverComponentType


class Configuration:

    changelog_output_file: str
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
        self.__logger = hanaro.get_logger()

        self.changelog_output_file = ''
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

    def __build_footer_regex(self, input_str: str) -> re.Pattern:
        pattern = r'[\S\s]*' + input_str + r'[\S\s]*'
        return re.compile(pattern, re.MULTILINE | re.IGNORECASE)

    def __build_type_regex(self, input_str: str) -> re.Pattern:
        pattern = r'^' + input_str + r':[\S\s]*'
        return re.compile(pattern, re.MULTILINE | re.IGNORECASE)

    def __create_entry(self, entry: str, entry_code: str) -> bool:
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
                        self.__logger.warn('Could not configure entry from: ' + line)
        return True

    def __print_configuration_summary(self) -> None:
        # TODO: 
        pass

    def process_configuration(self) -> None:
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
            self.changelog_output_file = str(Path.cwd() / 'changelog.md')

        if not self.git_path:
            self.git_path = 'git'

        self.__print_configuration_summary()
