# SPDX-FileCopyrightText: (c) 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Validate conventional commit messages against configured patterns.

Provides the :class:`Validator` class which checks committed messages against
the ``[types]`` and ``[footers]`` patterns loaded from configuration.  This
enables pre-commit hooks and CI pipelines to ensure every commit follows the
project's agreed-upon conventions.

Usage
-----

.. code-block:: python

    from conventional_semver import Configuration, GitEntry, Validator

    config = Configuration()
    config.process_configuration()

    validator = Validator(config)

    error = validator.validate_message('feat(cli): add help')
    assert error is None  # valid

    errors = validator.validate_log([entry1, entry2])
    assert len(errors) == 0  # all valid
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .GitEntry import GitEntry

if TYPE_CHECKING:
    from .Configuration import Configuration


class Validator:
    """Validate conventional commit messages against configured patterns.

    Checks the type and footer portions of a commit message against the
    :class:`~conventional_semver.Configuration` patterns.  A message is valid
    when at least one type pattern or footer pattern matches the extracted type
    or any footer line.

    Usage
    -----

    .. code-block:: python
        config = Configuration()
        config.process_configuration()
        validator = Validator(config)
        errors = validator.validate_log(entries)
    """

    __types: list[tuple[re.Pattern, re.Match]]
    __footers: list[tuple[re.Pattern, re.Match]]

    def __init__(self, config: Configuration) -> None:
        """Initialize with the patterns from *config*.

        :param config: The active configuration containing type and footer patterns.
        """
        self.__types = config.types  # type: ignore[assignment]
        self.__footers = config.footers  # type: ignore[assignment]

    def validate_message(self, message: str) -> str | None:
        """Validate a single commit message string.

        Extracts the type from the conventional-commit subject and checks it
        against every configured type pattern.  If no pattern matches, returns
        an error message describing the unrecognized type.  Otherwise returns
        ``None``.

        :param message: A conventional commit message such as ``'feat(cli): add help'``.
        :returns: ``None`` when valid, or an error description string when unrecognized.
        """
        entry = GitEntry(subject=message)
        return self._entry_has_unrecognized_type(entry, message)

    def validate_log(
        self,
        entries: list[GitEntry],
    ) -> list[str]:
        """Validate a list of git commit entries.

        Checks every entry using :meth:`validate_message` and returns all
        discovered validation errors, making it suitable for CI/CD pipelines
        that need to report every issue at once.

        :param entries: A list of parsed :class:`~conventional_semver.GitEntry` objects.
        :returns: A list of error description strings; empty when all entries are valid.
        """
        errors: list[str] = []
        for entry in entries:
            error = self._entry_has_unrecognized_type(entry, entry.subject)
            if error is not None:
                errors.append(error)
        return errors

    def _entry_has_unrecognized_type(
        self, entry: GitEntry, message: str
    ) -> str | None:
        """Return an error when *entry* type matches no configured pattern.

        Checks every type pattern against the full subject line, the same way
        :meth:`~conventional_semver.Configuration.compute_semver_change` does,
        then checks every footer pattern against each footer line.  If at least
        one match is found the message is valid.

        :param entry: A parsed git commit entry.
        :param message: The full commit message for use in error output.
        :returns: ``None`` when valid, or an error description string when unrecognized.
        """
        commit_type = entry._extract_type()
        if not commit_type:
            return f"Unrecognized commit message -- could not determine type: '{message}'"

        for pattern, _ in self.__types:
            if pattern.search(entry.subject):
                return None

        for footer_line in entry.footers:
            for pattern, _ in self.__footers:
                if pattern.search(footer_line):
                    return None

        return f"Unrecognized commit type: '{commit_type}' -- '{message}'"
