# git_adapter.py  (only the relevant parts are shown)

import hanaro
import logging
import os
import subprocess
import sys

from .Configuration import Configuration
from .GitEntryParser import GitEntryParser
from .GitLogStream import GitLogStream
from .OutputGenerator import OutputGenerator


class GitAdapter:

    __config: Configuration
    __git_log_stream: GitLogStream
    __logger: logging.Logger
    __output_generators: list[OutputGenerator]

    def __init__(
        self,
        config: Configuration,
        git_entry_parser: GitEntryParser,
        output_generators: list[OutputGenerator],
    ) -> None:
        self.__config = config
        self.__logger = hanaro.get_logger()
        self.__git_log_stream = GitLogStream(git_entry_parser)
        self.__output_generators = list(output_generators)

    def process_git_log(self) -> None:
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

        self.__git_log_stream.write(stdout_bytes, len(stdout_bytes))

        entry = self.__git_log_stream.readentry()
        while not entry.is_empty():
            for generator in self.__output_generators:
                generator.handle_commit_entry(entry)
            entry = self.__git_log_stream.readentry()

        if proc.returncode != 0:
            self.__logger.error(f'git process exited with non-zero code {proc.returncode}')
