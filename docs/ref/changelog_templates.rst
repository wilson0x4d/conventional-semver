Changelog Templates
===================

The changelog generator renders changelogs using `Jinja2` templates. You can use the
built-in default template or supply a custom ``.j2`` template via the
``--changelog-template`` CLI argument or the ``config.changelog_template`` setting.

.. code:: bash

   conventional-semver --changelog --changelog-template ./my-template.j2


Template Data Structure
-----------------------

When ``Changelog.generate(data, template_path)`` is called the template receives a
single ``dict`` as kwargs that expands into template-level variables. The dict is
built by :class:`~conventional_semver.ChangelogOutputGenerator` and consists of
the following keys:


Template-Level Variables
~~~~~~~~~~~~~~~~~~~~~~~~

A field list is used so Python union-style type annotations (e.g. ``str | None``)
do not break the RST table syntax.

: name:       Basename of the repository path. (``str``)
: semver:     Final computed version string, e.g. ``"1.2.3"``. (``str``)
: date:       Today's date in ``YYYY-MM-DD`` format. (``str``)
: hash:       Short hash of the most recent commit. (``str``)
: versions:   ``list[dict]`` of version-group dicts; see below. (``list``)


Version-Group Variables
~~~~~~~~~~~~~~~~~~~~~~~

Each item in ``versions`` is a dict:

: semver:     The semantic version string for this group. (``str``)
: commits:    ``list[dict]`` of commit dicts; see below. (``list``)


Commit Variables
~~~~~~~~~~~~~~~~

Each item in ``commits`` is a dict:

: hash:         Short (7-char) commit hash. (``str``)
: date:         Commit date in ``YYYY-MM-DD`` or ``'unknown'``. (``str``)
: type:         Conventional commit type, e.g. ``'feat'``, ``'fix'``. (``str``)
: scope:        Scope portion or ``''`` if absent. (``str``)
: header:       Message text after ``type(scope):`` prefix. (``str``)
: body:     Optional multi-line body text. Present only when the commit has a body. (``str | None``)
: footers:  ``list[str]`` of raw footer strings. Present only when footers exist (e.g. ``'Co-Authored-By: ...'``).
: commit_url: Full URL with commit hash. Only present when ``--commit-url`` is used (e.g. ``'https://github.com/.../abc1234'``).

Built-in Default Template
-------------------------

If no template path is supplied the generator uses this built-in template:

.. code::

   {% for version in versions %}
   #### {{ version.semver }}
   {% for commit in version.commits %}
   - {{ commit.type }}({{ commit.scope }}): {{ commit.header }} {% if commit.url is defined %}[{{ commit.hash }}]({{ commit.url }}){% endif %} {% if commit.body is defined %}
   {{ commit.body }}
   {% if commit.footers is defined %}
   {% for footer in commit.footers %}> {{ footer }}
   {%- endfor -%}{% endif %}{% else %}
   {% endif %}

   {%- endfor -%}{% endfor -%}


Custom Template Examples
------------------------


GitHub-Style Changelog
~~~~~~~~~~~~~~~~~~~~~~

This template produces a heading per version, with expandable commit entries
that show date, hash link, body, and footers.

.. code::

   # {{ name }} Changelog

   **Version {{ semver }}** -- {{ date }}

   {% for version in versions %}
   ## {{ version.semver }}

   {% for commit in version.commits %}
   ### {{ commit.type }}{% if commit.scope %}({{ commit.scope }}){% endif %}: {{ commit.header }}

   - **Date:** {{ commit.date }}
   - **Hash:** [`{{ commit.hash }}`]({{ commit.commit_url | default('#') }})
   {% if commit.body %}
   - **Body:**

     {{ commit.body }}
   {% endif %}
   {% if commit.footers %}
   - **Footers:**
   {% for footer in commit.footers %}
     - {{ footer }}
   {% endfor %}
   {% endif %}

   {% endfor %}
   {% endfor %}


Tabular / Compact Changelog
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Produces a single Markdown table with one row per commit:

.. code::

   # {{ name }} -- {{ semver }} ({{ date }})

   | Version | Date | Type | Scope | Header | Hash |
   |---------|------|------|-------|--------|------|
   {% for version in versions %}
   {% for commit in version.commits %}
   | `{{ version.semver }}` | {{ commit.date }} | {{ commit.type }} | {{ commit.scope | default('-') }} | {{ commit.header }} | `{{ commit.hash }}` |
   {% endfor %}
   {% endfor %}


GitHub Release Notes (JSON + Markdown)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generates an initial JSON block followed by a body in Markdown, suitable
for the GitHub Releases API:

.. code::

   {% raw %}
   {{
     "tag_name": "{{ semver }}",
     "target_commitish": "HEAD",
     "name": "{{ name }} {{ semver }}",
     "body": ""
   }}
   {% endraw %}
   {% for version in versions %}
   ## {{ version.semver }}

   {% for commit in version.commits %}
   - {{ commit.type }}{% if commit.scope %}({{ commit.scope }}){% endif %}: {{ commit.header }}

   {% if commit.body %}
   {{ commit.body }}
   {% endif %}

   {% endfor %}
   {% endfor %}


Template Reference
------------------


Top-Level Variables
~~~~~~~~~~~~~~~~~~~~~

``{{ name }}``
   Repository name (path basename).

``{{ semver }}``
   The final computed semantic version (e.g. ``"1.2.3"``).

``{{ date }}``
   Today's date in ISO format ``YYYY-MM-DD``.

``{{ hash }}``
   Short hash of the most recent commit in the processed range.

``{{ versions }}``
   A ``list[dict]`` of version groups. Iterate with
   ``{% for version in versions %}``.


