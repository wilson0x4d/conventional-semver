# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :class:`~conventional_semver.changelog_output_generator` class."""

from punit import fact, trait

from conventional_semver.changelog_output_generator import ChangelogOutputGenerator
from conventional_semver.configuration import Configuration
from conventional_semver.git_entry import GitEntry
from conventional_semver.semver_component_type import SemverComponentType


@fact
def handles_empty_entry_as_noop() -> None:
    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    generator.handle_commit_entry(GitEntry())

    assert len(generator.version_groups) == 0, f"(expected=0, actual={len(generator.version_groups)})"


@fact
def single_patch_commit_creates_group() -> None:
    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    entry = GitEntry(commit_hash='aabbccdd1234', subject='fix: patch one')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    assert len(generator.version_groups) == 1, f"(expected=1, actual={len(generator.version_groups)})"
    assert generator.version_groups[0]['semver'] == '0.0.1', f"(expected='0.0.1', actual={generator.version_groups[0]['semver']!r})"
    assert len(generator.version_groups[0]['commits']) == 1, f"(expected=1, actual={len(generator.version_groups[0]['commits'])})"


@fact
def each_unique_semver_gets_its_own_group() -> None:
    """Three PATCH commits produce three distinct semver values (0.0.1, 0.0.2, 0.0.3),
    each in its own group with one commit."""
    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    for i in range(3):
        entry = GitEntry(commit_hash=f'hash{i:04d}', subject='fix: patch fix')
        entry.semver_change = SemverComponentType.PATCH
        generator.handle_commit_entry(entry)

    groups = generator.version_groups
    assert len(groups) == 3, f'(expected=3, actual={len(groups)})'
    assert groups[2]['semver'] == '0.0.1', f"(expected='0.0.1', actual={groups[2]['semver']!r})"
    assert len(groups[2]['commits']) == 1, f"(expected=1, actual={len(groups[2]['commits'])})"
    assert groups[1]['semver'] == '0.0.2', f"(expected='0.0.2', actual={groups[1]['semver']!r})"
    assert len(groups[1]['commits']) == 1, f"(expected=1, actual={len(groups[1]['commits'])})"
    assert groups[0]['semver'] == '0.0.3', f"(expected='0.0.3', actual={groups[0]['semver']!r})"
    assert len(groups[0]['commits']) == 1, f"(expected=1, actual={len(groups[0]['commits'])})"


@fact
def consecutive_patch_commits_share_a_group_until_next() -> None:
    """A MINOR bump after patches starts a new group; a following PATCH returns to the minor's line."""
    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    entry = GitEntry(commit_hash='p1', subject='fix: patch')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    minor_entry = GitEntry(commit_hash='m1', subject='feat: new feature')
    minor_entry.semver_change = SemverComponentType.MINOR
    generator.handle_commit_entry(minor_entry)

    entry = GitEntry(commit_hash='p2', subject='fix: another patch')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    groups = generator.version_groups
    assert len(groups) == 3, f'(expected=3, actual={len(groups)})'
    assert groups[0]['semver'] == '0.1.1', f"(expected='0.1.1', actual={groups[0]['semver']!r})"
    assert groups[1]['semver'] == '0.1.0', f"(expected='0.1.0', actual={groups[1]['semver']!r})"
    assert groups[2]['semver'] == '0.0.1', f"(expected='0.0.1', actual={groups[2]['semver']!r})"


@fact
def commit_dict_contains_extracted_fields() -> None:
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

    commit = generator.version_groups[0]['commits'][0]
    assert commit['hash'] == 'abcdef1', f"(expected='abcdef1', actual={commit['hash']!r})"
    assert commit['type'] == 'feat', f"(expected='feat', actual={commit['type']!r})"
    assert commit['scope'] == 'cli', f"(expected='cli', actual={commit['scope']!r})"
    assert commit['header'] == 'add help command', f"(expected='add help command', actual={commit['header']!r})"
    assert commit['body'] == 'Some description.', f"(expected='Some description.', actual={commit['body']!r})"
    assert 'Co-Authored-By: Alice' in commit['footers'], f"(expected footer in, actual={commit['footers']!r})"


