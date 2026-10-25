# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :class:`~conventional_semver.git_entry_parser` class."""

from punit import fact, inlinedata, theory

from conventional_semver.git_entry_parser import GitEntryParser

HASH_A = 'aaaa1111' + '0' * 32
HASH_B = 'bbbb2222' + '1' * 32


@fact
def empty_input_yields_empty_entry() -> None:
    parser = GitEntryParser()
    entry = parser.parse('')
    assert entry.is_empty(), '(expected an empty entry)'


@fact
def hash_only_yields_hash() -> None:
    parser = GitEntryParser()
    entry = parser.parse(HASH_A)
    assert entry.commit_hash == HASH_A, f"(expected={HASH_A!r}, actual={entry.commit_hash!r})"
    assert entry.subject == '', f"(expected='', actual={entry.subject!r})"


@fact
def refs_line_is_parsed() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\ntag: v1.0.0, HEAD -> main\nfeat: x')
    assert entry.refs == ['tag: v1.0.0', 'HEAD -> main'], f"(expected=['tag: v1.0.0', 'HEAD -> main'], actual={entry.refs!r})"
    assert entry.subject == 'feat: x', f"(expected='feat: x', actual={entry.subject!r})"


@fact
def empty_refs_line_yields_no_refs() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x')
    assert entry.refs == [], f"(expected=[], actual={entry.refs!r})"
    assert entry.subject == 'feat: x', f"(expected='feat: x', actual={entry.subject!r})"


@fact
def hash_and_refs_without_subject() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_B}\ntag: v1.0.0')
    assert entry.commit_hash == HASH_B, f"(expected={HASH_B!r}, actual={entry.commit_hash!r})"
    assert entry.refs == ['tag: v1.0.0'], f"(expected=['tag: v1.0.0'], actual={entry.refs!r})"
    assert entry.subject == '', f"(expected='', actual={entry.subject!r})"
    assert entry.body == '', f"(expected='', actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def subject_without_body() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfix: resolve crash')
    assert entry.subject == 'fix: resolve crash', f"(expected='fix: resolve crash', actual={entry.subject!r})"
    assert entry.body == '', f"(expected='', actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def subject_with_multi_line_text_before_blank_line() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nline one\nline two')
    assert entry.subject == 'line one\nline two', f"(expected='line one\\nline two', actual={entry.subject!r})"
    assert entry.body == '', f"(expected='', actual={entry.body!r})"


@fact
def subject_and_body() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nbody line')
    assert entry.subject == 'feat: x', f"(expected='feat: x', actual={entry.subject!r})"
    assert entry.body == 'body line', f"(expected='body line', actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def multi_line_body() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nb1\nb2')
    assert entry.body == 'b1\nb2', f"(expected='b1\\nb2', actual={entry.body!r})"


@fact
def body_leading_blank_line_is_preserved() -> None:
    """A blank line between the subject's separator blank line and the body text belongs to the body."""
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: a thing\n\n\ncommit body\n')
    assert entry.subject == 'feat: a thing', f"(expected='feat: a thing', actual={entry.subject!r})"
    assert entry.body == '\ncommit body', f"(expected='\\ncommit body', actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def body_leading_blank_line_is_preserved_with_footers() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: a thing\n\n\ncommit body\n\nNOTE: x')
    assert entry.body == '\ncommit body', f"(expected='\\ncommit body', actual={entry.body!r})"
    assert entry.footers == ['NOTE: x'], f"(expected=['NOTE: x'], actual={entry.footers!r})"


@fact
def subject_body_and_footers() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nbody\n\nfooter: value\nother: value')
    assert entry.subject == 'feat: x', f"(expected='feat: x', actual={entry.subject!r})"
    assert entry.body == 'body', f"(expected='body', actual={entry.body!r})"
    assert entry.footers == ['footer: value', 'other: value'], f"(expected two footers, actual={entry.footers!r})"


@fact
def trailing_newline_after_body_yields_empty_footers() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nbody\n')
    assert entry.subject == 'feat: x', f"(expected='feat: x', actual={entry.subject!r})"
    assert entry.body == 'body', f"(expected='body', actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def non_footer_lines_after_body_remain_body() -> None:
    """Lines lacking a token/separator pair are not footers, even after a blank line."""
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nbody\n\nf1\n\nf2')
    assert entry.body == 'body\n\nf1\n\nf2', f"(expected='body\\n\\nf1\\n\\nf2', actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def spec_example_multi_paragraph_body_with_two_footers() -> None:
    """A multi-paragraph body whose paragraphs are not valid footers, followed by two valid footer lines."""
    parser = GitEntryParser()
    entry = parser.parse(
        f'{HASH_A}\n\n'
        'feat: something changed\n'
        '\n'
        'this is my commit body\n'
        '\n'
        '**and:** this is also my commit body.\n'
        '\n'
        '\n'
        '**and**: this ALSO is my commit body.\n'
        '\n'
        'NOTE: this is the first footer.\n'
        'Co-authored-by: this is the second footer.'
    )
    assert entry.subject == 'feat: something changed', f"(expected='feat: something changed', actual={entry.subject!r})"
    assert entry.body == (
        'this is my commit body\n\n'
        '**and:** this is also my commit body.\n\n\n'
        '**and**: this ALSO is my commit body.'
    ), f"(actual={entry.body!r})"
    assert entry.footers == [
        'NOTE: this is the first footer.',
        'Co-authored-by: this is the second footer.',
    ], f"(expected two footers, actual={entry.footers!r})"


