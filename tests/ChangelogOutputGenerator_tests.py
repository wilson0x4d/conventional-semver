# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

from punit import fact


@fact
def gitentry_extract_type_from_scopeful_commit() -> None:
    from conventional_semver.GitEntry import GitEntry

    entry = GitEntry(subject='feat(cli): add help command')
    assert entry._extract_type() == 'feat'


@fact
def gitentry_extract_type_from_scopeless_commit() -> None:
    from conventional_semver.GitEntry import GitEntry

    entry = GitEntry(subject='fix: resolve crash')
    assert entry._extract_type() == 'fix'


@fact
def gitentry_extract_type_from_breaking_change() -> None:
    from conventional_semver.GitEntry import GitEntry

    entry = GitEntry(subject='feat!: drop python 3.8 support')
    assert entry._extract_type() == 'feat'


@fact
def gitentry_extract_scope_when_present() -> None:
    from conventional_semver.GitEntry import GitEntry

    entry = GitEntry(subject='fix(core): hot fix')
    assert entry._extract_scope() == 'core'


@fact
def gitentry_extract_scope_when_absent() -> None:
    from conventional_semver.GitEntry import GitEntry

    entry = GitEntry(subject='chore: update deps')
    assert entry._extract_scope() == ''


@fact
def gitentry_extract_header_strips_whitespace() -> None:
    from conventional_semver.GitEntry import GitEntry

    entry = GitEntry(subject='feat(cli):   add help command  ')
    assert entry._extract_header() == 'add help command'


@fact
def gitentry_extract_type_from_non_conventional() -> None:
    from conventional_semver.GitEntry import GitEntry

    entry = GitEntry(subject='just some random message')
    assert entry._extract_type() == ''


@fact
def handles_empty_entry_as_noop() -> None:
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration
    from conventional_semver.GitEntry import GitEntry

    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    empty_entry = GitEntry()
    generator.handle_commit_entry(empty_entry)

    assert len(generator._version_groups) == 0


@fact
def single_patch_commit_creates_group() -> None:
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration
    from conventional_semver.GitEntry import GitEntry
    from conventional_semver.SemverComponentType import SemverComponentType

    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    entry = GitEntry(commit_hash='aabbccdd1234', subject='fix: patch one')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    assert len(generator._version_groups) == 1
    assert generator._version_groups[0]['semver'] == '0.0.1'
    assert len(generator._version_groups[0]['commits']) == 1


@fact
def each_unique_semver_gets_its_own_group() -> None:
    """Three PATCH commits produce three distinct semver values (0.0.1, 0.0.2, 0.0.3),
    each in its own group with one commit."""
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration
    from conventional_semver.GitEntry import GitEntry
    from conventional_semver.SemverComponentType import SemverComponentType

    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    for i in range(3):
        entry = GitEntry(commit_hash=f'hash{i:04d}', subject='fix: patch fix')
        entry.semver_change = SemverComponentType.PATCH
        generator.handle_commit_entry(entry)

    assert len(generator._version_groups) == 3
    assert generator._version_groups[2]['semver'] == '0.0.1'
    assert len(generator._version_groups[0]['commits']) == 1
    assert generator._version_groups[1]['semver'] == '0.0.2'
    assert len(generator._version_groups[1]['commits']) == 1
    assert generator._version_groups[0]['semver'] == '0.0.3'
    assert len(generator._version_groups[2]['commits']) == 1


@fact
def minor_change_creates_distinct_group() -> None:
    """Two PATCH commits (0.0.1, 0.0.2) then one MINOR (0.1.0) → three distinct groups."""
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration
    from conventional_semver.GitEntry import GitEntry
    from conventional_semver.SemverComponentType import SemverComponentType

    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    for _ in range(2):
        entry = GitEntry(commit_hash='p1', subject='fix: patch')
        entry.semver_change = SemverComponentType.PATCH
        generator.handle_commit_entry(entry)

    assert len(generator._version_groups) == 2

    minor_entry = GitEntry(commit_hash='m1', subject='feat: new feature')
    minor_entry.semver_change = SemverComponentType.MINOR
    generator.handle_commit_entry(minor_entry)

    assert len(generator._version_groups) == 3
    assert generator._version_groups[2]['semver'] == '0.0.1'
    assert generator._version_groups[1]['semver'] == '0.0.2'
    assert generator._version_groups[0]['semver'] == '0.1.0'


@fact
def commit_dict_contains_extracted_fields() -> None:
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration
    from conventional_semver.GitEntry import GitEntry

    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    entry = GitEntry(
        commit_hash='abcdef1234567890',
        subject='feat(cli): add help command',
        body='Some description.',
        footers=['Co-Authored-By: Alice'],
    )
    generator.handle_commit_entry(entry)

    commit = generator._version_groups[0]['commits'][0]
    assert commit['hash'] == 'abcdef1234567890'[:7]
    assert commit['type'] == 'feat'
    assert commit['scope'] == 'cli'
    assert commit['header'] == 'add help command'
    assert commit['body'] == 'Some description.'
    assert 'Co-Authored-By: Alice' in commit['footers']


