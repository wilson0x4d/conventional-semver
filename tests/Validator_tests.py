# SPDX-FileCopyrightText: (c) 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :class:`~conventional_semver.Validator` class."""

import re

from punit import fact

from conventional_semver import Validator
from conventional_semver.Configuration import Configuration
from conventional_semver.GitEntry import GitEntry
from conventional_semver.SemverComponentType import SemverComponentType


def _make_restricted_config() -> Configuration:
    """Create a configuration with a restricted set of types for testing.

    Only feat, fix, docs, and chore are valid, matching the format that
    :class:`~conventional_semver.Configuration` produces with its
    ``__build_type_regex`` helper (type + colon + rest of subject).
    """
    config = Configuration()
    config.types = [
        (re.compile(r'^feat.*:[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.MINOR),
        (re.compile(r'^fix.*:[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.PATCH),
        (re.compile(r'^docs.*:[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.PATCH),
        (re.compile(r'^chore.*:[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.PATCH),
    ]
    config.footers = [
        (re.compile(r'[\S\s]*BREAKING[\-\.]CHANGE[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.MAJOR),
    ]
    return config


# -- validate_message tests --


@fact
def valid_conventional_commit_passes() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('feat(cli): add help')

    assert error is None


@fact
def valid_simple_commit_passes() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('fix: resolve crash')

    assert error is None


@fact
def valid_scopeless_commit_passes() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('docs: update readme')

    assert error is None


@fact
def valid_chore_commit_passes() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('chore: update deps')

    assert error is None


@fact
def breaking_change_footer_validates_message() -> None:
    """A commit whose footer matches the BREAKING CHANGE pattern is valid."""
    config = _make_restricted_config()
    v = Validator(config)

    entry = GitEntry(
        subject='feat(api): new endpoint',
        footers=['BREAKING-CHANGE: API is now versioned'],
    )
    error = v._entry_has_unrecognized_type(entry, entry.subject)

    assert error is None


@fact
def unrecognized_type_is_rejected() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('xyz: something unknown')

    assert error is not None
    assert 'Unrecognized commit type' in error
    assert 'xyz: something unknown' in error


@fact
def unknown_type_error_contains_type_name() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('refactor: clean up code')

    assert error is not None
    assert 'refactor' in error
    assert 'refactor: clean up code' in error


@fact
def non_conventional_message_is_rejected() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('just a regular commit message')

    assert error is not None
    assert 'just a regular commit message' in error


# -- Case sensitivity --


@fact
def uppercase_type_is_validated_by_ignore_case_pattern() -> None:
    """Patterns in config use re.IGNORECASE, so uppercase feat should match."""
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('FEAT(api): new endpoint')

    assert error is None


@fact
def mixed_case_type_is_validated_by_ignore_case_pattern() -> None:
    """Mixed-case types still match via re.IGNORECASE in patterns."""
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('Fix: resolve bug')

    assert error is None


# -- validate_log tests --


@fact
def validate_log_all_valid_returns_empty_list() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    entries = [
        GitEntry(subject='feat(cli): add command'),
        GitEntry(subject='fix: resolve typo'),
    ]

    errors = v.validate_log(entries)

    assert errors == []


@fact
def validate_log_one_invalid_returns_single_error() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    entries = [
        GitEntry(subject='feat(cli): add command'),
        GitEntry(subject='xyz: unknown type'),
    ]

    errors = v.validate_log(entries)

    assert len(errors) == 1
    assert 'xyz' in errors[0]


@fact
def validate_log_all_invalid_returns_all_errors() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    entries = [
        GitEntry(subject='xyz: bad one'),
        GitEntry(subject='abc: bad two'),
    ]

    errors = v.validate_log(entries)

    assert len(errors) == 2
    assert 'xyz' in errors[0]
    assert 'abc' in errors[1]


@fact
def validate_log_empty_list_returns_empty_list() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    errors = v.validate_log([])

    assert errors == []


@fact
def validate_log_preserves_order_of_errors() -> None:
    """Errors should be returned in the order entries were processed."""
    config = _make_restricted_config()
    v = Validator(config)

    entries = [
        GitEntry(subject='fix: good'),
        GitEntry(subject='xyz: bad'),
        GitEntry(subject='feat: good'),
        GitEntry(subject='abc: bad'),
    ]

    errors = v.validate_log(entries)

    assert len(errors) == 2
    assert 'xyz' in errors[0]
    assert 'abc' in errors[1]


# -- Integration: main() entry point --


@fact
def main_validate_invalid_message_returns_exit_code_1() -> None:
    """main() should return 1 when --validate receives a message that cannot be parsed."""
    from conventional_semver.__main__ import main

    exit_code = main(['--validate', 'foo bar'])

    assert exit_code == 1


@fact
def main_validate_valid_message_succeeds_in_git_repo() -> None:
    """In a valid git repo with default config, --validate with a valid
    conventional commit message should pass validation and fall through
    to normal semver processing (exit 0).
    """
    from conventional_semver.__main__ import main

    exit_code = main(['--validate', 'feat: test commit'])

    assert exit_code == 0


@fact
def main_validate_f_flag_absent_gives_real_value() -> None:
    """--validate without value gives True, not a string or False."""
    from conventional_semver.CommandLineProcessor import (
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    ns = parse_arguments(['--validate'])
    apply_arguments_to_config(ns, config)

    assert config.validate_message is True  # type: ignore[comparison-overlap]


@fact
def main_validate_flag_with_value_gives_string() -> None:
    """--validate <MESSAGE> gives the message string."""
    from conventional_semver.CommandLineProcessor import (
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    ns = parse_arguments(['--validate', 'feat(cli): test'])
    apply_arguments_to_config(ns, config)

    assert config.validate_message == 'feat(cli): test'


@fact
def main_validate_flag_missing_is_false() -> None:
    """When --validate is absent, config.validate_message is False."""
    from conventional_semver.CommandLineProcessor import (
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    ns = parse_arguments([])
    apply_arguments_to_config(ns, config)

    assert config.validate_message is False


# -- Integration tests --


@fact
def validator_is_exported_from_package() -> None:
    from conventional_semver import Validator as TopLevelValidator

    assert TopLevelValidator is Validator


@fact
def validator_accepts_configuration_object() -> None:
    config = Configuration()
    config.types = []
    config.footers = []
    v = Validator(config)

    assert isinstance(v, Validator)


@fact
def configuration_validate_message_defaults_to_false() -> None:
    config = Configuration()

    assert config.validate_message is False


@fact
def configuration_validate_message_accepts_string() -> None:
    from conventional_semver.CommandLineProcessor import (
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    ns = parse_arguments(['--validate', 'feat: new thing'])
    apply_arguments_to_config(ns, config)

    assert config.validate_message == 'feat: new thing'


@fact
def configuration_validate_message_set_true_when_flag_absent_value() -> None:
    from conventional_semver.CommandLineProcessor import (
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    ns = parse_arguments(['--validate'])
    apply_arguments_to_config(ns, config)

    assert config.validate_message is True  # type: ignore[comparison-overlap]


@fact
def configuration_validate_message_defaults_false_when_flag_not_passed() -> None:
    from conventional_semver.CommandLineProcessor import (
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    ns = parse_arguments([])
    apply_arguments_to_config(ns, config)

    assert config.validate_message is False


# -- Non-conventional commit error messages --


@fact
def error_message_for_non_conventional_commit() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('Merge branch feature into main')

    assert error is not None
    assert 'Unrecognized commit message' in error
    assert 'Merge branch feature into main' in error


@fact
def error_message_for_unknown_type_includes_type() -> None:
    config = _make_restricted_config()
    v = Validator(config)

    error = v.validate_message('build: update webpack config')

    assert error is not None
    assert 'build' in error
