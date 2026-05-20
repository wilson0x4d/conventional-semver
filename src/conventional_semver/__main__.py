# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from __future__ import annotations
import sys

from .Configuration import Configuration
from .CommandLineProcessor import CommandlineProcessor
from .ChangelogOutputGenerator import ChangelogOutputGenerator
from .GitEntryParser import GitEntryParser
from .GitAdapter import GitAdapter
from .OutputGenerator import OutputGenerator
from .SemverOutputGenerator import SemverOutputGenerator
from . import __version__, __commit__


def main(argv: list[str]) -> int:
    config = Configuration()
    cmd_processor = CommandlineProcessor(config, __version__, __commit__)
    cmd_processor.process_command_line(argv)
    config.process_configuration()
    output_generators = list[OutputGenerator]()
    if not config.disable_semver_output:
        output_generators.append(SemverOutputGenerator(config))
    if config.changelog_output_file:
        output_generators.append(ChangelogOutputGenerator(config))
    git_entry_parser = GitEntryParser()
    git_adapter = GitAdapter(
        config,
        git_entry_parser,
        output_generators,
    )
    git_adapter.process_git_log()
    for generator in output_generators:
        generator.generate_output()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
