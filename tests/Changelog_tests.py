# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

import tempfile
from pathlib import Path

from punit import fact


@fact
def built_in_template_renders_versions_with_commits() -> None:
    from conventional_semver.Changelog import Changelog

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

    assert '#### 0.1.0' in result
    assert 'feat(cli): add help command' in result


@fact
def built_in_template_renders_body_and_footers() -> None:
    from conventional_semver.Changelog import Changelog

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

    assert 'resolve crash on startup' in result
    assert 'Detailed description of the fix.' in result
    assert 'Co-Authored-By:' in result


@fact
def built_in_template_omits_empty_body() -> None:
    from conventional_semver.Changelog import Changelog

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
    assert 'update dependencies' in result


@fact
def external_template_is_loaded_and_rendered() -> None:
    from conventional_semver.Changelog import Changelog

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

        assert '# Named' in result
        assert '## 3.0.0' in result
        assert '- new feature' in result
        assert '- hot fix' in result
    finally:
        tmpl_path.unlink()


@fact
def generate_returns_str_type() -> None:
    from conventional_semver.Changelog import Changelog

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

    assert isinstance(result, str), 'Expected generate to return a str'


@fact
def empty_versions_list_produces_valid_output() -> None:
    from conventional_semver.Changelog import Changelog

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
    assert '#### ' not in result


@fact
def multiple_versions_rendered() -> None:
    from conventional_semver.Changelog import Changelog

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

    assert '### 1.0.0' in result
    assert '### 2.0.0' in result
    assert 'v1 feature' in result
    assert 'v2 feature' in result