@fact
def commit_without_body_or_footers_omits_them() -> None:
    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: something')
    generator.handle_commit_entry(entry)

    commit = generator.version_groups[0]['commits'][0]
    assert 'body' not in commit, f"(expected no 'body' key, actual={commit!r})"
    assert 'footers' not in commit, f"(expected no 'footers' key, actual={commit!r})"


@fact
def set_changelog_template_propagates_path() -> None:
    config = Configuration()
    generator = ChangelogOutputGenerator(config)
    assert generator.changelog_template_path is None, '(expected=None)'

    generator.set_changelog_template('/custom/template.j2')
    assert generator.changelog_template_path == '/custom/template.j2', f"(expected='/custom/template.j2', actual={generator.changelog_template_path!r})"


@fact
def current_semver_tracks_bumps() -> None:
    config = Configuration()
    generator = ChangelogOutputGenerator(config)
    assert generator.current_semver == (0, 0, 0), f"(expected=(0, 0, 0), actual={generator.current_semver!r})"

    entry = GitEntry(commit_hash='h1', subject='fix: a')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)
    assert generator.current_semver == (0, 0, 1), f"(expected=(0, 0, 1), actual={generator.current_semver!r})"

    entry = GitEntry(commit_hash='h2', subject='feat: b')
    entry.semver_change = SemverComponentType.MINOR
    generator.handle_commit_entry(entry)
    assert generator.current_semver == (0, 1, 0), f"(expected=(0, 1, 0), actual={generator.current_semver!r})"


@fact
def resolve_date_finds_exact_match() -> None:
    dates = {
        'abcdef1234567890': '2026-01-15',
        '1111112222333344': '2026-02-20',
    }

    result = ChangelogOutputGenerator.resolve_date('abcdef1234567890', dates)
    assert result == '2026-01-15', f"(expected='2026-01-15', actual={result!r})"


@fact
def resolve_date_falls_back_to_prefix_match() -> None:
    dates = {
        'abcdef1234567890': '2026-01-15',
    }

    result = ChangelogOutputGenerator.resolve_date('abcdef1', dates)
    assert result == '2026-01-15', f"(expected='2026-01-15', actual={result!r})"


@fact
def resolve_date_falls_back_to_unknown() -> None:
    dates = {
        'abcdef1234567890': '2026-01-15',
    }

    result = ChangelogOutputGenerator.resolve_date('deadbee', dates)
    assert result == 'unknown', f"(expected='unknown', actual={result!r})"


@fact
def major_change_resets_minor_and_patch() -> None:
    config = Configuration()
    config.process_configuration()  # populates default type patterns
    generator = ChangelogOutputGenerator(config)

    for _ in range(2):
        entry = GitEntry(commit_hash='x', subject='fix: fix')
        entry.semver_change = SemverComponentType.PATCH
        generator.handle_commit_entry(entry)

    assert generator.version_groups[0]['semver'] == '0.0.2', f"(expected='0.0.2', actual={generator.version_groups[0]['semver']!r})"

    minor_entry = GitEntry(commit_hash='m1', subject='feat: new thing')
    minor_entry.semver_change = SemverComponentType.MINOR
    generator.handle_commit_entry(minor_entry)
    assert generator.version_groups[0]['semver'] == '0.1.0', f"(expected='0.1.0', actual={generator.version_groups[0]['semver']!r})"

    # Major change via footer (BREAKING CHANGE) → resets minor and patch to 0
    break_entry = GitEntry(
        commit_hash='b1',
        subject='feat: something',
        footers=['BREAKING-CHANGE: major change'],
    )
    break_entry.semver_change = SemverComponentType.MAJOR
    generator.handle_commit_entry(break_entry)

    assert generator.version_groups[0]['semver'] == '1.0.0', f"(expected='1.0.0', actual={generator.version_groups[0]['semver']!r})"
    assert generator.current_semver == (1, 0, 0), f"(expected=(1, 0, 0), actual={generator.current_semver!r})"


@fact
def commit_url_not_in_version_group_without_flag() -> None:
    """commit_url should not appear in the raw version group before generate_output()."""
    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    assert 'commit_url' not in generator.version_groups[0]['commits'][0], '(expected no commit_url key)'


