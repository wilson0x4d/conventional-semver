
**conventional-semver** is a [Conventional Commits](https://www.conventionalcommits.org/) processor designed to emit a [SEMVER](https://semver.org) as part of a build pipeline.

## Usage

```text
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
```

### Generating SEMVER

When you run **conventional-semver** from within a `git` repository, it will automatically process the log and emit a semver.

Example:

```bash
% conventional-semver
0.1.23
```

This allows you to pull a semver into an Environment Variable, evaluate it as an Argument to another tool, or pipe it to a file/stream for additional processing:

```bash
% export SEMVER=$(conventional-semver)
% echo $SEMVER
0.1.23
```

#### Override Baseline SEMVER

Projects adopting Conventional Commits may need to customize the baseline SEMVER, rather than starting from `0.0.0`. This can be done with the `--major`, `--minor`, and `--patch` arguments.

When run on a repo containing three non-conventional commits:

```bash
% conventional-semver --major 1 --minor 2 --patch 3
1.2.6
```

#### SEMVER Configuration

When run without any command-line arguments a default set of settings are used which implement a standard Conventional Commits behavior.

To customize behavior a configuration file may be created. This file can be passed in using a `--config` argument, or, placed into one of the following well-known locations (and in the following order):

* `./conventional-semver.conf` (working directory.)
* `~/.config/conventional-semver/settings.conf` (user profile `.config` directory.)
* `/etc/conventional-semver/settings.conf` (root `/etc` directory.)

The configuration file should have the following format:

```ini
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
```

There is a sample configuration file located in this repo as `config/conventional-semver.conf` which contains additional comments and explanations, you can customize it to fit your needs and then place it at one of the well-known locations mentioned above.

## Not yet Implemented

### Generating CHANGELOG

To generate a CHANGELOG you specify the `--changelog [filename]` switch, this takes an optional filename argument. If no filename is provided a default filename of `./CHANGELOG` is used to emit a file into the current working directory.

Example:

```bash
% conventional-semver --changelog
```

#### CHANGELOG Templates

The CHANGELOG output is controlled through one or more templates. This includes a required "entry" template, and optional "header" and "footer" templates. Combined this is meant to provide enough flexibility that you could emit templates in various structured formats such as XML, JSON, Markdown, etc.

The default templates are meant to produce a generic TEXT file that is markdown-friendly.

##### CHANGELOG Entry Template

For each SEMVER increment a CHANGELOG Entry is emitted.

The format of each CHANGELOG Entry is taken from a file named `changelog-entry.template`, when `--changelog` is specified this file is required to be present or the command will fail.

This is the default content of this template:

```text
$(DATE) $(SEMVER)-$(HASH)
$(TYPE)$(SCOPE): $(MESSAGE)
```

The entry template supports the following expando variables:

| Expando | Comment |
|-|-|
| $(DATE) | The date of the commit which caused SEMVER increment. This is emitted in the default culture of the current environment. |
| $(SEMVER) | The calculated SEMVER value. |
| $(HASH) | The short-form git commit hash. |
| $(TYPE) | The Conventional Commits `<type>` value. |
| $(SCOPE) | If any, the Conventional Commits `[scope]` value, including parenthesis. |
| $(MESSAGE) | The commit message, sans `<type>` and `[scope]`. |
| $(BODY) | If any, the commit body. |
| $(TRAILERS) | If any, the commit trailers (footers). |

##### CHANGELOG Header Template

The header prepended to the CHANGELOG comes from a file named `changelog-header.template`.

There are no special expando variables supported in the header.

##### CHANGELOG Footer Template

The footer appended to the CHANGELOG comes from a file named `changelog-footer.template`.

There are no special expando variables supported in the footer.

##### CHANGELOG Template Caveats

No escaping is performed on any of the emitted values. Thus, it is possible for commit messages to interact with parsers/renderers in unintended ways. For example if you make a template to emit an HTML changelog, and a commit message contains content which looks like an 'element', it will most likely result in a changelog that doesn't render as expected.
