# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :class:`~conventional_semver.semver_output_generator` class."""

from punit import fact, trait
from punit.mocks import patch

from conventional_semver.configuration import Configuration
from conventional_semver.git_entry import GitEntry
from conventional_semver.semver_component_type import SemverComponentType
from conventional_semver.semver_output_generator import SemverOutputGenerator


def _make_generator(major: int = 0, minor: int = 0, patch: int = 0) -> SemverOutputGenerator:
    config = Configuration()
    config.major_start = major
    config.minor_start = minor
    config.patch_start = patch
    return SemverOutputGenerator(config)


def _bump(generator: SemverOutputGenerator, component: SemverComponentType) -> None:
    entry = GitEntry(commit_hash='abc123', subject='feat: x')
    entry.semver_change = component
    generator.handle_commit_entry(entry)


@fact
@trait('mock')
def generator_starts_at_config_baseline() -> None:
    generator = _make_generator(1, 2, 3)
    with patch('builtins.print') as mock_print:
        generator.generate_output()
    assert mock_print.called_with('1.2.3'), '(expected print to be called with 1.2.3)'


@fact
@trait('mock')
def major_bump_increments_major_and_resets_lower() -> None:
    generator = _make_generator(1, 2, 3)
    _bump(generator, SemverComponentType.MAJOR)
    with patch('builtins.print') as mock_print:
        generator.generate_output()
    assert mock_print.called_with('2.0.0'), '(expected print to be called with 2.0.0)'


@fact
@trait('mock')
def minor_bump_increments_minor_and_resets_patch() -> None:
    generator = _make_generator(1, 2, 3)
    _bump(generator, SemverComponentType.MINOR)
    with patch('builtins.print') as mock_print:
        generator.generate_output()
    assert mock_print.called_with('1.3.0'), '(expected print to be called with 1.3.0)'


@fact
@trait('mock')
def patch_bump_increments_patch_only() -> None:
    generator = _make_generator(1, 2, 3)
    _bump(generator, SemverComponentType.PATCH)
    with patch('builtins.print') as mock_print:
        generator.generate_output()
    assert mock_print.called_with('1.2.4'), '(expected print to be called with 1.2.4)'


@fact
@trait('mock')
def none_bump_is_a_noop() -> None:
    generator = _make_generator(1, 2, 3)
    _bump(generator, SemverComponentType.NONE)
    with patch('builtins.print') as mock_print:
        generator.generate_output()
    assert mock_print.called_with('1.2.3'), '(expected print to be called with 1.2.3)'


@fact
@trait('mock')
def empty_entry_is_ignored() -> None:
    generator = _make_generator(1, 2, 3)
    generator.handle_commit_entry(GitEntry())
    with patch('builtins.print') as mock_print:
        generator.generate_output()
    assert mock_print.called_with('1.2.3'), '(expected print to be called with 1.2.3)'


@fact
@trait('mock')
def mixed_bumps_accumulate() -> None:
    generator = _make_generator(0, 0, 0)
    _bump(generator, SemverComponentType.MINOR)
    _bump(generator, SemverComponentType.PATCH)
    _bump(generator, SemverComponentType.MAJOR)
    _bump(generator, SemverComponentType.PATCH)
    with patch('builtins.print') as mock_print:
        generator.generate_output()
    assert mock_print.called_with('1.0.1'), '(expected print to be called with 1.0.1)'


@fact
@trait('mock')
def none_semver_change_defaults_on_entry() -> None:
    generator = _make_generator()
    entry = GitEntry(commit_hash='abc123', subject='feat: x')
    generator.handle_commit_entry(entry)
    with patch('builtins.print') as mock_print:
        generator.generate_output()
    assert mock_print.called_with('0.0.0'), '(expected print to be called with 0.0.0)'
