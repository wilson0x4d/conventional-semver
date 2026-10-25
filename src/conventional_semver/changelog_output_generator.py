# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Generate a changelog from conventional commit entries.

Accumulates commit data across ``handle_commit_entry`` calls, groups commits by semver value (each unique major.minor.patch gets its own version entry), and renders the result through :class:`~conventional_semver.changelog`.
"""

from __future__ import annotations

from datetime import date
import hanaro
import logging
from pathlib import Path
import subprocess
from typing import Any

from .changelog import Changelog
from .configuration import Configuration
from .git_entry import GitEntry
from .safe_env import scrubbed_env
from .output_generator import OutputGenerator
from .semver_component_type import SemverComponentType


class ChangelogOutputGenerator(OutputGenerator):
    """Accumulate conventional commit entries and render a changelog file.

    Groups commits by semver value, fetches commit dates from git, and writes a markdown-formatted changelog through :class:`~conventional_semver.changelog`.

    Usage
    -----

    .. code-block:: python
        config = Configuration()
        generator = ChangelogOutputGenerator(config)
        generator.generate_output()
    """

    __changelog_template_path: str | None
    __config: Configuration
    __current_semver: tuple[int, int, int]
    __last_semver_str: str | None
    __logger: logging.Logger
    __version_groups: list[dict[str, Any]]

    def __init__(self, config: Configuration) -> None:
        """Initialize with the project configuration.

        :param config: The active configuration containing start values and paths.
        """
        self.__changelog_template_path = None
        self.__config = config
        self.__current_semver = (
            config.major_start,
            config.minor_start,
            config.patch_start,
        )
        self.__last_semver_str = None
        self.__logger = hanaro.get_logger()
        self.__version_groups = []

    @property
    def changelog_template_path(self) -> str | None:
        """The path to a custom Jinja2 template, or None for the built-in."""
        return self.__changelog_template_path

    @property
    def current_semver(self) -> tuple[int, int, int]:
        """The (major, minor, patch) value computed so far."""
        return self.__current_semver

    @property
    def version_groups(self) -> list[dict[str, Any]]:
        """The accumulated version groups, newest first."""
        return self.__version_groups

    def generate_output(self) -> None:
        """Fetch commit dates, assemble data dict, and write the changelog.

        Queries git for per-commit dates, builds the version-grouped data structure, then delegates rendering to :class:`~conventional_semver.changelog`.
        """
        dates: dict[str, str] = {}
        try:
            result = subprocess.run(
                [
                    self.__config.git_path,
                    '--no-pager',
                    '-C',
                    self.__config.repo_path,
                    'log',
                    '--format=%H|%ad',
                    '--date=short',
                ],
                capture_output=True,
                text=True,
                cwd=self.__config.repo_path,
                env=scrubbed_env(),
            )
            for line in result.stdout.strip().splitlines():
                if '|' in line:
                    h, d = line.split('|', 1)
                    dates[h] = d
        except Exception:
            self.__logger.warning('Could not fetch commit dates from git.')

        major, minor, patch = self.__current_semver
        overall_semver = f'{major}.{minor}.{patch}'
        repo_name = Path(self.__config.repo_path).name
        latest_hash = ''
        if self.__version_groups and self.__version_groups[0]['commits']:
            latest_hash = self.__version_groups[0]['commits'][-1]['hash']

        formatted_versions: list[dict[str, Any]] = []
        for group in self.__version_groups:
            formatted_commits: list[dict[str, str | None]] = []
            for c in group['commits']:
                commit_dict: dict[str, str | None] = {
                    'hash': c['hash'],
                    'date': self.resolve_date(c['hash'], dates),
                    'type': c['type'] or '',
                    'scope': c['scope'] or '',
                    'header': c['header'] or '',
                }
                if c.get('body'):
                    commit_dict['body'] = c['body']
                if c.get('footers'):
                    commit_dict['footers'] = c['footers']
                if self.__config.commit_url:
                    base = self.__config.commit_url.rstrip('/') + '/'
                    commit_dict['commit_url'] = base + c['hash']
                formatted_commits.append(commit_dict)
            formatted_versions.append({
                'semver': group['semver'],
                'commits': formatted_commits,
            })

        data: dict[str, Any] = {
            'name': repo_name,
            'semver': overall_semver,
            'date': date.today().isoformat(),
            'hash': latest_hash or 'unknown',
            'versions': formatted_versions,
        }

        changelog = Changelog(autoescape=not self.__config.trust_ugc)
        output = changelog.generate(data, self.__changelog_template_path)
        assert self.__config.changelog_output_file is not None
        output_path = Path(self.__config.changelog_output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding='utf-8')

    def handle_commit_entry(self, entry: GitEntry) -> None:
        """Process a single commit entry.

        Increments the current semver by *entry*'s pre-computed change level, then appends the result to the current version group (or creates a new one when the semver value changes).

        :param entry: A parsed git commit entry with subject, body, and footers.
        """
        if entry.is_empty():
            return

        semver_component = entry.semver_change or SemverComponentType.NONE

        major, minor, patch = self.__current_semver
        if semver_component == SemverComponentType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif semver_component == SemverComponentType.MINOR:
            minor += 1
            patch = 0
        elif semver_component == SemverComponentType.PATCH:
            patch += 1

        self.__current_semver = (major, minor, patch)
        semver_str = f'{major}.{minor}.{patch}'

        if self.__last_semver_str is None or self.__last_semver_str != semver_str:
            self.__version_groups.insert(0, {'semver': semver_str, 'commits': []})
        self.__last_semver_str = semver_str

        commit_entry: dict[str, Any] = {
            'hash': entry.commit_hash[:7],
            'type': entry.extract_type(),
            'scope': entry.extract_scope(),
            'header': entry.extract_header(),
        }
        if entry.body:
            commit_entry['body'] = entry.body
        if entry.footers:
            commit_entry['footers'] = entry.footers

        self.__version_groups[0]['commits'].insert(0, commit_entry)

    @staticmethod
    def resolve_date(short_hash: str, dates: dict[str, str]) -> str:
        """Return the date for *short_hash*, falling back to ``'unknown'``.

        First checks for an exact match; if not found, falls back to prefix-matching against full hashes in *dates*.

        :param short_hash: A truncated commit hash (typically 7 characters).
        :returns: The formatted date string, or ``'unknown'`` when not found.
        """
        if short_hash in dates:
            return dates[short_hash]
        for full_hash, d in dates.items():
            if full_hash.startswith(short_hash):
                return d
        return 'unknown'

    def set_changelog_template(self, path: str) -> None:
        """Set the path to a custom Jinja2 changelog template.

        :param path: Filesystem path to a ``.j2`` template.
        """
        self.__changelog_template_path = path
