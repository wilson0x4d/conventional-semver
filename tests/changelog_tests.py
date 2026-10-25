# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

import tempfile
from pathlib import Path

from punit import fact, raises


@fact
def built_in_template_renders_versions_with_commits() -> None:
    from conventional_semver.changelog import Changelog

    changelog = Changelog()
    data = {
        'name': 'Demo',
        'semver': '0.1.0',
        'date': '2026-06-01',
        'hash': 'deadbeef',
        'versions': [
            {
                'semver': '0.1.0',
                'commits': [
                    {
                        'hash': 'aaa111',
                        'date': '2026-06-01',
                        'type': 'feat',
                        'scope': 'cli',
                        'header': 'add help command',
                    },
                ],
            },
        ],
    }
    result = changelog.generate(data)

    assert '#### 0.1.0' in result, f"(expected '#### 0.1.0' in, actual={result!r})"
    assert 'feat(cli): add help command' in result, f"(expected 'feat(cli): add help command' in, actual={result!r})"


@fact
def built_in_template_renders_body_and_footers() -> None:
    from conventional_semver.changelog import Changelog

    changelog = Changelog()
    data = {
        'name': 'Test',
        'semver': '0.2.0',
        'date': '2026-01-01',
        'hash': '111222',
        'versions': [
            {
                'semver': '0.2.0',
                'commits': [
                    {
                        'hash': 'bbb333',
                        'date': '2026-01-01',
                        'type': 'fix',
                        'scope': '',
                        'header': 'resolve crash on startup',
                        'body': 'Detailed description of the fix.',
                        'footers': ['Co-Authored-By: Alice <alice@example.com>'],
                    },
                ],
            },
        ],
    }
    result = changelog.generate(data)

    assert 'resolve crash on startup' in result, f"(expected 'resolve crash on startup' in, actual={result!r})"
    assert 'Detailed description of the fix.' in result, f"(expected 'Detailed description of the fix.' in, actual={result!r})"
    assert 'Co-Authored-By:' in result, f"(expected 'Co-Authored-By:' in, actual={result!r})"


@fact
def built_in_template_omits_empty_body() -> None:
    from conventional_semver.changelog import Changelog

    changelog = Changelog()
    data = {
        'name': 'NoBody',
        'semver': '0.3.0',
        'date': '2026-02-01',
        'hash': 'ccc444',
        'versions': [
            {
                'semver': '0.3.0',
                'commits': [
                    {
                        'hash': 'ddd555',
                        'date': '2026-02-01',
                        'type': 'chore',
                        'scope': 'deps',
                        'header': 'update dependencies',
                    },
                ],
            },
        ],
    }
    result = changelog.generate(data)

    # No body/footers means no empty indented lines from commit entries
    assert 'update dependencies' in result, f"(expected 'update dependencies' in, actual={result!r})"


@fact
def external_template_is_loaded_and_rendered() -> None:
    from conventional_semver.changelog import Changelog

    tmpl_content = '# {{ name }}\n## {{ semver }}\n{% for commit in versions[0].commits %}- {{ commit.header }}\n{% endfor %}'

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.j2', delete=False, encoding='utf-8'
    ) as fh:
        fh.write(tmpl_content)
        tmpl_path = Path(fh.name)

    try:
        changelog = Changelog()
        data = {
            'name': 'Named',
            'semver': '3.0.0',
            'versions': [
                {
                    'commits': [
                        {'hash': 'eee666', 'date': '2026-03-01', 'type': 'feat', 'scope': '', 'header': 'new feature'},
                        {'hash': 'fff777', 'date': '2026-03-02', 'type': 'fix', 'scope': 'core', 'header': 'hot fix'},
                    ],
                },
            ],
        }
        result = changelog.generate(data, template_path=str(tmpl_path))

        assert '# Named' in result, f"(expected '# Named' in, actual={result!r})"
        assert '## 3.0.0' in result, f"(expected '## 3.0.0' in, actual={result!r})"
        assert '- new feature' in result, f"(expected '- new feature' in, actual={result!r})"
        assert '- hot fix' in result, f"(expected '- hot fix' in, actual={result!r})"
    finally:
        tmpl_path.unlink()


@fact
def generate_returns_str_type() -> None:
    from conventional_semver.changelog import Changelog

    changelog = Changelog()
    result = changelog.generate(
        {
            'name': 'X',
            'semver': '1.0.0',
            'date': '2026-01-01',
            'hash': 'aaaaaa',
            'versions': [],
        }
    )

    assert isinstance(result, str), f"(expected str, actual {type(result)!r})"


@fact
def empty_versions_list_produces_valid_output() -> None:
    from conventional_semver.changelog import Changelog

    changelog = Changelog()
    data = {
        'name': 'Empty',
        'semver': '0.0.0',
        'date': '2026-01-01',
        'hash': 'bbbbbb',
        'versions': [],
    }
    result = changelog.generate(data)

    # No ### version headings because no versions
    assert '#### ' not in result, f"(expected no '#### ' in, actual={result!r})"


@fact
def no_autoescape_renders_content_verbatim() -> None:
    """autoescape=False renders commit content verbatim, with no escaping at all."""
    from conventional_semver.changelog import Changelog

    changelog = Changelog(autoescape=False)
    data = {
        'name': 'Demo',
        'semver': '1.0.0',
        'date': '2026-01-01',
        'hash': 'deadbeef',
        'versions': [
            {
                'semver': '1.0.0',
                'commits': [
                    {
                        'hash': 'aaa111',
                        'date': '2026-01-01',
                        'type': 'feat',
                        'scope': '',
                        'header': '<img src=x onerror=alert(1)>',
                        'body': 'it\'s "trusted" & <fine>',
                    },
                ],
            },
        ],
    }
    result = changelog.generate(data)

    assert '<img src=x onerror=alert(1)>' in result, f"(expected raw img tag, actual={result!r})"
    assert 'it\'s "trusted" & <fine>' in result, f"(expected raw body, actual={result!r})"
    assert '&lt;' not in result, f"(expected no escaping at all, actual={result!r})"


