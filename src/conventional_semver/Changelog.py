# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Render conventional commit data into a structured changelog.

This module provides a :class:`Changelog` class that accepts commit groups organized by semantic version and renders them as markdown-formatted release notes using Jinja2 templates (built-in or custom).

Usage
-----

.. code-block:: python

    changelog = Changelog()
    data = {'name': 'my-project', 'versions': [...]}
    output = changelog.generate(data, template_path='custom.j2')
"""

from __future__ import annotations

from jinja2 import Template
from typing import Any


class Changelog:
    """Generate a changelog from conventional commit entries.

    Renders Jinja2 templates (built-in or custom) to produce markdown-formatted release notes organized by semver version groups.

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
        '- {{ commit.type }}({{ commit.scope }}): {{ commit.header }} {% if commit.url is defined %}[{{ commit.hash }}]({{ commit.url }}){% endif %} {% if commit.body is defined %}\n'
        '{{ commit.body }}\n{% if commit.footers is defined %}\n'
        '{% for footer in commit.footers %}> {{ footer }}\n{%- endfor -%}{% endif %}{% else %}\n{% endif %}\n'
        '{%- endfor -%}{%- endfor -%}\n'
    )

    def generate(
        self, data: dict[str, Any], template_path: str | None = None
    ) -> str:
        """Render *data* into a changelog string.

        :param data: Mapping of variable names to values made available to the Jinja2 template; keys become template-level variables.
        :param template_path: Path to a ``.j2`` template file on disk.  When *None* the built-in default template is used.
        :returns: The rendered changelog content.
        """
        if template_path is None:
            tmpl = Template(self.__DEFAULT_TEMPLATE)
        else:
            with open(template_path, encoding='utf-8') as fh:
                raw = fh.read()
            tmpl = Template(raw)

        return tmpl.render(**data)
