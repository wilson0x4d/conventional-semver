# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Orchestrate the CLI application lifecycle.

Initializes configuration, processes command-line options, runs the git log through entry parsing, and triggers all registered output generators to produce their results.
"""

from __future__ import annotations

import sys

from .changelog_output_generator import ChangelogOutputGenerator
from .command_line_processor import (
    apply_arguments_to_config,
    parse_arguments,
)
from .configuration import Configuration
from .git_adapter import GitAdapter
from .git_entry import GitEntry
from .git_entry_parser import GitEntryParser
from .output_generator import OutputGenerator
from .semver_output_generator import SemverOutputGenerator
from .validator import Validator


def main(argv: list[str] | None = None) -> int:
    """Orchestrate configuration, parsing, and output generation.

    Initializes :class:`~conventional_semver.configuration`, processes command-line options via :func:`~conventional_semver.command_line_processor.parse_arguments` and :func:`~conventional_semver.command_line_processor.apply_arguments_to_config`, runs the git log through :class:`~conventional_semver.git_adapter`, then triggers all registered generators to produce their output.

    :param argv: Command-line arguments; defaults to ``sys.argv[1:]``.
    :returns: Zero on success; non-zero on error.
    """
    try:
        if argv is None:
            argv = sys.argv[1:]

        config = Configuration()
        ns = parse_arguments(argv)
        apply_arguments_to_config(ns, config)
        config.process_configuration()

        if isinstance(config.validate_message, str):
            validator = Validator(config)
            error = validator.validate_message(config.validate_message)
            if error is not None:
                print(f'error: {error}', file=sys.stderr)
                return 1

        if config.validate_message is True:
            validator = Validator(config)
            entries: list[GitEntry] = []
            git_adapter = GitAdapter(config, GitEntryParser(), [])
            git_adapter.process_git_log(entry_sink=entries)

            errors = validator.validate_log(entries)
            if errors:
                for e in errors:
                    print(f'error: {e}', file=sys.stderr)
                return 1

        output_generators = list[OutputGenerator]()
        if not config.disable_semver_output:
            output_generators.append(SemverOutputGenerator(config))
        if config.changelog_output_file:
            changelog_generator = ChangelogOutputGenerator(config)
            if config.changelog_template:
                changelog_generator.set_changelog_template(config.changelog_template)
            output_generators.append(changelog_generator)

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
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
