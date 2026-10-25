# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-License-Identifier: MIT

"""Tests for the :mod:`~conventional_semver.safe_env` module."""

from contextlib import contextmanager
from typing import Iterator
import os

from punit import fact, inlinedata, theory

from conventional_semver.safe_env import scrubbed_env


@contextmanager
def _env(name: str, value: str) -> Iterator[None]:
    """Set *name* to *value* in the environment, restoring the prior state on exit."""
    saved = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if saved is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = saved


@theory
@inlinedata('GIT_CONFIG_COUNT')
@inlinedata('GIT_CONFIG_KEY_0')
@inlinedata('GIT_DIR')
@inlinedata('GIT_SSH_COMMAND')
@inlinedata('GITHUB_TOKEN')
@inlinedata('GITEA_TOKEN')
@inlinedata('UV_PUBLISH_TOKEN')
@inlinedata('PYPI_URL')
@inlinedata('PIP_INDEX_URL')
@inlinedata('AWS_SECRET_ACCESS_KEY')
@inlinedata('MY_API_KEY')
@inlinedata('DEPLOY_TOKEN')
@inlinedata('git_config_global')
def sensitive_names_are_scrubbed(name: str) -> None:
    with _env(name, 'sentinel'):
        env = scrubbed_env()
    assert name not in env, f'(expected {name!r} to be scrubbed)'


@theory
@inlinedata('PATH')
@inlinedata('HOME')
@inlinedata('VIRTUAL_ENV')
@inlinedata('PYTHONPATH')
@inlinedata('TERM')
def benign_names_are_preserved(name: str) -> None:
    with _env(name, 'sentinel'):
        env = scrubbed_env()
    assert env.get(name) == 'sentinel', f"(expected {name!r} to be preserved, actual={env.get(name)!r})"


@fact
def scrubbed_env_returns_a_copy() -> None:
    with _env('HARDCODED_TEST_VAR', 'sentinel'):
        env = scrubbed_env()
        env['HARDCODED_TEST_VAR'] = 'mutated'
    assert os.environ.get('HARDCODED_TEST_VAR') is None, '(expected the process environment to be untouched)'


@fact
def scrubbed_env_is_callable_without_sensitive_vars() -> None:
    env = scrubbed_env()
    assert isinstance(env, dict), f'(expected dict, actual {type(env)!r})'
    assert 'PATH' in env, '(expected PATH to remain available for git lookup)'
