# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from __future__ import annotations

import hanaro
import logging

from .Configuration import Configuration
from .GitEntry import GitEntry
from .OutputGenerator import OutputGenerator


class ChangelogOutputGenerator(OutputGenerator):

    __config: Configuration
    __logger: logging.Logger

    def __init__(self, config: Configuration) -> None:
        self.__config = config
        self.__logger = hanaro.get_logger()

    def handle_commit_entry(self, entry: GitEntry) -> None:
        # TODO: implement handling logic
        self.__logger.warn('TODO: HandleCommitEntry')

    def generate_output(self) -> None:
        # TODO: implement output generation
        self.__logger.warn('TODO: GenerateOutput')