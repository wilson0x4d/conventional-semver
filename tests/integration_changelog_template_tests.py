# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Integration tests exercising the end-to-end ``--changelog-template`` flag
through the CLI entry point.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from punit import fact


# -- repo-local tmp directory (configured in .gitignore) --
_TMP = Path(__file__).resolve().parent.parent / 'tmp'
_TMP.mkdir(exist_ok=True)


# Use the entry-point binary installed in the venv to invoke the CLI via
# the same code path as real users (avoids the
# CommandlineProcessor argv-stripping pitfall).
_CLI = Path(sys.executable).parent / 'conventional-semver'


def _setup_repo(repo: Path) -> None:
    """Initialise *repo* as a git repo with a single conventional commit."""
    subprocess.run(['git', 'init'], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ['git', 'config', 'user.email', 'ci@test.dev'],
        cwd=repo, check=True, capture_output=True,
    )
    subprocess.run(
        ['git', 'config', 'user.name', 'CI Bot'],
        cwd=repo, check=True, capture_output=True,
    )


def _clean_fixture(repo: Path) -> None:
    """Remove any pre-existing fixture directory so the repo starts fresh."""
    if repo.exists():
        for item in repo.iterdir():
            if item.is_dir():
                import shutil
                shutil.rmtree(item)
            else:
                item.unlink()


def _make_commit(repo: Path, subject: str) -> None:
    """Create a conventional commit in *repo*."""
    n = len([x for x in repo.iterdir() if not x.is_dir()])
    (repo / f'file{n}').write_text(str(n))
    subprocess.run(['git', 'add', '.'], cwd=repo, check=True,
                   capture_output=True)
    subprocess.run(
        ['git', 'commit', '-m', subject],
        cwd=repo, check=True, capture_output=True,
    )


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [str(_CLI)] + args
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _fixture_path(name: str, repo: Path | None = None) -> Path:
    """Return a fresh path inside the repo-local tmp dir.

    If *repo* is given the fixture name is prefixed with the resolved repo
    basename so assertions can use ``{repo.name}_{name}``.
    """
    prefix = repo.name if repo is not None else 'x'
    return _TMP / f'{prefix}_{name}'


@fact
def custom_template_is_used_for_rendering() -> None:
    """The custom template content appears in the generated changelog file."""
    repo = _fixture_path('repo')
    tmpl = _fixture_path('custom.j2', repo)
    out = repo / 'CHANGELOG.md'

    _clean_fixture(repo)
    repo.mkdir(parents=True, exist_ok=True)
    _setup_repo(repo)
    _make_commit(repo, 'fix: small bug fix')

    tmpl.write_text(
        '# {{ name }} Custom\n'
        'Semantic Version: {{ semver }}\n'
        '{% for v in versions %}'
        '## {{ v.semver }}\n'
        '{% for c in v.commits %}'
        '- {{ c.type }}({{ c.scope }}): {{ c.header }}\n'
        '{% endfor %}{% endfor %}\n',
        encoding='utf-8',
    )

    result = _run([
        '--changelog', str(out.resolve()),
        '--changelog-template', str(tmpl.resolve()),
        '--no-semver',
        str(repo.resolve()),
    ])
    assert result.returncode == 0, f'stderr: {result.stderr}'
    content = out.read_text(encoding='utf-8')
    assert f'# {repo.name} Custom' in content
    assert 'Semantic Version: 0.' in content
    assert 'fix(): small bug fix' in content


@fact
def multiple_version_groups_rendered_by_custom_template() -> None:
    """Multiple commits yielding distinct semver bumps each appear in the
    custom template output."""
    repo = _fixture_path('repo2')
    tmpl = _fixture_path('tpl2.j2', repo)
    out = repo / 'out.md'

    _clean_fixture(repo)
    repo.mkdir(parents=True, exist_ok=True)
    _setup_repo(repo)
    _make_commit(repo, 'fix: initial fix')
    _make_commit(repo, 'feat: new feature')

    tmpl.write_text(
        '{{ semver }}\n'
        '{% for v in versions %}'
        '{{ v.semver }}|{% for c in v.commits %}'
        '{{ c.type }}:{{ c.header }};{% endfor %}'
        '{% endfor %}\n',
        encoding='utf-8',
    )

    result = _run([
        '--changelog', str(out.resolve()),
        '--changelog-template', str(tmpl.resolve()),
        '--no-semver',
        str(repo.resolve()),
    ])
    assert result.returncode == 0, f'stderr: {result.stderr}'
    content = out.read_text(encoding='utf-8')
    assert 'feat:new feature' in content
    assert 'fix:initial fix' in content


