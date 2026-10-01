# conventional-semver

## Purpose

`conventional-semver` is a Python CLI tool that processes [Conventional Commits](https://www.conventionalcommits.org/) in a git repository and emits a [SEMVER](https://semver.org) version string, and optionally generates a CHANGELOG file. It is designed for use in CI/CD pipelines and build workflows.

## CLI Usage

```
conventional-semver [options] [repo-path]
```

### Options

| Flag | Description |
|------|-------------|
| `--help` | Print usage, then exit |
| `--version` | Print version info, then exit |
| `--verbose` / `-v` | Enable verbose (debug) output |
| `--commit <hash>` | Start changelog from a specific commit hash |
| `--tag <name>` | Start changelog from a specific tag name |
| `--changelog [file]` | Enable changelog output; defaults to `CHANGELOG.md` if no file given |
| `--changelog-template <path>` | Path to a custom Jinja2 changelog template |
| `--no-semver` | Disable SEMVER output to STDOUT |
| `--from <X.Y.Z>` | Set the baseline SEMVER (e.g. `--from 1.4.0`). Takes precedence over `--major`/`--minor`/`--patch` |
| `--major <N>` | SEMVER Major component start value (default: 0) |
| `--minor <N>` | SEMVER Minor component start value (default: 0) |
| `--patch <N>` | SEMVER Patch component start value (default: 0) |
| `--git-path <path>` | Override the path to the `git` executable |
| `--config <file>` | Path to a custom config file (default: search standard locations) |
| `--validate [MESSAGE]` | Validate commit messages against configured patterns |
| `--commit-url <URL>` | Base URL for commit links in changelog |

Positional `repo-path` defaults to the current working directory.

### Basic Usage

```bash
# Emit SEMVER to stdout
$ conventional-semver
0.1.23

# Generate a changelog
$ conventional-semver --changelog
$ conventional-semver --changelog CHANGELOG.md

# Override baseline version
$ conventional-semver --from 1.4.0
1.4.3

# Validate commits only
$ conventional-semver --validate
```

### Configuration Files

Configuration can be placed in one of these locations (in precedence order):
1. `./conventional-semver.conf` (working directory)
2. `~/.config/conventional-semver/settings.conf` (user profile)
3. `/etc/conventional-semver/settings.conf` (system-wide)

Or specified via `--config`.

**Format** (INI-style with `[types]` and `[footers]` sections):

```ini
# lines starting with # are comments
# empty lines are ignored

# [types] section: regex patterns matched against commit type prefixes
# values: major, minor, or patch (first letter: j, n, t)
[types]
.*!=major
feat.*=minor
.*=patch

# [footers] section: regex patterns matched against footer lines
[footers]
BREAKING[\-\.]CHANGE=major
```

Key = regex pattern, Value = component to increment when the pattern matches. Higher-precedence matches win (MAJOR > MINOR > PATCH).

### Changelog Templates

Changelog output uses Jinja2 templates. The built-in default produces markdown. Customize with `--changelog-template <path>`.

**Template data dict structure:**

```json
{
    "name": "<repo basename>",
    "semver": "<most recent semver>",
    "date": "<today's date>",
    "hash": "<git hash of most recent commit>",
    "versions": [
        {
            "semver": "<semver>",
            "commits": [
                {
                    "date": "<commit date>",
                    "hash": "<short git hash>",
                    "message": "<full commit message>",
                    "type": "<commit type>",
                    "scope": "<commit scope>",
                    "header": "<subject sans type/scope>",
                    "body": "<optional body>",
                    "footers": "<optional footers>"
                }
            ]
        }
    ]
}
```
