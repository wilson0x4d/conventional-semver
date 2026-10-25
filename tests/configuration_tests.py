# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :class:`~conventional_semver.configuration` class."""

import os
from punit import fact, inlinedata, raises, theory
from pathlib import Path
import tempfile

from conventional_semver.configuration import Configuration
from conventional_semver.git_entry import GitEntry
from conventional_semver.semver_component_type import SemverComponentType


# -- set_start_from --


@theory
@inlinedata('1.4.0', 1, 4, 0)
@inlinedata('0.0.0', 0, 0, 0)
@inlinedata('  2.0.1  ', 2, 0, 1)
@inlinedata('10.20.30', 10, 20, 30)
def set_start_from_parses_valid_versions(version: str, major: int, minor: int, patch: int) -> None:
    config = Configuration()
    config.set_start_from(version)
    assert config.major_start == major, f"(expected={major}, actual={config.major_start!r})"
    assert config.minor_start == minor, f"(expected={minor}, actual={config.minor_start!r})"
    assert config.patch_start == patch, f"(expected={patch}, actual={config.patch_start!r})"
    assert config.from_version == version, f"(expected={version!r}, actual={config.from_version!r})"


@theory
@inlinedata('1.4')
@inlinedata('1.4.5.7')
@inlinedata('a.b.c')
@inlinedata('1..3')
@inlinedata('-1.0.0')
@inlinedata('1.-2.3')
def set_start_from_rejects_invalid_versions(version: str) -> None:
    config = Configuration()
    assert raises[ValueError](lambda: config.set_start_from(version)), f'(expected ValueError for {version!r})'


# -- validate_git_path --


@fact
def validate_git_path_accepts_real_executable() -> None:
    import shutil

    git = shutil.which('git')
    assert git is not None, 'git must be on PATH for this test'
    Configuration.validate_git_path(git)


# -- config file loading --


def _write_conf(lines: list[str]) -> str:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False, encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
        return fh.name


@fact
def config_file_types_and_footers_are_loaded() -> None:
    conf = _write_conf([
        '# a comment',
        '',
        '[types]',
        'feat.*=minor',
        'fix.*=patch',
        '',
        '[footers]',
        'BREAKING-CHANGE=major',
    ])
    try:
        config = Configuration()
        config.config_file = conf
        config.process_configuration()

        assert len(config.types) == 2, f'(expected=2, actual={len(config.types)})'
        assert config.types[0][1] is SemverComponentType.MINOR, f'(actual={config.types[0][1]!r})'
        assert config.types[1][1] is SemverComponentType.PATCH, f'(actual={config.types[1][1]!r})'
        assert len(config.footers) == 1, f'(expected=1, actual={len(config.footers)})'
        assert config.footers[0][1] is SemverComponentType.MAJOR, f'(actual={config.footers[0][1]!r})'
    finally:
        os.unlink(conf)


@fact
def config_file_case_insensitive_values() -> None:
    conf = _write_conf(['[types]', 'feat.*=Minor'])
    try:
        config = Configuration()
        config.config_file = conf
        config.process_configuration()

        assert len(config.types) == 1, f'(expected=1, actual={len(config.types)})'
        assert config.types[0][1] is SemverComponentType.MINOR, f'(actual={config.types[0][1]!r})'
    finally:
        os.unlink(conf)


@fact
def config_file_invalid_entries_are_skipped() -> None:
    conf = _write_conf([
        '[types]',
        'feat.*=minor',
        'no-equals-here',
        'bad.*=component',
        '=patch',
        'fix.*=',
    ])
    try:
        config = Configuration()
        config.config_file = conf
        config.process_configuration()

        assert len(config.types) == 1, f'(expected=1, actual={len(config.types)})'
    finally:
        os.unlink(conf)


@fact
def missing_explicit_config_file_raises() -> None:
    config = Configuration()
    config.config_file = '/no/such/conventional-semver.conf'
    assert raises[RuntimeError](config.process_configuration), '(expected RuntimeError)'


@fact
def config_file_entries_before_any_section_are_ignored() -> None:
    conf = _write_conf(['feat.*=minor', '[types]', 'fix.*=patch'])
    try:
        config = Configuration()
        config.config_file = conf
        config.process_configuration()

        assert len(config.types) == 1, f'(expected=1, actual={len(config.types)})'
    finally:
        os.unlink(conf)


