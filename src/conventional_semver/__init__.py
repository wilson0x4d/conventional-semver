# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Expose the public API of the ``conventional-semver`` CLI tool.

This package provides conventional commit parsing, semantic version tracking, and changelog generation utilities.

Usage
-----

.. code-block:: python

    from conventional_semver import GitEntryParser, SemverOutputGenerator

    parser = GitEntryParser()
    entry = parser.parse(raw_log_output)
    generator = SemverOutputGenerator(config)
"""

from .Changelog import Changelog
from .ChangelogOutputGenerator import ChangelogOutputGenerator
from .CommandLineProcessor import CommandlineProcessor
from .Configuration import Configuration
from .GitAdapter import GitAdapter
from .GitEntry import GitEntry
from .GitEntryParser import GitEntryParser
from .GitLogStream import GitLogStream
from .OutputGenerator import OutputGenerator
from .SemverOutputGenerator import SemverOutputGenerator
from .SemverComponentType import SemverComponentType
from .Validator import Validator

__version__ = '0.0.0'
__commit__ = '0abc123'
__all__ = [
    '__version__', '__commit__',
    'Changelog',
    'ChangelogOutputGenerator',
    'CommandlineProcessor',
    'Configuration',
    'GitAdapter',
    'GitEntry',
    'GitEntryParser',
    'GitLogStream',
    'OutputGenerator',
    'SemverOutputGenerator',
    'SemverComponentType',
    'Validator',
]
