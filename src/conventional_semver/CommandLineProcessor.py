# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-CopyrightText: (c) 2024 sw4k
# SPDX-License-Identifier: MIT

"""Parse command-line arguments and configure application behaviour.

Provides the :func:`parse_arguments` function which returns an
:class:`~argparse.Namespace`, and the helper :func:`apply_arguments_to_config`
which maps those parsed values onto a :class:`~conventional_semver.Configuration`
instance.

The legacy :class:`CommandlineProcessor` class is retained for backward
compatibility with any external importers.
"""

from __future__ import annotations

import argparse
from typing import Optional

from .Configuration import Configuration


def _create_parser() -> argparse.ArgumentParser:
    """Build and return the ArgumentParser with all CLI flags."""
    parser = argparse.ArgumentParser(
        prog='conventional-semver',
        description='Process conventional commits and emit SEMVER (and optionally CHANGELOG).',
    )

    # -- Version info --
    parser.add_argument('--version', action='version', version=_get_version())

    # -- Logging / output control --
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='enable verbose (debug) output',
    )
    parser.add_argument(
        '--no-semver',
        action='store_true',
        dest='disable_semver_output',
        default=False,
        help='disable SEMVER output to STDOUT',
    )

    # -- Validation --
    parser.add_argument(
        '--validate',
        nargs='?',
        const=True,
        default=False,
        metavar='MESSAGE',
        help='validate commit messages against configured patterns (use MESSAGE to validate a specific commit instead of the log)',
    )

    # -- Changelog options --
    # nargs='?' with const means: no value -> 'CHANGELOG.md'; value provided -> that path;
    # absent entirely -> None (changelog disabled).
    parser.add_argument(
        '--changelog',
        nargs='?',
        const='CHANGELOG.md',
        default=None,
        metavar='FILE',
        help='enable changelog output; defaults to CHANGELOG.md if no file given',
    )

    # -- Changelog display options --
    parser.add_argument(
        '--changelog-template',
        dest='changelog_template',
        default=None,
        metavar='PATH',
        help='path to a custom Jinja2 changelog template',
    )
    parser.add_argument(
        '--commit-url',
        dest='commit_url',
        default=None,
        metavar='URL',
        help='base URL for commit links; a / separator is added between the URL and hash',
    )
    parser.add_argument(
        '--commit',
        dest='start_commit_hash',
        default=None,
        metavar='HASH',
        help='start changelog from a specific commit hash',
    )

    # -- Start-point option (mutually exclusive with --commit) --
    parser.add_argument(
        '--tag',
        dest='start_tag',
        default=None,
        metavar='NAME',
        help='start changelog from a specific tag name',
    )

    # -- General options --
    parser.add_argument(
        '--config',
        dest='config_file',
        default='',
        metavar='FILE',
        help='path to a custom config file (default: search standard locations)',
    )
    parser.add_argument(
        '--git-path',
        dest='git_path',
        default='',
        metavar='PATH',
        help='override the path to the git executable (default: use PATH)',
    )

    # -- SEMVER baseline options --
    parser.add_argument(
        '--from',
        dest='from_version',
        default=None,
        metavar='VERSION',
        help='set the baseline semver as a single X.Y.Z value',
    )
    parser.add_argument(
        '--major',
        dest='major_start',
        type=int,
        default=0,
        metavar='N',
        help="SEMVER 'Major' component start value (default: 0, ignored when --from is used)",
    )
    parser.add_argument(
        '--minor',
        dest='minor_start',
        type=int,
        default=0,
        metavar='N',
        help="SEMVER 'Minor' component start value (default: 0, ignored when --from is used)",
    )
    parser.add_argument(
        '--patch',
        dest='patch_start',
        type=int,
        default=0,
        metavar='N',
        help="SEMVER 'Patch' component start value (default: 0, ignored when --from is used)",
    )

    # -- Positional argument --
    parser.add_argument(
        'repo_path',
        nargs='?',
        default=None,
        metavar='REPO',
        help='path to the git repository to process; defaults to the current working directory',
    )

    return parser


# --- Module-level parser singleton (created lazily on first use) ---
_parser: argparse.ArgumentParser | None = None