@fact
def set_changelog_template_propagates_path() -> None:
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration

    config = Configuration()
    generator = ChangelogOutputGenerator(config)
    assert generator._changelog_template_path is None

    generator.set_changelog_template('/custom/template.j2')
    assert generator._changelog_template_path == '/custom/template.j2'


@fact
def resolve_date_finds_matching_hash() -> None:
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator

    dates = {
        'abcdef1234567890': '2026-01-15',
        '1111112222333344': '2026-02-20',
    }

    result = ChangelogOutputGenerator._resolve_date('abcdef1234567890'[:7], dates)
    assert result == '2026-01-15'


@fact
def resolve_date_falls_back_to_unknown() -> None:
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator

    dates = {
        'abcdef1234567890': '2026-01-15',
    }

    result = ChangelogOutputGenerator._resolve_date('deadbeef123456'[:7], dates)
    assert result == 'unknown'


@fact
def major_change_resets_minor_and_patch() -> None:
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration
    from conventional_semver.GitEntry import GitEntry
    from conventional_semver.SemverComponentType import SemverComponentType

    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    for _ in range(2):
        entry = GitEntry(commit_hash='x', subject='fix: fix')
        entry.semver_change = SemverComponentType.PATCH
        generator.handle_commit_entry(entry)

    assert generator._version_groups[0]['semver'] == '0.0.2'

    minor_entry = GitEntry(commit_hash='m1', subject='feat: new thing')
    minor_entry.semver_change = SemverComponentType.MINOR
    generator.handle_commit_entry(minor_entry)
    assert generator._version_groups[0]['semver'] == '0.1.0'

    # Major change via footer (BREAKING CHANGE) → resets minor and patch to 0
    break_entry = GitEntry(
        commit_hash='b1',
        subject='feat: something',
        footers=['BREAKING-CHANGE: major change'],
    )
    break_entry.semver_change = SemverComponentType.MAJOR
    generator.handle_commit_entry(break_entry)

    # The BREAKING CHANGE footer should match the configured footer pattern
    # resulting in a MAJOR change (1.0.0)
    assert generator._version_groups[0]['semver'] == '1.0.0'
    # Minor and patch should be reset to 0
    assert generator._current_semver == (1, 0, 0)


@fact
def commit_url_not_in_version_group_without_flag() -> None:
    """commit_url should not appear in the raw version group before generate_output()."""
    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration
    from conventional_semver.GitEntry import GitEntry
    from conventional_semver.SemverComponentType import SemverComponentType

    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    assert 'commit_url' not in generator._version_groups[0]['commits'][0]


@fact
def commit_url_with_trailing_slash_normalized() -> None:
    """Trailing slash on URL should be normalised by the generator."""

    from punit.mocks import Mock, patch

    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration
    from conventional_semver.GitEntry import GitEntry
    from conventional_semver.SemverComponentType import SemverComponentType

    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)
    config.commit_url = 'https://github.com/org/repo/commit/'
    config.changelog_output_file = '/tmp/test_changelog.md'

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    mock_result = Mock()
    mock_result.stdout = 'abcdef1234567890|2026-01-15\n'

    captured_data = {}

    def capture_generate(data, _template_path):
        nonlocal captured_data
        captured_data = data
        return ''

    mock_instance = Mock()
    mock_instance.generate = capture_generate

    with patch(
        'conventional_semver.ChangelogOutputGenerator.subprocess.run'
    ) as mock_run:
        mock_run.side_effect = lambda *a, **kw: mock_result
        with patch(
            'conventional_semver.ChangelogOutputGenerator.Changelog'
        ) as MockChangelog:
            MockChangelog.side_effect = lambda: mock_instance
            generator.generate_output()

    commits = captured_data.get('versions', [{}])[0].get('commits', [])
    assert len(commits) == 1
    assert commits[0]['commit_url'] == 'https://github.com/org/repo/commit/abcdef1'


@fact
def commit_url_without_trailing_slash_gets_separator() -> None:
    """URL without trailing slash should get a separator inserted."""

    from punit.mocks import Mock, patch

    from conventional_semver.ChangelogOutputGenerator import ChangelogOutputGenerator
    from conventional_semver.Configuration import Configuration
    from conventional_semver.GitEntry import GitEntry
    from conventional_semver.SemverComponentType import SemverComponentType

    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)
    config.commit_url = 'https://github.com/org/repo/commit'
    config.changelog_output_file = '/tmp/test_changelog.md'

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    mock_result = Mock()
    mock_result.stdout = 'abcdef1234567890|2026-01-15\n'

    captured_data = {}

    def capture_generate(data, _template_path):
        nonlocal captured_data
        captured_data = data
        return ''

    mock_instance = Mock()
    mock_instance.generate = capture_generate

    with patch(
        'conventional_semver.ChangelogOutputGenerator.subprocess.run'
    ) as mock_run:
        mock_run.side_effect = lambda *a, **kw: mock_result
        with patch(
            'conventional_semver.ChangelogOutputGenerator.Changelog'
        ) as MockChangelog:
            MockChangelog.side_effect = lambda: mock_instance
            generator.generate_output()

    commits = captured_data.get('versions', [{}])[0].get('commits', [])
    assert len(commits) == 1
    assert commits[0]['commit_url'] == 'https://github.com/org/repo/commit/abcdef1'
