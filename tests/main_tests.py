# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :func:`main` entry point in :mod:`~conventional_semver.__main__`."""

import os
import sys
import tempfile
from pathlib import Path

from punit import fact, raises, trait
from punit.mocks import Mock, patch

from conventional_semver.__main__ import main

HASH_A = 'aaaa1111' + '0' * 32
HASH_B = 'bbbb2222' + '1' * 32


def _fake_proc(stdout: bytes) -> Mock:
    proc = Mock()
    proc.communicate.returns((stdout, b''))
    proc.returncode = 0
    return proc


@fact
def main_with_no_args_falls_back_to_sys_argv() -> None:
    """main(None) reads sys.argv[1:], so an invalid flag there exits via argparse."""
    old_argv = sys.argv
    sys.argv = ['conventional-semver', '--nonexistent-flag']
    try:
        assert raises[SystemExit](lambda: main(None)), '(expected SystemExit from argparse)'
    finally:
        sys.argv = old_argv


@fact
@trait('mock')
def main_validate_log_reports_invalid_entries() -> None:
    """--validate without a message validates the whole log and fails on unrecognized entries."""
    data = f'{HASH_A}\n\ntotally not conventional\n\n'.encode('utf-8') + b'\xef\n'
    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_fake_proc(data))
        exit_code = main(['--validate'])
    assert exit_code == 1, f'(expected=1, actual={exit_code})'


@fact
@trait('mock')
def main_validate_log_valid_entries_fall_through_to_semver() -> None:
    """A valid log passes validation and continues into normal semver output."""
    data = f'{HASH_A}\n\nfeat: one\n\n'.encode('utf-8') + b'\xef\n'
    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_fake_proc(data))
        with patch('builtins.print') as mock_print:
            exit_code = main(['--validate'])
    assert exit_code == 0, f'(expected=0, actual={exit_code})'
    assert mock_print.called_with('0.1.0'), '(expected print to be called with 0.1.0)'


@fact
@trait('mock')
def main_wires_changelog_generator_when_requested() -> None:
    """--changelog instantiates ChangelogOutputGenerator and runs it alongside the others."""
    data = f'{HASH_B}\n\nfix: one\n\n'.encode('utf-8') + b'\xef\n'
    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_fake_proc(data))
        with patch('conventional_semver.__main__.ChangelogOutputGenerator') as mock_changelog_cls:
            exit_code = main(['--changelog', 'CHANGELOG.md'])
    assert exit_code == 0, f'(expected=0, actual={exit_code})'
    assert mock_changelog_cls.called, '(expected ChangelogOutputGenerator to be instantiated)'
    assert mock_changelog_cls.handle_commit_entry.called, '(expected handle_commit_entry to be invoked)'
    assert mock_changelog_cls.generate_output.called, '(expected generate_output to be invoked)'


@fact
@trait('mock')
def main_wires_custom_changelog_template_when_requested() -> None:
    """--changelog-template propagates to the changelog generator."""
    tmpl_path = Path(tempfile.mkdtemp()) / 'custom.tmpl'
    tmpl_path.write_text('# {{ name }}\n', encoding='utf-8')
    try:
        with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
            mock_popen.returns(_fake_proc(b''))
            with patch('conventional_semver.__main__.ChangelogOutputGenerator') as mock_changelog_cls:
                exit_code = main(['--changelog', 'CHANGELOG.md', '--changelog-template', str(tmpl_path)])
        assert exit_code == 0, f'(expected=0, actual={exit_code})'
        assert mock_changelog_cls.set_changelog_template.called_with(str(tmpl_path)), '(expected set_changelog_template to be invoked)'
    finally:
        os.unlink(str(tmpl_path))


@fact
@trait('mock')
def main_invalid_git_path_reports_error() -> None:
    """A non-executable --git-path surfaces as a clean error and exit code 1."""
    with patch('builtins.print') as mock_print:
        exit_code = main(['--git-path', '/no/such/git'])
    assert exit_code == 1, f'(expected=1, actual={exit_code})'
    assert mock_print.called_with('error: git path "/no/such/git" does not exist'), '(expected the error message to be printed)'


@fact
@trait('mock')
def main_no_semver_flag_skips_semver_generator() -> None:
    """--no-semver prevents SemverOutputGenerator from being created."""
    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_fake_proc(b''))
        with patch('conventional_semver.__main__.SemverOutputGenerator') as mock_semver_cls:
            exit_code = main(['--no-semver'])
    assert exit_code == 0, f'(expected=0, actual={exit_code})'
    assert not mock_semver_cls.called, '(expected SemverOutputGenerator not to be instantiated)'
