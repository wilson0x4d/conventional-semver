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

from .changelog import Changelog
from .changelog_output_generator import ChangelogOutputGenerator
from .command_line_processor import CommandlineProcessor
from .configuration import Configuration
from .git_adapter import GitAdapter
from .git_entry import GitEntry
from .git_entry_parser import GitEntryParser
from .git_log_stream import GitLogStream
from .output_generator import OutputGenerator
from .semver_component_type import SemverComponentType
from .semver_output_generator import SemverOutputGenerator
from .validator import Validator

__version__ = '0.0.0'
__commit__ = '0abc123'
__all__ = [
    'Changelog',
    'ChangelogOutputGenerator',
    'CommandlineProcessor',
    'Configuration',
    'GitAdapter',
    'GitEntry',
    'GitEntryParser',
    'GitLogStream',
    'OutputGenerator',
    'SemverComponentType',
    'SemverOutputGenerator',
    'Validator',
    '__commit__',
    '__version__',
]
