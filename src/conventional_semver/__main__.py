# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Orchestrate the CLI application lifecycle.

Initializes configuration, processes command-line options, runs the git log through entry parsing, and triggers all registered output generators to produce their results.
"""

from __future__ import annotations


import sys
from typing import Optional

from .ChangelogOutputGenerator import ChangelogOutputGenerator
from .CommandLineProcessor import CommandlineProcessor
from .Configuration import Configuration
from .GitAdapter import GitAdapter
from .GitEntryParser import GitEntryParser
from .OutputGenerator import OutputGenerator
from .SemverOutputGenerator import SemverOutputGenerator

from . import __version__, __commit__


def main(argv: Optional[list[str]] = sys.argv[1:]) -> int:
    """Orchestrate configuration, parsing, and output generation.

    Initializes :class:`~conventional_semver.Configuration`, processes command-line options via :class:`~conventional_semver.CommandlineProcessor`, runs the git log through :class:`~conventional_semver.GitAdapter`, then triggers all registered generators to produce their output.

    :returns: Zero on success; non-zero on error.
    """
    config = Configuration()
    cmd_processor = CommandlineProcessor(config, __version__, __commit__)
    cmd_processor.process_command_line(argv)
    config.process_configuration()

    output_generators = list[OutputGenerator]()
    if not config.disable_semver_output:
        output_generators.append(SemverOutputGenerator(config))
    if config.changelog_output_file:
        generator = ChangelogOutputGenerator(config)
        if config.changelog_template:
            generator.set_changelog_template(config.changelog_template)
        output_generators.append(generator)

    git_entry_parser = GitEntryParser()
    git_adapter = GitAdapter(
        config,
        git_entry_parser,
        output_generators,
        semver_change_callback=Configuration.compute_semver_change,
    )
    git_adapter.process_git_log()

    for generator in output_generators:
        generator.generate_output()
    return 0


if __name__ == '__main__':
    sys.exit(main())
