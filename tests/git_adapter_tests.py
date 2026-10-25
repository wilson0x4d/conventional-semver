# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :class:`~conventional_semver.git_adapter` class."""

import re

from punit import fact, raises, trait
from punit.mocks import Mock, patch

from conventional_semver.configuration import Configuration
from conventional_semver.git_adapter import GitAdapter
from conventional_semver.git_entry import GitEntry
from conventional_semver.git_entry_parser import GitEntryParser
from conventional_semver.output_generator import OutputGenerator
from conventional_semver.semver_component_type import SemverComponentType

HASH_1 = 'aaaa1111' + '0' * 32
HASH_2 = 'bbbb2222' + '1' * 32

TWO_ENTRIES = (
    f'{HASH_1}\n\nfeat: first\n\n'.encode('utf-8') + b'\xef\n'
    + f'{HASH_2}\n\nfix: second\n\n'.encode('utf-8') + b'\xef\n'
)


class _RecordingGenerator(OutputGenerator):
    """Test double that records every entry it receives."""

    entries: list[GitEntry]

    def __init__(self) -> None:
        self.entries = []

    def handle_commit_entry(self, entry: GitEntry) -> None:
        self.entries.append(entry)

    def generate_output(self) -> None:
        pass


def _config() -> Configuration:
    config = Configuration()
    config.repo_path = '/tmp'
    config.git_path = 'git'
    config.types = [
        (re.compile(r'^feat.*:[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.MINOR),
        (re.compile(r'^fix.*:[\S\s]*', re.MULTILINE | re.IGNORECASE), SemverComponentType.PATCH),
    ]
    return config


def _mocked_proc(stdout: bytes, stderr: bytes = b'', returncode: int = 0) -> Mock:
    proc = Mock()
    proc.communicate.returns((stdout, stderr))
    proc.returncode = returncode
    return proc


@fact
@trait('mock')
def process_git_log_feeds_generators_and_sink() -> None:
    config = _config()
    generator = _RecordingGenerator()
    adapter = GitAdapter(
        config,
        GitEntryParser(),
        [generator],
        semver_change_callback=Configuration.compute_semver_change,
    )
    sink: list[GitEntry] = []

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_mocked_proc(TWO_ENTRIES))
        adapter.process_git_log(entry_sink=sink)

    assert len(generator.entries) == 2, f'(expected=2, actual={len(generator.entries)})'
    assert generator.entries[0].commit_hash == HASH_1, f"(expected={HASH_1!r}, actual={generator.entries[0].commit_hash!r})"
    assert generator.entries[1].commit_hash == HASH_2, f"(expected={HASH_2!r}, actual={generator.entries[1].commit_hash!r})"
    assert generator.entries[0].semver_change is SemverComponentType.MINOR, f'(actual={generator.entries[0].semver_change!r})'
    assert generator.entries[1].semver_change is SemverComponentType.PATCH, f'(actual={generator.entries[1].semver_change!r})'
    assert len(sink) == 2, f'(expected=2, actual={len(sink)})'
    assert sink[0] is generator.entries[0], '(expected the same entry instances in the sink)'


@fact
@trait('mock')
def process_git_log_without_callback_leaves_semver_change_unset() -> None:
    config = _config()
    generator = _RecordingGenerator()
    adapter = GitAdapter(config, GitEntryParser(), [generator])

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_mocked_proc(TWO_ENTRIES))
        adapter.process_git_log()

    assert len(generator.entries) == 2, f'(expected=2, actual={len(generator.entries)})'
    assert generator.entries[0].semver_change is SemverComponentType.NONE, f'(actual={generator.entries[0].semver_change!r})'


@fact
@trait('mock')
def process_git_log_ignores_generators_added_after_construction() -> None:
    config = _config()
    generator = _RecordingGenerator()
    late_generator = _RecordingGenerator()
    generators = [generator, late_generator]
    # The adapter copies the list at construction; simulate the copy by
    # dropping the late generator from the *outer* list after construction.
    adapter = GitAdapter(config, GitEntryParser(), generators[:1])
    del generators

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_mocked_proc(TWO_ENTRIES))
        adapter.process_git_log()

    assert len(generator.entries) == 2, f'(expected=2, actual={len(generator.entries)})'
    assert len(late_generator.entries) == 0, f'(expected=0, actual={len(late_generator.entries)})'


