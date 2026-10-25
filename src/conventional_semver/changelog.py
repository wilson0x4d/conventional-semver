# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Render conventional commit data into a structured changelog.

This module provides a :class:`Changelog` class that accepts commit groups organized by semantic version and renders them as markdown-formatted release notes using Jinja2 templates (built-in or custom).

Commit-derived content is HTML autoescaped by default (full Jinja2 autoescaping of ``& < > " '``); pass ``autoescape=False`` to render content verbatim.

Usage
-----

.. code-block:: python

    changelog = Changelog()
    data = {'name': 'my-project', 'versions': [...]}
    output = changelog.generate(data, template_path='custom.j2')
"""

from __future__ import annotations

from jinja2.sandbox import SandboxedEnvironment
from typing import Any


class Changelog:
    """Generate a changelog from conventional commit entries.

    Renders Jinja2 templates (built-in or custom) to produce markdown-formatted release notes organized by semver version groups.  By default the render environment applies full Jinja2 HTML autoescaping (``& < > " '`` are all escaped); ``autoescape=False`` passes commit-derived strings through to the template verbatim.

    Usage
    -----

    .. code-block:: python
        changelog = Changelog()
        output = changelog.generate(data, template_path='custom.j2')
    """

    __DEFAULT_TEMPLATE: str = (
        '{% for version in versions %}\n'
        '#### {{ version.semver }}\n'
        '{% for commit in version.commits %}\n'
        '- {{ commit.type }}{% if commit.scope %}({{ commit.scope }}){% endif %}: {{ commit.header }} {% if commit.commit_url is defined %}\n'
        '[{{ commit.hash }}]({{ commit.commit_url }}){% endif %} {% if commit.body is defined %}\n'
        '{{ commit.body }}\n{% if commit.footers is defined %}\n'
        '{% for footer in commit.footers %}> {{ footer }}\n{%- endfor -%}{% endif %}{% else %}\n\n{% endif %}\n'
        '{%- endfor -%}{%- endfor -%}\n'
    )

    __ENVIRONMENT_AUTOESCAPED: SandboxedEnvironment = SandboxedEnvironment(autoescape=True)
    __ENVIRONMENT_PLAIN: SandboxedEnvironment = SandboxedEnvironment(autoescape=False)

    __autoescape: bool

    def __init__(self, autoescape: bool = True) -> None:
        """Initialize the renderer with an escaping policy.

        :param autoescape: When True (the default), the render environment applies full Jinja2 HTML autoescaping (``& < > " '`` are all escaped); when False, commit-derived content is rendered verbatim.
        """
        self.__autoescape = autoescape

    def generate(self, data: dict[str, Any], template_path: str | None = None) -> str:
        """Render *data* into a changelog string.

        Templates are compiled and rendered through a sandboxed Jinja2 environment so template code cannot reach arbitrary Python attributes, callables, or builtins.  When *autoescape* is True (the default), the environment HTML-escapes every rendered string.

        :param data: Mapping of variable names to values made available to the Jinja2 template; keys become template-level variables.
        :param template_path: Path to a ``.j2`` template file on disk.  When *None* the built-in default template is used.
        :returns: The rendered changelog content.
        """
        if template_path is None:
            raw = self.__DEFAULT_TEMPLATE
        else:
            with open(template_path, encoding='utf-8') as fh:
                raw = fh.read()

        environment = (
            self.__ENVIRONMENT_AUTOESCAPED
            if self.__autoescape
            else self.__ENVIRONMENT_PLAIN
        )
        return environment.from_string(raw).render(**data)
