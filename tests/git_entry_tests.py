# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :class:`~conventional_semver.git_entry` class."""

from punit import fact

from conventional_semver.git_entry import GitEntry
from conventional_semver.semver_component_type import SemverComponentType


@fact
def extract_type_from_scopeful_commit() -> None:
    entry = GitEntry(subject='feat(cli): add help command')
    assert entry.extract_type() == 'feat', f"(expected='feat', actual={entry.extract_type()!r})"


@fact
def extract_type_from_scopeless_commit() -> None:
    entry = GitEntry(subject='fix: resolve crash')
    assert entry.extract_type() == 'fix', f"(expected='fix', actual={entry.extract_type()!r})"


@fact
def extract_type_from_breaking_change() -> None:
    entry = GitEntry(subject='feat!: drop python 3.8 support')
    assert entry.extract_type() == 'feat', f"(expected='feat', actual={entry.extract_type()!r})"


@fact
def extract_type_from_non_conventional() -> None:
    entry = GitEntry(subject='just some random message')
    assert entry.extract_type() == '', f"(expected='', actual={entry.extract_type()!r})"


@fact
def extract_type_from_subject_with_space_before_scope() -> None:
    entry = GitEntry(subject='fix (core): hot fix')
    assert entry.extract_type() == '', f"(expected='', actual={entry.extract_type()!r})"


@fact
def extract_scope_when_present() -> None:
    entry = GitEntry(subject='fix(core): hot fix')
    assert entry.extract_scope() == 'core', f"(expected='core', actual={entry.extract_scope()!r})"


@fact
def extract_scope_when_absent() -> None:
    entry = GitEntry(subject='chore: update deps')
    assert entry.extract_scope() == '', f"(expected='', actual={entry.extract_scope()!r})"


@fact
def extract_scope_from_non_conventional() -> None:
    entry = GitEntry(subject='no type here')
    assert entry.extract_scope() == '', f"(expected='', actual={entry.extract_scope()!r})"


@fact
def extract_header_strips_whitespace() -> None:
    entry = GitEntry(subject='feat(cli):   add help command  ')
    assert entry.extract_header() == 'add help command', f"(expected='add help command', actual={entry.extract_header()!r})"


@fact
def extract_header_when_absent() -> None:
    entry = GitEntry(subject='fix: ')
    assert entry.extract_header() == '', f"(expected='', actual={entry.extract_header()!r})"


@fact
def extract_header_from_non_conventional() -> None:
    entry = GitEntry(subject='random text')
    assert entry.extract_header() == '', f"(expected='', actual={entry.extract_header()!r})"


@fact
def defaults_are_empty_and_none() -> None:
    entry = GitEntry()
    assert entry.commit_hash == '', f"(expected='', actual={entry.commit_hash!r})"
    assert entry.body == '', f"(expected='', actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"
    assert entry.refs == [], f"(expected=[], actual={entry.refs!r})"
    assert entry.subject == '', f"(expected='', actual={entry.subject!r})"
    assert entry.commit_date == '', f"(expected='', actual={entry.commit_date!r})"
    assert entry.semver == '', f"(expected='', actual={entry.semver!r})"
    assert entry.semver_change is SemverComponentType.NONE, f'(actual={entry.semver_change!r})'


@fact
def provided_footers_and_refs_are_retained() -> None:
    entry = GitEntry(footers=['a: b'], refs=['tag: v1.0.0'])
    assert entry.footers == ['a: b'], f"(expected=['a: b'], actual={entry.footers!r})"
    assert entry.refs == ['tag: v1.0.0'], f"(expected=['tag: v1.0.0'], actual={entry.refs!r})"


@fact
def empty_entry_reports_empty() -> None:
    assert GitEntry().is_empty() is True, '(expected=True, actual=False)'


@fact
def entry_with_hash_is_not_empty() -> None:
    assert GitEntry(commit_hash='abc').is_empty() is False, '(expected=False, actual=True)'


@fact
def entry_with_subject_is_not_empty() -> None:
    assert GitEntry(subject='feat: x').is_empty() is False, '(expected=False, actual=True)'


@fact
def entry_with_body_is_not_empty() -> None:
    assert GitEntry(body='some body').is_empty() is False, '(expected=False, actual=True)'


@fact
def entry_with_footers_is_not_empty() -> None:
    assert GitEntry(footers=['BREAKING-CHANGE: yes']).is_empty() is False, '(expected=False, actual=True)'


@fact
def entry_with_refs_is_not_empty() -> None:
    assert GitEntry(refs=['HEAD -> main']).is_empty() is False, '(expected=False, actual=True)'


@fact
def str_of_empty_entry_is_empty() -> None:
    assert str(GitEntry()) == '', f"(expected='', actual={str(GitEntry())!r})"


@fact
def str_of_minimal_entry_contains_hash_and_subject() -> None:
    entry = GitEntry(commit_hash='abc123', subject='feat: x')
    result = str(entry)
    assert 'abc123' in result, f"(expected 'abc123' in, actual={result!r})"
    assert 'feat: x' in result, f"(expected 'feat: x' in, actual={result!r})"


@fact
def str_of_full_entry_contains_refs_body_and_footers() -> None:
    entry = GitEntry(
        commit_hash='abc123',
        refs=['tag: v1.0.0', 'HEAD -> main'],
        subject='feat: x',
        body='body text',
        footers=['Co-Authored-By: A', 'Ref: 1'],
    )
    result = str(entry)
    assert 'tag: v1.0.0, HEAD -> main' in result, f"(expected refs in, actual={result!r})"
    assert 'body text' in result, f"(expected body in, actual={result!r})"
    assert 'Co-Authored-By: A,Ref: 1' in result, f"(expected footers in, actual={result!r})"