def _generate_with_mocked_git_and_changelog(generator: ChangelogOutputGenerator, git_stdout: str) -> dict:
    """Run generate_output() with mocked subprocess.run and Changelog, returning the data dict."""
    from punit.mocks import Mock, patch

    mock_result = Mock()
    mock_result.stdout = git_stdout

    captured: dict = {}

    def capture_generate(data, _template_path):
        captured['data'] = data
        return ''

    mock_instance = Mock()
    mock_instance.generate = capture_generate

    with patch('conventional_semver.changelog_output_generator.subprocess.run') as mock_run:
        mock_run.side_effect = lambda *a, **kw: mock_result
        with patch('conventional_semver.changelog_output_generator.Changelog') as mock_changelog:
            mock_changelog.side_effect = lambda *a, **kw: mock_instance
            generator.generate_output()

    return captured['data']


@fact
@trait('mock')
def commit_url_with_trailing_slash_normalized() -> None:
    """Trailing slash on URL should be normalised by the generator."""
    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)
    config.commit_url = 'https://github.com/org/repo/commit/'
    config.changelog_output_file = '/tmp/test_changelog.md'

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    data = _generate_with_mocked_git_and_changelog(generator, 'abcdef1234567890|2026-01-15\n')

    commits = data.get('versions', [{}])[0].get('commits', [])
    assert len(commits) == 1, f'(expected=1, actual={len(commits)})'
    assert commits[0]['commit_url'] == 'https://github.com/org/repo/commit/abcdef1', f"(expected='https://github.com/org/repo/commit/abcdef1', actual={commits[0]['commit_url']!r})"


@fact
@trait('mock')
def commit_url_without_trailing_slash_gets_separator() -> None:
    """URL without trailing slash should get a separator inserted."""
    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)
    config.commit_url = 'https://github.com/org/repo/commit'
    config.changelog_output_file = '/tmp/test_changelog.md'

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    data = _generate_with_mocked_git_and_changelog(generator, 'abcdef1234567890|2026-01-15\n')

    commits = data.get('versions', [{}])[0].get('commits', [])
    assert len(commits) == 1, f'(expected=1, actual={len(commits)})'
    assert commits[0]['commit_url'] == 'https://github.com/org/repo/commit/abcdef1', f"(expected='https://github.com/org/repo/commit/abcdef1', actual={commits[0]['commit_url']!r})"


@fact
@trait('mock')
def generate_output_data_contains_name_semver_date_and_hash() -> None:
    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)
    config.changelog_output_file = '/tmp/test_changelog.md'

    entry = GitEntry(
        commit_hash='abcdef1234567890',
        subject='fix: test',
        body='The actual fix.',
        footers=['Ref: 1'],
    )
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    data = _generate_with_mocked_git_and_changelog(generator, 'abcdef1234567890abcdef1234|2026-01-15\n')

    assert data['semver'] == '0.0.1', f"(expected='0.0.1', actual={data['semver']!r})"
    assert data['hash'] == 'abcdef1', f"(expected='abcdef1', actual={data['hash']!r})"
    assert 'name' in data, f"(expected 'name' key, actual={data!r})"
    assert 'date' in data, f"(expected 'date' key, actual={data!r})"
    commit = data['versions'][0]['commits'][0]
    assert commit['date'] == '2026-01-15', f"(expected='2026-01-15', actual={commit['date']!r})"
    assert commit['body'] == 'The actual fix.', f"(expected='The actual fix.', actual={commit.get('body')!r})"
    assert commit['footers'] == ['Ref: 1'], f"(expected=['Ref: 1'], actual={commit.get('footers')!r})"


@fact
@trait('mock')
def generate_output_without_commits_uses_unknown_hash() -> None:
    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)
    config.changelog_output_file = '/tmp/test_changelog.md'

    data = _generate_with_mocked_git_and_changelog(generator, '')

    assert data['hash'] == 'unknown', f"(expected='unknown', actual={data['hash']!r})"
    assert data['versions'] == [], f"(expected=[], actual={data['versions']!r})"


