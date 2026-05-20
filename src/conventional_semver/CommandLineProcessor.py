# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from __future__ import annotations

import sys
import hanaro
import logging

from .Configuration import Configuration


class CommandlineProcessor:

    __config: Configuration
    __logger: logging.Logger
    __paths: list[str]

    def __init__(self, config: Configuration, version: str, commit: str) -> None:
        self.__commit = commit
        self.__config = config
        self.__logger = hanaro.get_logger()
        self.__paths = [] 
        self.__version = version

    def __print_info(self) -> None:
        print(f'conventional-semver {self.__version} ({self.__commit})')

    def __print_usage(self) -> None:
        print()
        print('Usage:')
        print('\tconventional-semver [options] [repo-path]')
        print()
        print('Options:')
        print('\t--help              print usage, then exit.')
        print('\t--version           print version info, then exit.')
        print('\t--verbose           enable verbose (debug) output.')
        print('\t--commit <hash>     indicates which commit hash to start changelog from.')
        print('\t--tag <name>        indicates which tag to start changelog from.')
        print('\t--changelog <file>  overrides the name of the file the changelog is written to, otherwise \'changelog.md\' is the default.')
        print('\t--no-semver         disable SEMVER output to STDOUT.')
        print('\t--major             SEMVER \'Major\' component will start with this value, default is \'0\'.')
        print('\t--minor             SEMVER \'Minor\' component will start with this value, default is \'0\'.')
        print('\t--patch             SEMVER \'Patch\' component will start with this value, default is \'0\'.')
        print('\t--git-path <path>   overrides the path to `git` tool, otherwise `git` must be in environment PATH.')
        print()
        print('Parameters:')
        print('\trepo-path           the path of the git repository to process, if not specified defaults to working directory.')
        print()

    def process_command_line(self, argv: list[str] | None = None) -> None:
        if argv is None:
            argv = sys.argv
        args = argv[1:]
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == '--help':
                self.__print_info()
                self.__print_usage()
                sys.exit(0)
            elif arg == '--version':
                self.__print_info()
                sys.exit(0)
            elif arg == '--no-semver':
                self.__config.disable_semver_output = True
            elif arg == '--changelog':
                i += 1
                if i >= len(args) or args[i].startswith('-'):
                    raise IndexError('missing argument to `' + arg + '` option')
                self.__config.changelog_output_file = args[i]
            elif arg == '--commit':
                if getattr(self.__config, 'start_tag', ''):
                    raise RuntimeError('cannot specify both `--commit` and `--tag` options.')
                i += 1
                if i >= len(args) or args[i].startswith('-'):
                    raise IndexError('missing argument to `' + arg + '` option')
                self.__config.start_commit_hash = args[i]
            elif arg == '--config':
                i += 1
                if i >= len(args) or args[i].startswith('-'):
                    raise IndexError('missing argument to `' + arg + '` option')
                self.__config.config_file = args[i]
            elif arg == '--git-path':
                i += 1
                if i >= len(args) or args[i].startswith('-'):
                    raise IndexError('missing argument to `' + arg + '` option')
                self.__config.git_path = args[i]
            elif arg == '--major':
                i += 1
                if i >= len(args) or args[i].startswith('-'):
                    raise IndexError('missing argument to `' + arg + '` option')
                self.__config.major_start = int(args[i])
            elif arg == '--minor':
                i += 1
                if i >= len(args) or args[i].startswith('-'):
                    raise IndexError('missing argument to `' + arg + '` option')
                self.__config.minor_start = int(args[i])
            elif arg == '--patch':
                i += 1
                if i >= len(args) or args[i].startswith('-'):
                    raise IndexError('missing argument to `' + arg + '` option')
                self.__config.patch_start = int(args[i])
            elif arg == '--tag':
                if getattr(self.__config, 'start_commit_hash', ''):
                    raise RuntimeError('cannot specify both `--commit` and `--tag` options.')
                i += 1
                if i >= len(args) or args[i].startswith('-'):
                    raise IndexError('missing argument to `' + arg + '` option')
                self.__config.start_tag = args[i]
            elif arg == '--verbose':
                # TODO
                pass
            elif not self.__config.repo_path and not arg.startswith('-'):
                self.__config.repo_path = arg
            else:
                self.__print_usage()
                raise ValueError('unexpected argument: ' + arg)
            i += 1