@fact
def omitting_flag_uses_builtin_template() -> None:
    """When ``--changelog-template`` is absent the built-in template still
    renders correctly."""
    repo = _fixture_path('repo3')
    out = repo / 'CHANGELOG.md'

    _clean_fixture(repo)
    repo.mkdir(parents=True, exist_ok=True)
    _setup_repo(repo)
    _make_commit(repo, 'feat(cli): initial help')

    result = _run([
        '--changelog', str(out.resolve()),
        '--no-semver',
        str(repo.resolve()),
    ])
    assert result.returncode == 0, f'stderr: {result.stderr}'
    content = out.read_text(encoding='utf-8')
    # built-in template renders '#### <semver>'
    assert '#### 0.' in content
    assert 'feat(cli): initial help' in content


@fact
def custom_template_output_file_is_respected() -> None:
    """``--changelog <file>`` combined with ``--changelog-template`` writes
    output to the specified path."""
    repo = _fixture_path('repo4')
    tmpl = _fixture_path('tpl4.j2', repo)
    out = repo / 'custom.md'

    _clean_fixture(repo)
    repo.mkdir(parents=True, exist_ok=True)
    _setup_repo(repo)
    _make_commit(repo, 'chore(deps): bump')

    tmpl.write_text('{{ name }} custom', encoding='utf-8')

    result = _run([
        '--changelog', str(out.resolve()),
        '--changelog-template', str(tmpl.resolve()),
        '--no-semver',
        str(repo.resolve()),
    ])
    assert result.returncode == 0, f'stderr: {result.stderr}'
    assert out.exists()
    assert out.read_text(encoding='utf-8') == f'{repo.name} custom'


@fact
def integration_from_flag_produces_expected_version() -> None:
    """:option:`--from 1.4.0` with 1 fix + 1 feat produces ``1.5.0``."""
    repo = _fixture_path('repo5')
    out = repo / 'CHANGELOG.md'

    _clean_fixture(repo)
    repo.mkdir(parents=True, exist_ok=True)
    _setup_repo(repo)
    _make_commit(repo, 'fix: patch one')
    _make_commit(repo, 'feat: feature one')

    result = _run([
        '--from', '1.4.0',
        '--changelog', str(out.resolve()),
        '--no-semver',
        str(repo.resolve()),
    ])
    assert result.returncode == 0, f'stderr: {result.stderr}'
    content = out.read_text(encoding='utf-8')
    # major unchanged (1.4.0 → 1.5.0), minor bumped 4→5, patch reset
    assert '## 1.5.0' in content


@fact
def integration_from_flag_major_bump_resets_components() -> None:
    """:option:`--from 1.4.0` with fix + feat + feat! produces ``2.0.0``."""
    repo = _fixture_path('repo6')
    tmpl = _fixture_path('tpl6.j2', repo)
    out = repo / 'out.md'

    _clean_fixture(repo)
    repo.mkdir(parents=True, exist_ok=True)
    _setup_repo(repo)
    _make_commit(repo, 'fix: initial patch')
    _make_commit(repo, 'feat: feature')
    _make_commit(repo, 'feat!: breaking change')

    tmpl.write_text('{{ semver }}\n', encoding='utf-8')

    result = _run([
        '--from', '1.4.0',
        '--changelog', str(out.resolve()),
        '--changelog-template', str(tmpl.resolve()),
        '--no-semver',
        str(repo.resolve()),
    ])
    assert result.returncode == 0, f'stderr: {result.stderr}'
    content = out.read_text(encoding='utf-8')
    assert content.strip() == '2.0.0'


@fact
def integration_invalid_from_flag_fails() -> None:
    """An invalid --from value causes the CLI to exit with non-zero."""
    repo = _fixture_path('repo7')
    out = repo / 'CHANGELOG.md'

    _clean_fixture(repo)
    repo.mkdir(parents=True, exist_ok=True)
    _setup_repo(repo)
    _make_commit(repo, 'fix: test')

    result = _run([
        '--from', 'not-valid',
        '--changelog', str(out.resolve()),
        '--no-semver',
        str(repo.resolve()),
    ])
    assert result.returncode == 1, f'Expected failure but got: {result.stdout}'


@fact
def integration_from_flag_with_changelog_template() -> None:
    """--from combined with --changelog-template renders correct semver in output."""
    repo = _fixture_path('repo8')
    tmpl = _fixture_path('tpl8.j2', repo)
    out = repo / 'CHANGELOG.md'

    _clean_fixture(repo)
    repo.mkdir(parents=True, exist_ok=True)
    _setup_repo(repo)
    _make_commit(repo, 'fix: something')

    tmpl.write_text(
        '# {{ name }}\n'
        '{{ semver }}\n'
        '{% for v in versions %}'
        '{{ v.semver }}:{% for c in v.commits %}'
        '{{ c.type }};{% endfor %}\n'
        '{% endfor %}\n',
        encoding='utf-8',
    )

    result = _run([
        '--from', '0.0.1',
        '--changelog', str(out.resolve()),
        '--changelog-template', str(tmpl.resolve()),
        '--no-semver',
        str(repo.resolve()),
    ])
    assert result.returncode == 0, f'stderr: {result.stderr}'
    content = out.read_text(encoding='utf-8')
    assert '0.0.2' in content
    assert 'fix' in content
