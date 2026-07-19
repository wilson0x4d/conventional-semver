Semver Calculation
==================

**conventional-semver** computes semantic version numbers
from git history, and CLI arguments can control that computation.

.. contents::
   :depth: 3
   :local:

Overview
--------

When **conventional-semver** runs it:

1. Executes ``git log`` to read the commit history.
2. Parses each commit to extract **type**, **scope**, **header**, **body**, and **footers**.
3. Matches each commit against configured **type patterns** and **footer patterns** to
   determine the bump level: **MAJOR**, **MINOR**, or **PATCH**.
4. Starting from a configurable **baseline version**, increments counters following
   semver rules (major resets minor & patch; minor resets patch).
5. Outputs the final computed version string and optionally generates a changelog.

Baseline Versions
-----------------

The baseline is the version from which all increments are counted.  If no baseline
is explicitly set the tool starts from ``0.0.0``.

.. code:: bash

   # Default baseline: 0.0.0
   $ conventional-semver
   0.0.1

   # Explicit baseline via --from
   $ conventional-semver --from 1.4.0
   1.4.3

   # Explicit baseline via individual version component flags
   $ conventional-semver --major 1 --minor 4 --patch 0
   1.4.3

.. note::

   The ``--from`` flag and the ``--major``/``--minor``/``--patch`` flags are
   alternative ways to specify the same thing. When both are present, ``--from``
   takes precedence.

   ``--from`` expects a single ``X.Y.Z`` string where ``X``, ``Y``, and ``Z`` are
   non-negative integers.  Passing an invalid format (e.g. ``1.4``, ``invalid``,
   ``-1.0.0``) produces a clear error message and a non-zero exit code.

Commit Type Patterns
--------------------

Each commit is classified into a **bump level** by matching its subject line against
a configurable list of regex patterns.  The patterns are checked in order and the
highest-precedence match wins:

+------------+-------------------+-----------------------------------------------+
| Component  | Precedence        | Example pattern                               |
+------------+-------------------+-----------------------------------------------+
| MAJOR      | Highest (3)       | ``.*!`` — commits whose subject contains ``!``|
| MINOR      | Medium (2)        | ``feat.*`` — commits whose type is ``feat``   |
| PATCH      | Lowest (1)        | ``.*`` — catch-all for all other commits       |
+------------+-------------------+-----------------------------------------------+

Default Pattern Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When no custom configuration file is provided the following defaults are used:

.. code::

   [types]
   .*!=major
   feat.*=minor
   *=patch

   [footers]
   BREAKING[\-\.]CHANGE=major


Configuring Patterns
~~~~~~~~~~~~~~~~~~~~

Patterns are defined in the ``[types]`` section of a configuration file (for
subjects) or the ``[footers]`` section (for footer lines).  Each line has the
form ``<regex>=<component-letter>`` where the letter is:

+--------+-----------------+
| Letter | Component       |
+--------+-----------------+
| ``j``  | MAJOR           |
| ``n``  | MINOR           |
| ``t``  | PATCH           |
+--------+-----------------+

Examples:

.. code::

   [types]
   chore(deps).*=patch
   release.*=minor

   [footers]
   JIRA-ID.*=minor

Semver Counter Rules
--------------------

Once a bump level is determined the appropriate counter is incremented and lower
counters are reset.  This is the standard semver increment behaviour:

+------------+-----------------+-------------------------+
| Bump Level | Incremented     | Lower Counters Reset To |
+------------+-----------------+-------------------------+
| MAJOR      | major           | minor=0, patch=0        |
| MINOR      | minor           | patch=0                 |
| PATCH      | patch           | (none)                  |
+------------+-----------------+-------------------------+

Example Walk-Through
~~~~~~~~~~~~~~~~~~~~

Given the baseline ``--from 1.4.0`` and this commit history:

  +------------------+---------+------------+-----------+
  | Command          | Type    | Increment  | Result    |
  +------------------+---------+------------+-----------+
  | ``fix: patch ``  | PATCH   | patch + 1  | ``1.4.1`` |
  | ``feat: feature``| MINOR   | minor + 1  | ``1.5.0`` |
  | ``feat!: break ``| MAJOR   | major + 1  | ``2.0.0`` |
  +------------------+---------+------------+-----------+

After the final commit the tool prints ``2.0.0`` because the MAJOR bump resets
minor and patch to zero.

Footer-Based MAJOR Bumps
~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to type patterns, **footer lines** in commit messages can trigger
a MAJOR bump.  The default footer pattern matches:

.. code::

   BREAKING CHANGE: description
   Breaking-Change: description
   BREAKING.CHANGE: description

``<text>`` and ``<text>: <value>`` forms of the footer are both recognised.

How to Control Semver Calculation
---------------------------------

CLI Arguments
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Argument
     - Description
     - Example

   * - ``--from X.Y.Z``
     - Sets the starting version as a single string. ``X``, ``Y``, ``Z`` must be non-negative integers.
     - ``--from 1.4.0``
   * - ``--major N``
     - Sets the starting major component to *N*. Ignored when ``--from`` is used.
     - ``--major 1``
   * - ``--minor N``
     - Sets the starting minor component to *N*. Ignored when ``--from`` is used.
     - ``--minor 4``
   * - ``--patch N``
     - Sets the starting patch component to *N*. Ignored when ``--from`` is used.
     - ``--patch 0``

Config File Override
~~~~~~~~~~~~~~~~~~~~

Patterns in ``conventional-semver.conf`` override the built-in defaults. The
config file can redefine which commit types or body/subject patterns trigger
which bump level.

.. code::

   [types]
   feat.*=minor
   fix.*=patch
   *.!=major

   [footers]
   BREAKING[\-\.]CHANGE=major

Programmatic API
~~~~~~~~~~~~~~~~~~~~~

For programmatic use the same mechanism is exposed:

.. code:: python

   from conventional_semver import Configuration

   config = Configuration()
   config.set_start_from('1.4.0')   # equivalent to --from 1.4.0

   # config.major_start, .minor_start, and .patch_start are now 1, 4, 0
   assert config.major_start == 1
   assert config.minor_start == 4
   assert config.patch_start == 0


Output Generators
-----------------

Two generators produce output based on the same underlying semver calculation:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Generator
     - Description

   * - SemverOutputGenerator
     - Emits the final computed version string to **STDOUT** (e.g. ``1.5.0``). This is the tool's
       primary purpose — providing a version number for CI/CD pipelines.

   * - ChangelogOutputGenerator
     - Accumulates commits grouped by semver value and renders a **markdown-file**
       via a Jinja2 template.  Each unique semver bump becomes a version group in the
       changelog.


Bump Policies
~~~~~~~~~~~~~

The calculation is **deterministic** and **history-dependent**: the final
version is the result of processing *every commit* in the range from the latest
tag (or ``HEAD`` if no tag exists) back to ``--commit`` or ``--tag``.

Non-conventional commits that do not match any type pattern default to
**PATCH**, so even ``"bump version"`` or ``"merge branch"`` will increment patch
unless a custom pattern removes them.
