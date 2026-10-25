Quick Start
===========
.. _quickstart:

Installation
------------

You can install ``conventional-semver`` from `PyPI <https://pypi.org/project/py_conventional_semver/>`_ through the usual means, such as ``pip``:

.. code-block:: bash

   pip install py_conventional_semver

Usage
-----

.. code-block:: text

    Usage:
            conventional-semver [options] [repo-path]

    Options:
            -h, --help                    print usage, then exit.
            --version                     print version info, then exit.
            --verbose, -v                 enable verbose (debug) output.
            --no-semver                   disable SEMVER output to STDOUT.
            --validate [MESSAGE]          validate commit messages against configured patterns (use MESSAGE to validate a specific commit instead of the log).
            --changelog [FILE]            enable changelog output; defaults to CHANGELOG.md if no file given.
            --changelog-template <path>   path to a custom Jinja2 changelog template.
            --commit-url <URL>            base URL for commit links in the changelog; a / separator is added between the URL and hash.
            --commit <hash>               start changelog from a specific commit hash.
            --tag <name>                  start changelog from a specific tag name.
            --config <file>               path to a custom config file (default: search standard locations).
            --git-path <path>             override the path to the git executable (default: use PATH).
            --from <X.Y.Z>                set the baseline semver as a single X.Y.Z value (e.g. `--from 1.4.0`).
            --major <N>                   SEMVER major component start value (default: 0, ignored when --from is used).
            --minor <N>                   SEMVER minor component start value (default: 0, ignored when --from is used).
            --patch <N>                   SEMVER patch component start value (default: 0, ignored when --from is used).
            --trust-repo-templates        explicitly allow a changelog template that lies inside the repo being processed (unsafe for untrusted repos)..
            --trust-ugc                   treat commit content as trusted and disable HTML autoescaping (unsafe for untrusted repos).

    Parameters:
            repo-path                     the path to the git repository to process; defaults to the working directory.

Generating SEMVER
-----------------

When you run **conventional-semver** from within a ``git`` repository, it will automatically process the log and emit a semver.

Example:

.. code-block:: bash

    % conventional-semver
    0.1.23

This allows you to pull a semver into an Environment Variable, evaluate it as an Argument to another tool, or pipe it to a file/stream for additional processing:

.. code-block:: bash

    % export SEMVER=$(conventional-semver)
    % echo $SEMVER
    0.1.23

Override Baseline SEMVER
------------------------

Projects adopting Conventional Commits may need to customize the baseline SEMVER, rather than starting from ``0.0.0``. This can be done with the ``--major``, ``--minor``, and ``--patch`` arguments.

When run on a repo containing three non-conventional commits:

.. code-block:: bash

    % conventional-semver --major 1 --minor 2 --patch 3
    1.2.6

SEMVER Configuration
--------------------

When run without any command-line arguments a default set of settings are used which implement a standard Conventional Commits behavior.

To customize behavior a configuration file may be created. This file can be passed in using a ``--config`` argument, or, placed into one of the following well-known locations (and in the following order):

* ``~/.config/conventional-semver/settings.conf`` (user profile ``.config`` directory.)
* ``/etc/conventional-semver/settings.conf`` (root ``/etc`` directory.)

.. note::

   Loading a ``conventional-semver.conf`` from inside the repo (the working directory) became opt-in behavior with the 2.0.0 release (security hardening release).  Use ``--config`` to load a configuration file from the repo being processed.

The configuration file should have the following format:

.. code-block:: ini

    # lines starting with hash (#) are comments
    # empty lines, like the following, are ignored

    # conventional commit "type" mappings are
    # configured in a [types] section. the following
    # mirrors the default configuration:
    [types]
    .*!=major
    feat.*=minor
    .*=patch

    # conventional commit "footer" mappings are
    # configured in a [footers] section. the following
    # mirrors the default configuration:
    [footers]
    BREAKING[\-\.]CHANGE=major
    breaks:=major

    # in each of the above sections, each line
    # represents a key-value pair. the key is a regex
    # and the value is a component type to be
    # incremented if the regex is a match.

There is a sample configuration file located in this repo as ``configs/conventional-semver.conf`` which contains additional comments and explanations, you can customize it to fit your needs and then place it at one of the well-known locations mentioned above.

