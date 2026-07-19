# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Orchestrate the CLI application lifecycle.

Initializes configuration, processes command-line options, runs the git log through entry parsing, and triggers all registered output generators to produce their results.
"""

from __future__ import annotations




import os
import subprocess
import sys
from typing import Optional

from .ChangelogOutputGenerator import ChangelogOutputGenerator
from .CommandLineProcessor import (
    CommandlineProcessor,
    apply_arguments_to_config,
    parse_arguments,
)
from .Configuration import Configuration
from .GitAdapter import GitAdapter
from .GitEntry import GitEntry
from .GitEntryParser import GitEntryParser
from .OutputGenerator import OutputGenerator
from .SemverOutputGenerator import SemverOutputGenerator
from .Validator import Validator

from . import __version__, __commit__


def main(argv: Optional[list[str]] = sys.argv[1:]) -> int:
    """Orchestrate configuration, parsing, and output generation.

    Initializes :class:`~conventional_semver.Configuration`, processes command-line options via :func:`~conventional_semver.CommandLineProcessor.parse_arguments` and :func:`~conventional_semver.CommandLineProcessor.apply_arguments_to_config`, runs the git log through :class:`~conventional_semver.GitAdapter`, then triggers all registered generators to produce their output.

    :returns: Zero on success; non-zero on error.
    """
    try:
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
            from .GitLogStream import GitLogStream

            validator = Validator(config)
            git_entry_parser = GitEntryParser()
            git_log_stream = GitLogStream(git_entry_parser)

            try:
                proc = subprocess.Popen(
                    [config.git_path, '--no-pager', '-C', config.repo_path,
                     'log', '--reverse',
                     '--format=tformat:%H%n%D%n%B%n%xef'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    cwd=config.repo_path,
                )
            except OSError as ex:
                raise RuntimeError(f'Failed to start git: {ex}') from ex

            stdout_bytes, stderr_bytes = proc.communicate()

            if stderr_bytes:
                os.write(sys.stderr.fileno(), stderr_bytes)

            if proc.returncode != 0:
                os._exit(proc.returncode)

            git_log_stream.write(stdout_bytes, len(stdout_bytes))
            entries: list[GitEntry] = []
            entry = git_log_stream.readentry()
            while not entry.is_empty():
                entries.append(entry)
                entry = git_log_stream.readentry()

            errors = validator.validate_log(entries)
            if errors:
                for e in errors:
                    print(f'error: {e}', file=sys.stderr)
                return 1

        output_generator: OutputGenerator
        output_generators = list[OutputGenerator]()
        if not config.disable_semver_output:
            output_generators.append(SemverOutputGenerator(config))
        if config.changelog_output_file:
            output_generator = ChangelogOutputGenerator(config)
            if config.changelog_template:
                output_generator.set_changelog_template(config.changelog_template)
            output_generators.append(output_generator)

        git_entry_parser = GitEntryParser()
        git_adapter = GitAdapter(
            config,
            git_entry_parser,
            output_generators,
            semver_change_callback=Configuration.compute_semver_change,
        )
        git_adapter.process_git_log()

        for output_generator in output_generators:
            output_generator.generate_output()
        return 0
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
