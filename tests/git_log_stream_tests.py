# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :class:`~conventional_semver.git_log_stream` class."""

from punit import fact

from conventional_semver.git_log_stream import GitLogStream
from conventional_semver.git_entry_parser import GitEntryParser

HASH_A = 'aaaa1111' + '0' * 32
HASH_B = 'bbbb2222' + '1' * 32
HASH_C = 'cccc3333' + '2' * 32


@fact
def readentry_on_empty_buffer_returns_empty_entry() -> None:
    stream = GitLogStream(GitEntryParser())
    entry = stream.readentry()
    assert entry.is_empty(), '(expected an empty entry)'


@fact
def single_entry_is_parsed_and_buffer_drained() -> None:
    stream = GitLogStream(GitEntryParser())
    data = f'{HASH_A}\n\nfeat: first\n\n'.encode('utf-8') + b'\xef\n'
    stream.write(data, len(data))

    entry = stream.readentry()
    assert entry.commit_hash == HASH_A, f"(expected={HASH_A!r}, actual={entry.commit_hash!r})"
    assert entry.subject == 'feat: first', f"(expected='feat: first', actual={entry.subject!r})"

    assert stream.readentry().is_empty(), '(expected the buffer to be drained)'


@fact
def consecutive_entries_keep_their_full_hashes() -> None:
    """Each git log record ends with the 0xEF delimiter followed by a
    newline; both bytes must be consumed or the next record's hash is
    corrupted."""
    stream = GitLogStream(GitEntryParser())
    data = (
        f'{HASH_A}\n\nfeat: first\n\n'.encode('utf-8') + b'\xef\n'
        + f'{HASH_B}\ntag: v1.0.0\nfix: second\n\n'.encode('utf-8') + b'\xef\n'
    )
    stream.write(data, len(data))

    first = stream.readentry()
    assert first.commit_hash == HASH_A, f"(expected={HASH_A!r}, actual={first.commit_hash!r})"
    assert first.subject == 'feat: first', f"(expected='feat: first', actual={first.subject!r})"

    second = stream.readentry()
    assert second.commit_hash == HASH_B, f"(expected={HASH_B!r}, actual={second.commit_hash!r})"
    assert second.refs == ['tag: v1.0.0'], f"(expected=['tag: v1.0.0'], actual={second.refs!r})"
    assert second.subject == 'fix: second', f"(expected='fix: second', actual={second.subject!r})"

    assert stream.readentry().is_empty(), '(expected no further entries)'


@fact
def unterminated_block_yields_empty_entry_and_keeps_buffer() -> None:
    stream = GitLogStream(GitEntryParser())
    data = f'{HASH_A}\n\nfeat: x'.encode('utf-8')
    stream.write(data, len(data))

    assert stream.readentry().is_empty(), '(expected an empty entry without a delimiter)'

    stream.write(b'\n\xef', 2)
    entry = stream.readentry()
    assert entry.commit_hash == HASH_A, f"(expected={HASH_A!r}, actual={entry.commit_hash!r})"


@fact
def write_respects_count() -> None:
    stream = GitLogStream(GitEntryParser())
    # Records end with the 0xEF delimiter followed by a tformat newline,
    # exactly as git emits them.
    data = (
        HASH_A.encode('utf-8') + b'\xef\n'
        + HASH_B.encode('utf-8') + b'\xef\n'
    )

    stream.write(data, 4)
    assert stream.readentry().is_empty(), '(expected no entry before the first delimiter arrives)'

    stream.write(data[4:], len(data) - 4)
    first = stream.readentry()
    assert first.commit_hash == HASH_A, f"(expected={HASH_A!r}, actual={first.commit_hash!r})"
    second = stream.readentry()
    assert second.commit_hash == HASH_B, f"(expected={HASH_B!r}, actual={second.commit_hash!r})"


@fact
def invalid_utf8_is_replaced_not_fatal() -> None:
    stream = GitLogStream(GitEntryParser())
    data = f'{HASH_A}\n\nfeat: \xff\xfe\n\xef'.encode('latin-1')
    stream.write(data, len(data))

    entry = stream.readentry()
    assert not entry.is_empty(), '(expected a non-empty entry)'
    assert entry.commit_hash == HASH_A, f"(expected={HASH_A!r}, actual={entry.commit_hash!r})"
    assert entry.subject == 'feat: \ufffd\ufffd', f"(expected='feat: \\ufffd\\ufffd', actual={entry.subject!r})"


@fact
def embedded_delimiter_byte_in_body_is_skipped_without_losing_following_entries() -> None:
    """A raw 0xEF byte smuggled into a commit body desynchronizes the stream;
    the resulting fragment must be rejected as malformed so the next real
    record parses intact."""
    stream = GitLogStream(GitEntryParser())
    data = (
        f'{HASH_A}\n\nfeat: first\n\nbody-part-1'.encode('utf-8') + b'\xef'
        + 'body-part-2\n'.encode('utf-8') + b'\xef\n'
        + f'{HASH_C}\n\nfix: second\n\n'.encode('utf-8') + b'\xef\n'
    )
    stream.write(data, len(data))

    first = stream.readentry()
    assert first.commit_hash == HASH_A, f"(expected={HASH_A!r}, actual={first.commit_hash!r})"
    assert first.subject == 'feat: first', f"(expected='feat: first', actual={first.subject!r})"

    assert stream.readentry().is_empty(), '(expected the desynchronized fragment to be rejected)'

    third = stream.readentry()
    assert third.commit_hash == HASH_C, f"(expected={HASH_C!r}, actual={third.commit_hash!r})"
    assert third.subject == 'fix: second', f"(expected='fix: second', actual={third.subject!r})"

    assert stream.readentry().is_empty(), '(expected no further entries)'
