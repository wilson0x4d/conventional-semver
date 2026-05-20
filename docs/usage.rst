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
            --help              print usage, then exit.
            --version           print version info, then exit.
            --verbose           enable verbose (debug) output.
            --commit <hash>     indicates which commit hash to start changelog from.
            --tag <name>        indicates which tag to start changelog from.
            --changelog <file>  overrides the name of the file the changelog is written to, otherwise 'changelog.md' is the default.
            --no-semver         disable SEMVER output to STDOUT.
            --major             SEMVER 'Major' component will start with this value, default is '0'.
            --minor             SEMVER 'Minor' component will start with this value, default is '0'.
            --patch             SEMVER 'Patch' component will start with this value, default is '0'.
            --git-path <path>   overrides the path to `git` tool, otherwise `git` must be in environment PATH.

    Parameters:
            repo-path           the path of the git repository to process, if not specified defaults to working directory.

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

* ``./conventional-semver.conf`` (working directory.)
* ``~/.config/conventional-semver/settings.conf`` (user profile ``.config`` directory.)
* ``/etc/conventional-semver/settings.conf`` (root ``/etc`` directory.)

The configuration file should have the following format:

.. code-block:: yaml

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

    # in each of the above sections, each line
    # represents a key-value pair. the key is a regex
    # and the value is a component type to be
    # incremented if the regex is a match.

There is a sample configuration file located in this repo as ``config/conventional-semver.conf`` which contains additional comments and explanations, you can customize it to fit your needs and then place it at one of the well-known locations mentioned above.