@fact
def footer_immediately_after_subject_without_body() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfix: crash\n\nBREAKING-CHANGE: removed api')
    assert entry.body == '', f"(expected='', actual={entry.body!r})"
    assert entry.footers == ['BREAKING-CHANGE: removed api'], f"(expected=['BREAKING-CHANGE: removed api'], actual={entry.footers!r})"


@fact
def breaking_change_two_word_token_is_a_footer() -> None:
    """The spec carves out uppercase BREAKING CHANGE as a valid two-word token."""
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nbody\n\nBREAKING CHANGE: the api moved')
    assert entry.body == 'body', f"(expected='body', actual={entry.body!r})"
    assert entry.footers == ['BREAKING CHANGE: the api moved'], f"(expected=['BREAKING CHANGE: the api moved'], actual={entry.footers!r})"


@fact
def lowercase_breaking_change_is_not_a_footer_token() -> None:
    """The spec requires BREAKING CHANGE to be uppercase, so the lowercased form stays body."""
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nbody\n\nbreaking change: the api moved')
    assert entry.body == 'body\n\nbreaking change: the api moved', f"(actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def hash_separator_is_recognized() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfix: x\n\nbody\n\nRefs #123\nCloses #345')
    assert entry.body == 'body', f"(expected='body', actual={entry.body!r})"
    assert entry.footers == ['Refs #123', 'Closes #345'], f"(expected=['Refs #123', 'Closes #345'], actual={entry.footers!r})"


@fact
def colon_without_space_is_not_a_footer_separator() -> None:
    """The spec separators are ':<space>' or '<space>#'; 'token:value' is not a footer."""
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nbody\n\nkey:value')
    assert entry.body == 'body\n\nkey:value', f"(actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def whitespace_in_token_is_not_a_footer() -> None:
    """Tokens must use hyphens in place of whitespace."""
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nbody\n\nsome words: value')
    assert entry.body == 'body\n\nsome words: value', f"(actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def footer_token_line_without_preceding_blank_line_stays_body() -> None:
    """The footer section must appear one blank line after the body."""
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\npara one\nnote: not a footer yet')
    assert entry.body == 'para one\nnote: not a footer yet', f"(actual={entry.body!r})"
    assert entry.footers == [], f"(expected=[], actual={entry.footers!r})"


@fact
def footer_value_continues_until_next_token_pair() -> None:
    """A footer's value spans lines until the next valid token/separator pair is observed."""
    parser = GitEntryParser()
    entry = parser.parse(
        f'{HASH_A}\n\nfeat: x\n\nbody\n\n'
        'NOTE: first line of note\n'
        'second line of note\n'
        '\n'
        'indented continuation\n'
        'Co-authored-by: Jane Doe <jane@example.com>'
    )
    assert entry.body == 'body', f"(expected='body', actual={entry.body!r})"
    assert entry.footers == [
        'NOTE: first line of note\nsecond line of note\n\nindented continuation',
        'Co-authored-by: Jane Doe <jane@example.com>',
    ], f"(expected two footers with a multi-line value, actual={entry.footers!r})"


@fact
def trailing_blank_lines_after_footers_are_stripped() -> None:
    parser = GitEntryParser()
    entry = parser.parse(f'{HASH_A}\n\nfeat: x\n\nbody\n\nRefs: #1\n\n\n')
    assert entry.body == 'body', f"(expected='body', actual={entry.body!r})"
    assert entry.footers == ['Refs: #1'], f"(expected=['Refs: #1'], actual={entry.footers!r})"


# -- commit hash validation --


@fact
def short_hash_yields_empty_entry() -> None:
    parser = GitEntryParser()
    entry = parser.parse('abc123')
    assert entry.is_empty(), '(expected an empty entry for a short hash)'


@fact
def uppercase_hash_yields_empty_entry() -> None:
    """git %H emits lowercase hex; anything else is not a real hash."""
    parser = GitEntryParser()
    entry = parser.parse('A' * 40)
    assert entry.is_empty(), '(expected an empty entry for an uppercase hash)'


@theory
@inlinedata('')
@inlinedata('abc123')
@inlinedata('g' * 40)
@inlinedata('a' * 39)
@inlinedata('a' * 41)
@inlinedata('aaaa1111 \n' + '0' * 32)
def malformed_hash_lines_yield_empty_entries(input_str: str) -> None:
    parser = GitEntryParser()
    entry = parser.parse(input_str)
    assert entry.is_empty(), f"(expected an empty entry for {input_str!r})"


@fact
def full_40_hex_hash_is_accepted() -> None:
    parser = GitEntryParser()
    entry = parser.parse(HASH_A)
    assert not entry.is_empty(), '(expected a non-empty entry for a full 40-char lowercase hex hash)'
    assert entry.commit_hash == HASH_A, f"(expected={HASH_A!r}, actual={entry.commit_hash!r})"