def _get_parser() -> argparse.ArgumentParser:
    """Return a cached ArgumentParser, creating one if needed."""
    global _parser
    if _parser is None:
        _parser = _create_parser()
    return _parser


def _get_version() -> str:
    """Return the version string, loading it lazily to avoid circular imports."""
    from . import __version__, __commit__
    return f'conventional-semver {__version__} ({__commit__})'


def parse_arguments(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments and return an :class:`~argparse.Namespace`.

    :param argv: Command-line arguments; defaults to ``sys.argv[1:]``.
                 Callers that receive raw ``sys.argv`` must strip the program name (``argv[0]``)
                 before passing it here — the legacy :class:`CommandlineProcessor` class does this
                 automatically. Direct callers (e.g. tests) should pass flags-only lists.
    :returns: An :class:`~argparse.Namespace` with all parsed attributes.
    """
    parser = _get_parser()
    if argv is None:
        return parser.parse_args()  # argparse defaults to sys.argv[1:]
    return parser.parse_args(argv or ())


def apply_arguments_to_config(ns: argparse.Namespace, config: Configuration) -> None:
    """Map parsed namespace attributes onto a :class:`~conventional_semver.Configuration` instance.

    Only non-empty / non-None values are applied so that default configuration
    values are not silently overwritten.

    :param ns: The parsed argument namespace from :func:`parse_arguments`.
    :param config: The configuration object to update.
    """
    # Changelog output (enabled when --changelog is present)
    if ns.changelog is not None:
        config.changelog_output_file = ns.changelog

    # Optional changelog metadata
    if ns.changelog_template:
        config.changelog_template = ns.changelog_template
    if ns.commit_url:
        config.commit_url = ns.commit_url.rstrip('/')
    if ns.start_commit_hash:
        config.start_commit_hash = ns.start_commit_hash
    if ns.start_tag:
        config.start_tag = ns.start_tag

    # General configuration overrides
    if ns.config_file:
        config.config_file = ns.config_file
    if ns.git_path:
        config.git_path = ns.git_path

    # SEMVER baseline (from_version takes precedence over individual flags)
    if ns.from_version:
        try:
            config.set_start_from(ns.from_version)
        except ValueError as exc:
            raise SystemExit(f'error: {exc}') from exc
    else:
        config.major_start = ns.major_start
        config.minor_start = ns.minor_start
        config.patch_start = ns.patch_start

    # Output control
    if ns.disable_semver_output:
        config.disable_semver_output = True
    if ns.repo_path:
        config.repo_path = ns.repo_path
    config.validate_message = ns.validate


class CommandlineProcessor:
    """Parse command-line arguments and configure application behaviour.

    .. deprecated::
        Use :func:`parse_arguments` directly.  This class is retained for
        backward compatibility with any external importers.

    Usage
    -----

    .. code-block:: python

        config = Configuration()
        processor = CommandlineProcessor(config, '1.0.0', 'abc123')
        processor.process_command_line(['--changelog'])
    """

    _config: Configuration

    def __init__(self, config: Configuration, _version: str, _commit: str) -> None:
        """Initialize with configuration and version metadata.

        :param config: The active project configuration.
        :param _version: The application version string (unused, kept for API compat).
        :param _commit: The build commit hash (unused, kept for API compat).
        """
        self._config = config  # noqa: SLF001

    def process_command_line(self, argv: Optional[list[str]] = None) -> None:
        """Parse *argv* and apply command-line options to the configuration.

        :param argv: Command-line arguments; defaults to ``sys.argv`` (with argv[0] stripped).
        """
        # Defensive stripping: when 2+ elements are present, the first is likely
        # argv[0] (the script path) — strip it so argparse only sees real flags.
        # When exactly one element exists and looks like a file path (starts with / or \),
        # also strip it as a leftover argv[0]. Single-element lists that are clearly flags
        # (start with -) pass through unchanged; an empty list or None lets
        # parse_arguments fall back to sys.argv without risking a double-slice that
        # would drop flags like --changelog.
        stripped: list[str]
        if argv and len(argv) > 1:
            stripped = argv[1:]
        elif argv and len(argv) == 1 and argv[0].startswith(('/', '\\')):
            stripped = []
        else:
            stripped = argv if argv is not None else []
        ns = parse_arguments(stripped)
        apply_arguments_to_config(ns, self._config)
