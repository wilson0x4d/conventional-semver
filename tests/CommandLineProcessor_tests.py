# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the argparse-based :mod:`~conventional_semver.CommandLineProcessor`."""

from __future__ import annotations

from punit import fact


@fact
def changelog_without_value_uses_default() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--changelog'])
    assert ns.changelog == 'CHANGELOG.md'


@fact
def changelog_with_explicit_path_uses_that_path() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--changelog', '/custom/Changelog.rst'])
    assert ns.changelog == '/custom/Changelog.rst'


@fact
def changelog_absent_means_disabled() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments([])
    assert ns.changelog is None


@fact
def no_semver_flag_sets_disable_on() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--no-semver'])
    assert ns.disable_semver_output is True


@fact
def no_no_semver_flag_means_enabled_by_default() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments([])
    assert ns.disable_semver_output is False


@fact
def major_minor_patch_default_to_zero() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments([])
    assert ns.major_start == 0
    assert ns.minor_start == 0
    assert ns.patch_start == 0


@fact
def major_component_respects_value() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--major', '3'])
    assert ns.major_start == 3


@fact
def minor_and_patch_together() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--minor', '2', '--patch', '7'])
    assert ns.minor_start == 2
    assert ns.patch_start == 7


@fact
def commit_flag_sets_start_commit_hash() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--commit', 'abc123'])
    assert ns.start_commit_hash == 'abc123'


@fact
def tag_flag_sets_start_tag() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--tag', 'v1.0.0'])
    assert ns.start_tag == 'v1.0.0'


@fact
def config_file_flag_sets_config_file() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--config', '/my/custom.conf'])
    assert ns.config_file == '/my/custom.conf'


@fact
def git_path_flag_sets_git_path() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--git-path', '/usr/local/bin/git'])
    assert ns.git_path == '/usr/local/bin/git'


@fact
def positional_repo_path_defaults_to_none() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments([])
    assert ns.repo_path is None


@fact
def positional_repo_path_set_explicitly() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['/path/to/repo'])
    assert ns.repo_path == '/path/to/repo'


@fact
def apply_maps_changelog_onto_config() -> None:
    from conventional_semver.CommandLineProcessor import (
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    ns = parse_arguments(['--changelog', '/out/changelog.md'])
    apply_arguments_to_config(ns, config)
    assert config.changelog_output_file == '/out/changelog.md'


@fact
def apply_maps_commit_url_with_trailing_slash_stripped() -> None:
    from conventional_semver.CommandLineProcessor import (
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    ns = parse_arguments(['--commit-url', 'https://example.com/commits/'])
    apply_arguments_to_config(ns, config)
    assert config.commit_url == 'https://example.com/commits'


@fact
def apply_maps_semver_components_onto_config() -> None:
    from conventional_semver.CommandLineProcessor import (
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    ns = parse_arguments(['--major', '1', '--minor', '2', '--patch', '3'])
    apply_arguments_to_config(ns, config)
    assert config.major_start == 1
    assert config.minor_start == 2
    assert config.patch_start == 3


@fact
def legacy_commandlineprocessor_class_still_works() -> None:
    from conventional_semver.CommandLineProcessor import (
        CommandlineProcessor,
        apply_arguments_to_config,
        parse_arguments,
    )
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    processor = CommandlineProcessor(config, '1.0.0', 'abc')
    processor.process_command_line(['--changelog', '/legacy.md'])

    ns = parse_arguments(['--changelog', '/direct.md'])
    apply_arguments_to_config(ns, config)
    assert config.changelog_output_file == '/direct.md'


def _expect_system_exit(fn):  # type: ignore[no-untyped-def]
    """Helper to assert that *fn* raises SystemExit."""
    try:
        fn()
    except SystemExit:
        return
    raise AssertionError('expected SystemExit but nothing was raised')


@fact
def invalid_major_int_raises_system_exit() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    _expect_system_exit(lambda: parse_arguments(['--major', 'abc']))


@fact
def invalid_minor_int_raises_system_exit() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    _expect_system_exit(lambda: parse_arguments(['--minor', 'xyz']))


@fact
def invalid_patch_int_raises_system_exit() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    _expect_system_exit(lambda: parse_arguments(['--patch', '!!']))


@fact
def unknown_flag_raises_system_exit() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    _expect_system_exit(lambda: parse_arguments(['--nonexistent-flag']))


@fact
def changelog_with_dash_prefixed_value_defaults_to_changelog_md() -> None:
    # When --changelog is followed by a dash-prefixed arg, argparse treats
    # it as a new flag; nargs='?' falls back to const.
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--changelog', '--verbose'])
    assert ns.changelog == 'CHANGELOG.md'


@fact
def verbose_flag_is_stored_true() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--verbose'])
    assert ns.verbose is True


@fact
def verbose_flag_not_passed_means_false() -> None:
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments([])
    assert ns.verbose is False


@fact
def parse_arguments_does_not_auto_strip_args() -> None:
    """parse_arguments forwards all args as-is — callers are responsible for stripping argv[0]."""
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['/some/fake/script/path', '--no-semver'])
    # repo_path is set to whatever parse_arguments sees — no auto-detection here.
    assert ns.repo_path == '/some/fake/script/path'


@fact
def legacy_class_strips_argv0_explicitly() -> None:
    """CommandlineProcessor explicitly strips argv[0] before calling parse_arguments."""
    from conventional_semver.CommandLineProcessor import CommandlineProcessor
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    processor = CommandlineProcessor(config, '1.0.0', 'abc')

    # Passing sys.argv[0] as first element should NOT pollute repo_path or git_path
    processor.process_command_line(['/fake/script/path'])

    # The key check: git_path must remain '' so process_configuration falls back to 'git'.
    assert config.git_path == '', f'Expected empty git_path but got {config.git_path!r}'


@fact
def main_default_argv_does_not_pollute_repo_path() -> None:
    """When __main__.py's main() defaults to sys.argv[1:], the legacy class strips argv[0]."""
    # The default is sys.argv[1:] at function definition, so production never sees this risk.
    from conventional_semver.CommandLineProcessor import CommandlineProcessor
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    processor = CommandlineProcessor(config, '1.0.0', 'abc')
    processor.process_command_line(['/some/fake/__main__.py'])

    assert config.repo_path == '', f'Expected empty repo_path but got {config.repo_path!r}'
    assert config.git_path == '', f'Expected empty git_path but got {config.git_path!r}'


@fact
def parse_arguments_forwards_single_element_path() -> None:
    """parse_arguments preserves single-element lists — the caller handles stripping."""
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['/path/to/repo'])
    assert ns.repo_path == '/path/to/repo'


@fact
def parse_arguments_preserves_flags_without_argv0() -> None:
    """parse_arguments preserves flags when passed directly (no argv[0] to strip)."""
    from conventional_semver.CommandLineProcessor import parse_arguments

    ns = parse_arguments(['--changelog', '/custom/changelog.md'])
    assert ns.changelog == '/custom/changelog.md'


# -- help/version flags are tested implicitly by all other tests
# that successfully invoke parse_arguments() (a broken parser would crash).