Version Group Variables
~~~~~~~~~~~~~~~~~~~~~~~

``{{ version.semver }}``
   The semantic version string for this group.

``{{ version.commits }}``
   A ``list[dict]`` of commits that contributed to this version bump.


Commit Variables
~~~~~~~~~~~~~~~~

``{{ commit.hash }}``
   Short commit hash (7 characters).

``{{ commit.date }}``
   Commit author date in ``YYYY-MM-DD`` format. Values of ``'unknown'`` are
   returned when the date could not be retrieved from git.

``{{ commit.type }}``
   The conventional commit type extracted from the subject. For a commit
   ``feat(cli): add help`` this yields ``'feat'``.

``{{ commit.scope }}``
   The scope portion inside parentheses. For ``feat(cli):`` the value is
   ``'cli'``. If no scope is specified the value is an empty string ``''``.

``{{ commit.header }}``
   The message text after the ``type(scope):`` prefix. For
   ``fix(core): resolve crash`` this yields ``'resolve crash'``.

``{{ commit.body }}``
   Optional. The multi-line commit body. This key exists in the dict only
   when the commit has body text. Check with the ``is defined`` test:

   .. code::

      {% if commit.body is defined %}
      {{ commit.body }}
      {% endif %}

``{{ commit.footers }}``
   Optional. A ``list[str]`` of footer lines. Each element is a raw footer
   string such as ``'Co-Authored-By: Alice <alice@example.com>'``.

   .. code::

      {% if commit.footers is defined %}
      {% for footer in commit.footers %}
      > {{ footer }}
      {% endfor %}
      {% endif %}

``{{ commit.commit_url }}``
   Only present when the ``--commit-url`` flag is used. Contains the full URL
   pointing to the commit on the hosting service. Use the ``| default`` filter
   to avoid undefined variable errors when the flag is not set:

   .. code::

      [`{{ commit.hash }}`]({{ commit.commit_url | default('#') }})


Conditional Rendering
~~~~~~~~~~~~~~~~~~~~~

Because ``body``, ``footers``, and ``commit_url`` are only present when data
exists, use Jinja2's ``is defined`` test or the ``default`` filter to avoid
``UndefinedError`` exceptions:

.. code::

   {# Correct: uses 'is defined' check #}
   {% if commit.body is defined and commit.body %}
   {{ commit.body }}
   {% endif %}

   {# Also correct: default filter provides a fallback #}
   {{ commit.body | default('') }}

   {# Incorrect: will raise UndefinedError when body is absent #}
   {{ commit.body }}


Filters and Tests
~~~~~~~~~~~~~~~~~

Jinja2's standard filters and tests are available. Useful examples:

.. code::

   {# Trim whitespace in body text #}
   {{ commit.body | trim }}

   {# Capitalize the first letter of the header #}
   {{ commit.header | capitalize }}

   {# Escape HTML in body/footers for safe rendering #}
   {{ commit.body | e }}

   {# Check if scope is non-empty #}
   {% if commit.scope %}({{ commit.scope }}){% endif %}

   {# Reverse the commit list within a version #}
   {{ version.commits | reverse }}

   {# Count commits in a version group #}
   {{ version.commits | length }}


Loop Helpers
~~~~~~~~~~~~

Access the loop index and state inside ``for`` blocks:

.. code::

   {% for commit in version.commits %}
   {{ loop.index }}. {{ commit.header }}   {# 1-based index #}
   {% if loop.first %}(first){% endif %}
   {% if loop.last %}(last){% endif %}
   {% endfor %}


Template Lookup Order
---------------------

When ``--changelog-template`` is specified, the generator reads the filesystem
at the exact path you provide (relative or absolute). The file is read with
``encoding='utf-8'`` and passed to ``jinja2.Template(raw)``.

If you pass ``None`` (no flag), the built-in template is used automatically.

You can also set the template path programmatically:

.. code:: python

   from conventional_semver import ChangelogOutputGenerator, Configuration

   config = Configuration()
   generator = ChangelogOutputGenerator(config)
   generator.set_changelog_template('./my-template.j2')
   generator.generate_output()


Best Practices
--------------

* **Validate templates early.** Render against an empty repo to catch syntax
  errors before CI runs.

* **Use ``is defined`` for optional keys.** ``body``, ``footers``, and
  ``commit_url`` may not exist.

* **Prefer ``| default('')`` over raw access.** When you are confident the key
  exists but want to suppress ``None`` output, use the ``default`` filter.

* **Keep templates DRY.** Extract common snippets into Jinja2 macros if you
  reuse templates across projects.

* **Test with diverse commits.** Ensure your template handles commits without
  bodies, without scopes, and without footers correctly.

* **Escape user content.** If footers or bodies may contain special
  characters, apply the ``| e`` (escape) filter.


Quick-Start Checklist
---------------------

1. Write your template as a ``.j2`` file.
2. Test it locally with
   ``conventional-semver --changelog --changelog-template ./my-template.j2``.
3. Add ``--changelog-template`` to your CI/CD pipeline configuration.
4. Commit the template alongside your project.

For reference, the default template is available in the source at
``src/conventional_semver/Changelog.py:__DEFAULT_TEMPLATE``.


Implementation Notes
--------------------

Template rendering is performed by
:class:`~conventional_semver.Changelog.generate`. Each call creates a new
``jinja2.Template`` instance from the raw template string. Data is passed via
``**data`` using ``tmpl.render(**data)``. There is no template caching between
calls; for repeated rendering of the same template string, reuse the
``Template`` object directly.

The ``ChangelogOutputGenerator`` is responsible for constructing the ``data``
dict. It queries git for dates, groups commits by semver, and builds the
``versions`` list before passing everything to
``Changelog.generate()``.