# -- default fallback --


@fact
def defaults_applied_when_no_config_file_found() -> None:
    cwd = os.getcwd()
    tmp = Path(tempfile.mkdtemp())
    try:
        os.chdir(tmp)
        config = Configuration()
        config.process_configuration()

        assert len(config.types) == 3, f'(expected=3, actual={len(config.types)})'
        assert [t[1] for t in config.types] == [
            SemverComponentType.MAJOR,
            SemverComponentType.MINOR,
            SemverComponentType.PATCH,
        ], f'(actual={[t[1] for t in config.types]!r})'
        assert len(config.footers) == 2, f'(expected=2, actual={len(config.footers)})'
        assert config.footers[0][1] is SemverComponentType.MAJOR, f'(actual={config.footers[0][1]!r})'
        assert config.footers[1][1] is SemverComponentType.MAJOR, f'(actual={config.footers[1][1]!r})'
        assert config.repo_path == str(tmp), f"(expected={str(tmp)!r}, actual={config.repo_path!r})"
        assert config.git_path == 'git', f"(expected='git', actual={config.git_path!r})"
    finally:
        os.chdir(cwd)


@fact
def config_file_in_cwd_is_not_loaded_automatically() -> None:
    """An in-repo (cwd) config must not be auto-loaded — it is opt-in via --config."""
    cwd = os.getcwd()
    tmp = Path(tempfile.mkdtemp())
    (tmp / 'conventional-semver.conf').write_text('[types]\nfeat.*=minor\n', encoding='utf-8')
    try:
        os.chdir(tmp)
        config = Configuration()
        config.process_configuration()

        assert len(config.types) == 3, f'(expected=3 default types, actual={len(config.types)})'
    finally:
        os.chdir(cwd)


@fact
def config_file_in_cwd_is_loaded_when_explicitly_configured() -> None:
    cwd = os.getcwd()
    tmp = Path(tempfile.mkdtemp())
    conf_path = tmp / 'conventional-semver.conf'
    conf_path.write_text('[types]\nfeat.*=minor\n', encoding='utf-8')
    try:
        os.chdir(tmp)
        config = Configuration()
        config.config_file = str(conf_path)
        config.process_configuration()

        assert len(config.types) == 1, f'(expected=1, actual={len(config.types)})'
        assert config.types[0][1] is SemverComponentType.MINOR, f'(actual={config.types[0][1]!r})'
    finally:
        os.chdir(cwd)


# -- process_configuration defaults --


@fact
def start_tag_enables_default_changelog_output_file() -> None:
    cwd = os.getcwd()
    tmp = Path(tempfile.mkdtemp())
    try:
        os.chdir(tmp)
        config = Configuration()
        config.start_tag = 'v1.0.0'
        config.process_configuration()
        assert config.changelog_output_file == str(tmp / 'CHANGELOG.md'), f"(expected={str(tmp / 'CHANGELOG.md')!r}, actual={config.changelog_output_file!r})"
    finally:
        os.chdir(cwd)


@fact
def explicit_changelog_file_is_preserved() -> None:
    config = Configuration()
    config.start_tag = 'v1.0.0'
    config.changelog_output_file = '/custom/CHANGELOG.md'
    config.process_configuration()
    assert config.changelog_output_file == '/custom/CHANGELOG.md', f"(expected='/custom/CHANGELOG.md', actual={config.changelog_output_file!r})"


@fact
def explicit_repo_path_is_preserved() -> None:
    config = Configuration()
    config.repo_path = '/some/repo'
    config.process_configuration()
    assert config.repo_path == '/some/repo', f"(expected='/some/repo', actual={config.repo_path!r})"


# -- start_commit_hash validation --


@fact
def valid_start_commit_hashes_are_accepted() -> None:
    for value in ('abc1234', 'a' * 40, 'DEADBEEF'):
        config = Configuration()
        config.start_commit_hash = value
        config.process_configuration()
        assert config.start_commit_hash == value, f"(expected={value!r}, actual={config.start_commit_hash!r})"


@theory
@inlinedata('abc123')
@inlinedata('a' * 41)
@inlinedata('xyz1234')
@inlinedata('-abc123')
@inlinedata('abc def')
def invalid_start_commit_hashes_raise(value: str) -> None:
    config = Configuration()
    config.start_commit_hash = value
    assert raises[ValueError](config.process_configuration), f'(expected ValueError for {value!r})'