@fact
@trait('mock')
def process_git_log_without_sink_is_fine() -> None:
    config = _config()
    generator = _RecordingGenerator()
    adapter = GitAdapter(config, GitEntryParser(), [generator])

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_mocked_proc(TWO_ENTRIES))
        adapter.process_git_log()

    assert len(generator.entries) == 2, f'(expected=2, actual={len(generator.entries)})'


@fact
@trait('mock')
def popen_failure_raises_runtime_error() -> None:
    config = _config()
    adapter = GitAdapter(config, GitEntryParser(), [])

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.side_effect(OSError('git not found'))
        assert raises[RuntimeError](adapter.process_git_log), '(expected RuntimeError)'


@fact
@trait('mock')
def stderr_bytes_are_forwarded_without_breaking_entries() -> None:
    config = _config()
    generator = _RecordingGenerator()
    adapter = GitAdapter(config, GitEntryParser(), [generator])

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_mocked_proc(TWO_ENTRIES, stderr=b'warning: something'))
        adapter.process_git_log()

    assert len(generator.entries) == 2, f'(expected=2, actual={len(generator.entries)})'


@fact
@trait('mock')
def process_git_log_with_start_tag_constrains_log_range() -> None:
    config = _config()
    config.start_tag = 'v1.0.0'
    adapter = GitAdapter(config, GitEntryParser(), [])

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_mocked_proc(b''))
        adapter.process_git_log()

    argv = mock_popen.all_calls[0].args[0]
    assert 'v1.0.0..' in argv, f"(expected 'v1.0.0..' in argv, actual={argv!r})"


@fact
@trait('mock')
def process_git_log_with_start_commit_hash_constrains_log_range() -> None:
    config = _config()
    config.start_commit_hash = 'abc1234'
    adapter = GitAdapter(config, GitEntryParser(), [])

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_mocked_proc(b''))
        adapter.process_git_log()

    argv = mock_popen.all_calls[0].args[0]
    assert 'abc1234..' in argv, f"(expected 'abc1234..' in argv, actual={argv!r})"


@fact
@trait('mock')
def process_git_log_start_tag_takes_precedence_over_commit_hash() -> None:
    config = _config()
    config.start_tag = 'v1.0.0'
    config.start_commit_hash = 'abc1234'
    adapter = GitAdapter(config, GitEntryParser(), [])

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_mocked_proc(b''))
        adapter.process_git_log()

    argv = mock_popen.all_calls[0].args[0]
    assert 'v1.0.0..' in argv, f"(expected 'v1.0.0..' in argv, actual={argv!r})"
    assert 'abc1234..' not in argv, f"(expected 'abc1234..' not in argv, actual={argv!r})"


@fact
@trait('integration')
def process_git_log_parses_every_record_with_full_hashes() -> None:
    """Regression guard: run the real pipeline against this repository and
    require one entry per ``git log`` record, each with an intact 40-char
    hash (delimiter handling must consume exactly 0xEF plus its newline)."""
    import subprocess
    from pathlib import Path

    config = _config()
    config.repo_path = str(Path(__file__).resolve().parents[1])
    adapter = GitAdapter(config, GitEntryParser(), [])
    sink: list[GitEntry] = []
    adapter.process_git_log(entry_sink=sink)

    expected = subprocess.run(
        ['git', 'log', '--format=%H'],
        capture_output=True,
        text=True,
        check=True,
        cwd=config.repo_path,
    ).stdout.splitlines()
    assert len(sink) == len(expected), f'(expected={len(expected)}, actual={len(sink)})'
    for entry in sink:
        assert len(entry.commit_hash) == 40, f'(expected=40 chars, actual={entry.commit_hash!r})'
        assert entry.commit_hash in expected, f"(expected one of the git log hashes, actual={entry.commit_hash!r})"


@fact
@trait('mock')
def empty_git_output_yields_no_entries() -> None:
    config = _config()
    generator = _RecordingGenerator()
    adapter = GitAdapter(config, GitEntryParser(), [generator])

    with patch('conventional_semver.git_adapter.subprocess.Popen') as mock_popen:
        mock_popen.returns(_mocked_proc(b''))
        adapter.process_git_log()

    assert generator.entries == [], f"(expected=[], actual={generator.entries!r})"