@fact
@trait('mock')
def generate_output_survives_git_date_fetch_failure() -> None:
    from punit.mocks import Mock, patch

    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)
    config.changelog_output_file = '/tmp/test_changelog.md'

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    captured: dict = {}

    def capture_generate(data, _template_path):
        captured['data'] = data
        return ''

    mock_instance = Mock()
    mock_instance.generate = capture_generate

    with patch('conventional_semver.changelog_output_generator.subprocess.run') as mock_run:
        mock_run.side_effect = OSError('git unavailable')
        with patch('conventional_semver.changelog_output_generator.Changelog') as mock_changelog:
            mock_changelog.side_effect = lambda *a, **kw: mock_instance
            generator.generate_output()

    commit = captured['data']['versions'][0]['commits'][0]
    assert commit['date'] == 'unknown', f"(expected='unknown', actual={commit['date']!r})"
    assert captured['data']['hash'] == 'abcdef1', f"(expected='abcdef1', actual={captured['data']['hash']!r})"


@fact
@trait('mock')
def generate_output_writes_changelog_file() -> None:
    import tempfile
    from pathlib import Path

    from punit.mocks import Mock, patch

    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)

    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as fh:
        out_path = Path(fh.name)

    config.changelog_output_file = str(out_path)

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    with patch('conventional_semver.changelog_output_generator.subprocess.run') as mock_run:
        mock_run.side_effect = lambda *a, **kw: Mock(stdout='abcdef1234567890|2026-01-15\n')
        generator.generate_output()

    try:
        content = out_path.read_text(encoding='utf-8')
        assert '#### 0.0.1' in content, f"(expected '#### 0.0.1' in, actual={content!r})"
        assert 'fix: test' in content, f"(expected 'fix: test' in, actual={content!r})"
    finally:
        out_path.unlink()


@fact
@trait('mock')
def generate_output_creates_missing_parent_directories() -> None:
    import tempfile
    from pathlib import Path

    from punit.mocks import Mock, patch

    config = Configuration()
    config.process_configuration()
    generator = ChangelogOutputGenerator(config)

    tmp = Path(tempfile.mkdtemp())
    out_path = tmp / 'nested' / 'deeper' / 'CHANGELOG.md'
    config.changelog_output_file = str(out_path)

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    with patch('conventional_semver.changelog_output_generator.subprocess.run') as mock_run:
        mock_run.side_effect = lambda *a, **kw: Mock(stdout='abcdef1234567890|2026-01-15\n')
        generator.generate_output()

    try:
        assert out_path.is_file(), f"(expected {out_path} to exist)"
        content = out_path.read_text(encoding='utf-8')
        assert '#### 0.0.1' in content, f"(expected '#### 0.0.1' in, actual={content!r})"
    finally:
        import shutil
        shutil.rmtree(tmp)


def _capture_changelog_kwargs(config: Configuration) -> dict:
    """Run generate_output() fully mocked and return the Changelog constructor kwargs."""
    from punit.mocks import Mock, patch

    generator = ChangelogOutputGenerator(config)
    config.changelog_output_file = '/tmp/test_changelog.md'

    entry = GitEntry(commit_hash='abcdef1234567890', subject='fix: test')
    entry.semver_change = SemverComponentType.PATCH
    generator.handle_commit_entry(entry)

    captured: dict = {}

    def capture_init(*_args, **kwargs):
        captured['kwargs'] = kwargs
        instance = Mock()
        instance.generate = lambda _data, _template_path: ''
        return instance

    with patch('conventional_semver.changelog_output_generator.subprocess.run') as mock_run:
        mock_run.side_effect = lambda *a, **kw: Mock(stdout='abcdef1234567890|2026-01-15\n')
        with patch('conventional_semver.changelog_output_generator.Changelog') as mock_changelog:
            mock_changelog.side_effect = capture_init
            generator.generate_output()

    return captured['kwargs']


@fact
@trait('mock')
def generate_output_default_mode_uses_full_autoescape() -> None:
    """With no UGC flag set, full autoescape is on."""
    config = Configuration()
    config.process_configuration()

    kwargs = _capture_changelog_kwargs(config)

    assert kwargs == {'autoescape': True}, f"(expected default-mode kwargs, actual={kwargs!r})"


@fact
@trait('mock')
def generate_output_trust_ugc_disables_autoescape() -> None:
    """--trust-ugc disables autoescape of rendered commit content."""
    config = Configuration()
    config.process_configuration()
    config.trust_ugc = True

    kwargs = _capture_changelog_kwargs(config)

    assert kwargs == {'autoescape': False}, f"(expected trust-mode kwargs, actual={kwargs!r})"