# -- start_tag validation --


@fact
def valid_start_tags_are_accepted() -> None:
    config = Configuration()
    config.start_tag = 'v1.0.0'
    config.process_configuration()
    assert config.start_tag == 'v1.0.0', f"(expected='v1.0.0', actual={config.start_tag!r})"


@theory
@inlinedata('-v1.0.0')
@inlinedata('--foo')
@inlinedata('-')
def leading_dash_start_tags_raise(value: str) -> None:
    config = Configuration()
    config.start_tag = value
    assert raises[ValueError](config.process_configuration), f'(expected ValueError for {value!r})'


# -- changelog template validation --


@fact
def changelog_template_missing_file_raises() -> None:
    config = Configuration()
    config.changelog_template = '/no/such/template.j2'
    assert raises[ValueError](config.process_configuration), '(expected ValueError for a missing template file)'


@fact
def changelog_template_inside_repo_is_blocked_by_default() -> None:
    tmp = Path(tempfile.mkdtemp())
    (tmp / 'template.j2').write_text('# {{ name }}\n', encoding='utf-8')

    config = Configuration()
    config.repo_path = str(tmp)
    config.changelog_template = str(tmp / 'template.j2')
    assert raises[ValueError](config.process_configuration), '(expected ValueError for an in-repo template)'


@fact
def changelog_template_inside_repo_is_allowed_with_flag() -> None:
    tmp = Path(tempfile.mkdtemp())
    (tmp / 'template.j2').write_text('# {{ name }}\n', encoding='utf-8')

    config = Configuration()
    config.repo_path = str(tmp)
    config.changelog_template = str(tmp / 'template.j2')
    config.trust_repo_templates = True
    config.process_configuration()
    assert config.changelog_template == str(tmp / 'template.j2'), f"(expected={str(tmp / 'template.j2')!r}, actual={config.changelog_template!r})"


@fact
def changelog_template_outside_repo_is_allowed_without_flag() -> None:
    tmp = Path(tempfile.mkdtemp())
    (tmp / 'template.j2').write_text('# {{ name }}\n', encoding='utf-8')

    config = Configuration()
    config.repo_path = '/some/other/repo'
    config.changelog_template = str(tmp / 'template.j2')
    config.process_configuration()
    assert config.changelog_template == str(tmp / 'template.j2'), f"(expected={str(tmp / 'template.j2')!r}, actual={config.changelog_template!r})"


# -- compute_semver_change --


def _config_with_types() -> Configuration:
    import re

    config = Configuration()
    config.types = [
        (re.compile(r'^feat.*:[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.MINOR),
        (re.compile(r'^fix.*:[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.PATCH),
        (re.compile(r'^.*:[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.PATCH),
    ]
    config.footers = [
        (re.compile(r'[\S\s]*BREAKING[\-\.]CHANGE[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.MAJOR),
    ]
    return config


@fact
def compute_semver_change_matches_feat_to_minor() -> None:
    config = _config_with_types()
    entry = GitEntry(subject='feat(cli): add help')
    assert Configuration.compute_semver_change(entry, config) is SemverComponentType.MINOR, f'(actual={Configuration.compute_semver_change(entry, config)!r})'


@fact
def compute_semver_change_matches_fix_to_patch() -> None:
    config = _config_with_types()
    entry = GitEntry(subject='fix: crash')
    assert Configuration.compute_semver_change(entry, config) is SemverComponentType.PATCH, f'(actual={Configuration.compute_semver_change(entry, config)!r})'


@fact
def compute_semver_change_breaking_footer_wins_over_type() -> None:
    config = _config_with_types()
    entry = GitEntry(subject='fix: crash', footers=['BREAKING-CHANGE: API redesign'])
    assert Configuration.compute_semver_change(entry, config) is SemverComponentType.MAJOR, f'(actual={Configuration.compute_semver_change(entry, config)!r})'


@fact
def compute_semver_change_returns_none_when_nothing_matches() -> None:
    config = Configuration()
    entry = GitEntry(subject='whatever')
    assert Configuration.compute_semver_change(entry, config) is SemverComponentType.NONE, f'(actual={Configuration.compute_semver_change(entry, config)!r})'
