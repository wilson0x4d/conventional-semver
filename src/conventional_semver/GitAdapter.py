# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Orchestrate git log processing through entry parsing and output generation.

Spawns ``git log``, streams raw bytes to :class:`~conventional_semver.GitLogStream`, parses each entry, computes semver change levels, and routes results to all registered :class:`~conventional_semver.OutputGenerator` instances.
"""

from __future__ import annotations

import hanaro
import logging
import os
import subprocess
import sys
from typing import Callable

from .Configuration import Configuration
from .GitEntryParser import GitEntryParser
from .GitLogStream import GitLogStream
from .GitEntry import GitEntry
from .OutputGenerator import OutputGenerator
from .SemverComponentType import SemverComponentType

_ComponentTypeCallback = Callable[[GitEntry, Configuration], SemverComponentType]


class GitAdapter:
    """Orchestrate git log processing through entry parsing and output generation.

    Spawns ``git log``, streams raw bytes to :class:`~conventional_semver.GitLogStream`, parses each entry, computes semver change levels, and routes results to all registered :class:`~conventional_semver.OutputGenerator` instances.

    Usage
    -----

    .. code-block:: python
        parser = GitEntryParser()
        generators: list[OutputGenerator] = [SemverOutputGenerator(config)]
        adapter = GitAdapter(config, parser, generators)
        adapter.process_git_log()
    """

    __semver_change_callback: _ComponentTypeCallback | None
    __config: Configuration
    __git_log_stream: GitLogStream
    __logger: logging.Logger
    __output_generators: list[OutputGenerator]

    def __init__(
        self,
        config: Configuration,
        git_entry_parser: GitEntryParser,
        output_generators: list[OutputGenerator],
        semver_change_callback: _ComponentTypeCallback | None = None,
    ) -> None:
        """Initialize with configuration and output pipeline.

        :param config: The active project configuration.
        :param git_entry_parser: Parser used to interpret raw git log output.
        :param output_generators: List of generators that will receive each parsed commit entry.
        :param semver_change_callback: Optional callable for computing semver change levels.
        """
        self.__semver_change_callback = semver_change_callback
        self.__config = config
        self.__logger = hanaro.get_logger()
        self.__git_log_stream = GitLogStream(git_entry_parser)
        self.__output_generators = list(output_generators)

    def process_git_log(self) -> None:
        """Execute ``git log`` and pipe entries through parsers and generators.

        Spawns a git log process in reverse chronological order, parses each entry, computes change levels via the callback (if provided), and routes them to all registered output generators.  Exits with the git exit code on failure.
        """
        argv = [
            self.__config.git_path,
            '--no-pager',
            '-C',
            self.__config.repo_path,
            'log',
            '--reverse',
            '--format=tformat:%H%n%D%n%B%n%xef',
        ]
        try:
            proc = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.__config.repo_path,
            )
        except OSError as ex:
            raise RuntimeError(f'Failed to start git: {ex}') from ex

        stdout_bytes, stderr_bytes = proc.communicate()

        if stderr_bytes:
            os.write(sys.stderr.fileno(), stderr_bytes)

        if proc.returncode != 0:
            os._exit(proc.returncode)

        self.__git_log_stream.write(stdout_bytes, len(stdout_bytes))

        entry = self.__git_log_stream.readentry()
        while not entry.is_empty():
            if self.__semver_change_callback is not None:
                entry.semver_change = self.__semver_change_callback(entry, self.__config)
            for generator in self.__output_generators:
                generator.handle_commit_entry(entry)
            entry = self.__git_log_stream.readentry()
