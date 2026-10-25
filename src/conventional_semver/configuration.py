# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Manage application settings loaded from disk or defaults.

Provides :class:`Configuration` which loads settings from well-known system configuration paths (or an explicit ``--config`` file), builds regex patterns for commit-type detection, and resolves the git repository path when processing is required.
"""

from __future__ import annotations

import hanaro
import logging
import os
from pathlib import Path
import re

from .git_entry import GitEntry
from .semver_component_type import SemverComponentType


class Configuration:
    """Manage application settings loaded from disk or defaults.

    Loads configuration from well-known system configuration paths (or an explicit ``--config`` file), builds regex patterns for commit-type detection, and resolves the git repository path when processing is required.  A configuration file inside the working directory is never loaded automatically; use ``--config`` to load one explicitly.

    Usage
    -----

    .. code-block:: python
        config = Configuration()
        config.process_configuration()
        assert config.repo_path is not None
    """

    __logger: logging.Logger

    trust_repo_templates: bool
    trust_ugc: bool
    changelog_output_file: str | None
    changelog_template: str | None
    commit_url: str | None
    config_file: str
    disable_semver_output: bool
    footers: list[tuple[re.Pattern, SemverComponentType]]
    from_version: str | None
    git_path: str
    major_start: int
    minor_start: int
    patch_start: int
    repo_path: str
    start_commit_hash: str
    start_tag: str
    types: list[tuple[re.Pattern, SemverComponentType]]
    validate_message: bool | str

    def __init__(self) -> None:
        """Initialize with default configuration values.

        Sets all attributes to their defaults and creates the logger instance.
        """
        self.__logger = hanaro.get_logger()

        self.trust_repo_templates = False
        self.trust_ugc = False
        self.changelog_output_file = ''
        self.changelog_template = None
        self.commit_url = None
        self.config_file = ''
        self.disable_semver_output = False
        self.footers = []
        self.from_version = None
        self.git_path = ''
        self.major_start = 0
        self.minor_start = 0
        self.patch_start = 0
        self.repo_path = ''
        self.start_commit_hash = ''
        self.start_tag = ''
        self.types = []
        self.validate_message = False

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

        The value must be one of ``major``, ``minor``, or ``patch`` (case-insensitive).

        :param entry: A string in the form ``kind=value`` where *kind* is converted to a regex and *value* selects the component to increment.
        :param entry_code: Either ``'t'`` for types or ``'f'`` for footers.
        :returns: True if the entry was valid and processed, False otherwise.
        """
        idx = entry.find('=')
        if idx == -1:
            return False

        key_part = entry[:idx].strip()
        if not key_part:
            return False

        regex = self.__build_type_regex(key_part)

        value_part = entry[idx + 1:].strip()
        if not value_part:
            return False

        component_types = {
            'major': SemverComponentType.MAJOR,
            'minor': SemverComponentType.MINOR,
            'patch': SemverComponentType.PATCH,
        }
        component_type = component_types.get(value_part.lower())
        if component_type is None:
            return False

        if entry_code == 't':
            self.types.append((regex, component_type))
        elif entry_code == 'f':
            self.footers.append((regex, component_type))
        else:
            return False

        return True

    @staticmethod
    def __match_patterns(
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

    def __print_configuration_summary(self) -> None:
        """Print a summary of the active configuration to stdout.

        Currently a no-op placeholder for future implementation.
        """
        # TODO:
        pass

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

    def __validate_changelog_template(self) -> None:
        """Validate the configured changelog template path.

        Raises when the template file does not exist, or when it lies inside the repository being processed and :attr:`trust_repo_templates` is not set — template content is compiled as executable Jinja2 code, so repo (and therefore PR/commit) content must not be able to become template code without explicit opt-in.

        :raises ValueError: When the template file is missing, or when an in-repo template was not explicitly allowed.
        """
        if not self.changelog_template:
            return

        template_path = Path(self.changelog_template).expanduser()
        if not template_path.is_file():
            raise ValueError(
                f'changelog template "{self.changelog_template}" does not exist'
            )

        repo_root = Path(self.repo_path).expanduser().resolve()
        inside_repo = (
            template_path.resolve().is_relative_to(repo_root)
            or template_path.absolute().is_relative_to(repo_root)
        )
        if inside_repo and not self.trust_repo_templates:
            raise ValueError(
                'changelog template '
                f'"{self.changelog_template}" lies inside the repo being '
                'processed; repo-relative templates are blocked and must be '
                'explicitly allowed via --trust-repo-templates'
            )

    def __validate_start_commit_hash(self) -> None:
        """Validate the configured start commit hash.

        The value is passed to ``git log`` as a revision argument, so it is constrained to 7-40 hex characters to prevent it from being interpreted as a git option.

        :raises ValueError: When the value is set but is not 7-40 hex characters.
        """
        if not self.start_commit_hash:
            return

        if not re.fullmatch(r'[0-9a-fA-F]{7,40}', self.start_commit_hash):
            raise ValueError(
                f'invalid start commit hash "{self.start_commit_hash}": '
                'expected 7-40 hex characters'
            )

    def __validate_start_tag(self) -> None:
        """Validate the configured start tag.

        The value is passed to ``git log`` as a revision argument, so a leading dash is rejected to prevent it from being interpreted as a git option.

        :raises ValueError: When the value is set but starts with ``-``.
        """
        if not self.start_tag:
            return

        if self.start_tag.startswith('-'):
            raise ValueError(
                f'invalid start tag "{self.start_tag}": '
                'tag names must not start with a dash'
            )

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
        component_type = Configuration.__match_patterns(config.types, entry.subject, component_type)

        # Match each footer line against footer patterns.
        for footer_line in entry.footers:
            component_type = Configuration.__match_patterns(
                config.footers, footer_line, component_type
            )

        return component_type

    def process_configuration(self) -> None:
        """Load configuration from disk or apply defaults.

        Searches the well-known system configuration locations in order of precedence (an explicitly configured ``config_file`` always takes precedence), then falls back to building default commit-type detection regexes when no config is found.  A ``conventional-semver.conf`` in the working directory is intentionally not searched — loading in-repo configuration is opt-in via ``--config``.  Also validates ``start_commit_hash``, ``start_tag``, and the changelog template, and sets ``repo_path``, ``git_path``, and ``changelog_output_file`` to sensible defaults when not already configured.
        """
        config_processed = False

        if self.config_file:
            config_processed = self.__process_configuration_file(self.config_file)
            if not config_processed:
                raise RuntimeError(
                    f'Failed to process expected configuration file: {self.config_file}'
                )
        else:
            # NOTE: a conventional-semver.conf in the working directory is
            # intentionally not searched — a repo being processed (e.g. an
            # untrusted PR checkout) must not be able to supply its own
            # configuration.  Use --config to load an in-repo file explicitly.
            candidate_paths = [
                os.path.expanduser('~/.config/conventional-semver/settings.conf'),
                '/etc/conventional-semver/settings.conf',
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
                    ),
                )
                self.footers.append(
                    (
                        self.__build_footer_regex(r'breaks:'),
                        SemverComponentType.MAJOR,
                    )
                )

        if not self.repo_path:
            self.repo_path = str(Path.cwd())

        if (self.start_commit_hash or self.start_tag) and not self.changelog_output_file:
            self.changelog_output_file = str(Path.cwd() / 'CHANGELOG.md')

        if not self.git_path:
            self.git_path = 'git'

        # Validate git_path exists and is executable when explicitly provided.
        # An empty string means "use PATH" — no further validation needed.
        if self.git_path and self.git_path != 'git':
            Configuration.validate_git_path(self.git_path)

        self.__validate_start_commit_hash()
        self.__validate_start_tag()
        self.__validate_changelog_template()

        self.__print_configuration_summary()

    def set_start_from(self, version: str) -> None:
        """Parse a semver string and set the baseline major/minor/patch.

        Expects the form ``X.Y.Z`` where ``X``, ``Y``, and ``Z`` are
        non-negative integers.  Sets ``major_start``, ``minor_start``, and
        ``patch_start`` accordingly.

        :param version: A valid semver version string such as ``"1.4.0"``.
        :raises ValueError: If the string cannot be parsed as ``X.Y.Z``.
        """
        parts = version.strip().split('.')
        if len(parts) != 3:
            raise ValueError(
                f'Invalid semver baseline "{version}": expected X.Y.Z'
            )
        try:
            major, minor, patch = [int(p) for p in parts]
        except ValueError:
            raise ValueError(
                f'Invalid semver baseline "{version}": all components must be integers'
            )
        if major < 0 or minor < 0 or patch < 0:
            raise ValueError(
                f'Invalid semver baseline "{version}": components must be non-negative'
            )
        self.from_version = version
        self.major_start = major
        self.minor_start = minor
        self.patch_start = patch

    @staticmethod
    def validate_git_path(path: str) -> None:
        """Validate that *path* points to an existing executable.

        When *path* is empty the validation is skipped since an empty value
        defers to a standard ``git`` lookup on ``PATH``.

        :param path: The file-system path to validate.
        :raises ValueError: If the path is non-empty but does not exist or is not executable.
        """
        if not path:
            return
        resolved = Path(path).expanduser()
        if not resolved.is_file():
            raise ValueError(
                f'git path "{path}" does not exist'
            )
        if not os.access(resolved, os.X_OK):
            raise ValueError(
                f'git path "{path}" is not executable'
            )