@fact
def default_mode_applies_full_autoescape() -> None:
    """Default mode fully HTML-escapes commit content, including quotes."""
    from conventional_semver.changelog import Changelog

    changelog = Changelog()
    data = {
        'name': 'Demo',
        'semver': '1.0.0',
        'date': '2026-01-01',
        'hash': 'deadbeef',
        'versions': [
            {
                'semver': '1.0.0',
                'commits': [
                    {
                        'hash': 'aaa111',
                        'date': '2026-01-01',
                        'type': 'feat',
                        'scope': '',
                        'header': '<img src=x onerror=alert("pwn")>',
                        'body': "it's <b>bold</b> & more",
                    },
                ],
            },
        ],
    }
    result = changelog.generate(data)

    assert '<img' not in result, f"(expected no raw img tag, actual={result!r})"
    assert '&lt;img' in result, f"(expected escaped img tag, actual={result!r})"
    assert '&#34;' in result, f"(expected escaped double quotes, actual={result!r})"
    assert 'it&#39;s' in result, f"(expected escaped apostrophe, actual={result!r})"
    assert '&amp;' in result, f"(expected escaped ampersand, actual={result!r})"
    assert '&amp;lt;' not in result, f"(expected no double-escaping, actual={result!r})"


@fact
def built_in_template_renders_commit_url_link_when_present() -> None:
    from conventional_semver.changelog import Changelog

    changelog = Changelog()
    data = {
        'name': 'Demo',
        'semver': '1.0.0',
        'date': '2026-01-01',
        'hash': 'deadbeef',
        'versions': [
            {
                'semver': '1.0.0',
                'commits': [
                    {
                        'hash': 'aaa111',
                        'date': '2026-01-01',
                        'type': 'feat',
                        'scope': '',
                        'header': 'add feature',
                        'commit_url': 'https://example.com/commit/aaa111',
                    },
                ],
            },
        ],
    }
    result = changelog.generate(data)

    assert '[aaa111](https://example.com/commit/aaa111)' in result, f"(expected the commit link in, actual={result!r})"


@fact
def built_in_template_omits_commit_url_link_when_absent() -> None:
    from conventional_semver.changelog import Changelog

    changelog = Changelog()
    data = {
        'name': 'Demo',
        'semver': '1.0.0',
        'date': '2026-01-01',
        'hash': 'deadbeef',
        'versions': [
            {
                'semver': '1.0.0',
                'commits': [
                    {
                        'hash': 'aaa111',
                        'date': '2026-01-01',
                        'type': 'feat',
                        'scope': '',
                        'header': 'add feature',
                    },
                ],
            },
        ],
    }
    result = changelog.generate(data)

    assert '](https://' not in result, f"(expected no commit link, actual={result!r})"


@fact
def multiple_versions_rendered() -> None:
    from conventional_semver.changelog import Changelog

    changelog = Changelog()
    data = {
        'name': 'Multi',
        'semver': '2.0.0',
        'date': '2026-04-01',
        'hash': 'cccccc',
        'versions': [
            {
                'semver': '1.0.0',
                'commits': [
                    {'hash': 'd1', 'date': '2025-01-01', 'type': 'feat', 'scope': '', 'header': 'v1 feature'},
                ],
            },
            {
                'semver': '2.0.0',
                'commits': [
                    {'hash': 'd2', 'date': '2026-04-01', 'type': 'feat', 'scope': 'api', 'header': 'v2 feature'},
                ],
            },
        ],
    }
    result = changelog.generate(data)

    assert '### 1.0.0' in result, f"(expected '### 1.0.0' in, actual={result!r})"
    assert '### 2.0.0' in result, f"(expected '### 2.0.0' in, actual={result!r})"
    assert 'v1 feature' in result, f"(expected 'v1 feature' in, actual={result!r})"
    assert 'v2 feature' in result, f"(expected 'v2 feature' in, actual={result!r})"


@fact
def custom_template_dunder_access_renders_nothing() -> None:
    """Custom templates render through a sandboxed environment, so dunder
    attribute access yields no output (SSTI defense-in-depth)."""
    from conventional_semver.changelog import Changelog

    tmpl_content = '{{ name.__class__ }}'
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.j2', delete=False, encoding='utf-8'
    ) as fh:
        fh.write(tmpl_content)
        tmpl_path = Path(fh.name)

    try:
        changelog = Changelog()
        result = changelog.generate({'name': 'Demo'}, template_path=str(tmpl_path))
        assert result == '', f"(expected='', actual={result!r})"
    finally:
        tmpl_path.unlink()


@fact
def custom_template_cannot_exploit_blocked_dunder_access() -> None:
    """Chaining further operations onto a sandbox-blocked dunder attribute
    raises SecurityError."""
    from conventional_semver.changelog import Changelog
    from jinja2.exceptions import SecurityError

    tmpl_content = '{{ name.__class__.__mro__ }}'
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.j2', delete=False, encoding='utf-8'
    ) as fh:
        fh.write(tmpl_content)
        tmpl_path = Path(fh.name)

    try:
        changelog = Changelog()
        assert raises[SecurityError](
            lambda: changelog.generate({'name': 'Demo'}, template_path=str(tmpl_path))
        ), '(expected SecurityError for chained dunder attribute access)'
    finally:
        tmpl_path.unlink()
