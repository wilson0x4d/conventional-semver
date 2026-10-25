
**conventional-semver** is a [Conventional Commits](https://www.conventionalcommits.org/) processor designed to emit a [SEMVER](https://semver.org) as part of a build pipeline.

## Usage

```text
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
```

### Generating SEMVER

When you run **conventional-semver** from within a `git` repository, it will automatically process the log and emit a semver.

Example:

```bash
$ conventional-semver
0.1.23
```

This allows you to pull a semver into an Environment Variable, evaluate it as an Argument to another tool, or pipe it to a file/stream for additional processing:

```bash
$ export SEMVER=$(conventional-semver)
$ echo $SEMVER
0.1.23
```

#### Override Baseline SEMVER

Projects adopting Conventional Commits may need to customize the baseline SEMVER, rather than starting from `0.0.0`. This can be done in two ways:

**Using `--from`** — supply a single semver string:

```bash
$ conventional-semver --from 1.4.0
1.4.3
```

**Using `--major`, `--minor`, and `--patch`** — specify each component individually:

```bash
$ conventional-semver --from 1.4.0
1.4.3

$ conventional-semver --major 1 --minor 4 --patch 0
1.4.3
```

Only `--from` *or* the individual `--major`/`--minor`/`--patch` flags may be used; when both are supplied, `--from` takes precedence.

#### SEMVER Configuration

When run without any command-line arguments a default set of settings are used which implement a standard Conventional Commits behavior.

To customize behavior a configuration file may be created. This file can be passed in using a `--config` argument, or, placed into one of the following well-known locations (and in the following order):

* `~/.config/conventional-semver/settings.conf` (user profile `.config` directory.)
* `/etc/conventional-semver/settings.conf` (root `/etc` directory.)

> **NOTE:** Loading a `conventional-semver.conf` from inside the repo (the working directory) became opt-in behavior with the 2.0.0 release. Use `--config` to load a configuration file from the repo being processed.

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
breaks:=major


# in each of the above sections, each line
# represents a key-value pair. the key is a regex
# and the value is a component type to be
# incremented if the regex is a match.
```

There is a sample configuration file located in this repo as `configs/conventional-semver.conf` which contains additional comments and explanations, you can customize it to fit your needs and then place it at one of the well-known locations mentioned above.

## Generating CHANGELOG

To generate a CHANGELOG you specify the `--changelog [filename]` switch, this takes an optional filename argument. If no filename is provided a default filename of `CHANGELOG.md` is used to emit a file into the current working directory.

Example:

```bash
$ conventional-semver --changelog
```

```bash
$ conventional-semver --changelog CHANGELOG.md
```

### CHANGELOG Templates

The CHANGELOG output is defined as a single template, this is meant to provide enough flexibility that you could emit templates in various structured formats such as XML, JSON, Markdown, reStructuredText, etc.

The default template is built-in, and is designed to produce a file that is markdown-friendly.

To specify a custom template, supply an additional `--changelog-template <template path>` argument that indicates where the template can be found:

```bash
$ conventional-semver --changelog --changelog-template ./templates/template_name.j2
```

```bash
$ conventional-semver --changelog ./CHANGELOG.rst --changelog-template ./templates/template_name.j2
```

#### Jinja2

Templates are Jinja2-based, offering a powerful feature set and a syntax familiar to the Python community.

##### Variables

Templates are provided a data dict having the following structure:

```json
{
    "name": <derived from the repo directory basename>,
    "semver": <most recent semver computed from the log>,
    "date": <today's date>,
    "hash": <git hash of the most recent commit>,
    "versions": [
        {
            "semver": <semver of the version group>,
            "commits": [
                {
                    "date": <commit date>,
                    "hash": <short git hash>,
                    "type": <the `type` parsed from the commit message>,
                    "scope": <the `scope` parsed from the commit message>,
                    "header": <the first line parsed from the commit message, sans `type` and `scope`>,
                    "body": <optional, the `body` lines parsed from the commit message, if defined>,
                    "footers": <optional, the footer lines parsed from the commit message, as a list of strings>,
                    "commit_url": <optional, full commit URL when --commit-url is set>
                }
            ]
        }
    ]
}
```

For each SEMVER increment a `"versions"` entry is provided. A single semver increment may be the result of multiple commits, and so `"commits"` is an array of all commits related to the semver increment.  Typically, this will be a 1-to-1 relationship, but it depends on the practices and patterns of the developer/organization.

##### Example

The built-in template looks approximately like this:

```jinja2
{% for version in versions %}
#### {{ version.semver }}
{% for commit in version.commits %}
- {{ commit.type }}{% if commit.scope %}({{ commit.scope }}){% endif %}: {{ commit.header }} {% if commit.commit_url is defined %}
[{{ commit.hash }}]({{ commit.commit_url }}){% endif %} {% if commit.body is defined %}
{{ commit.body }}
{% if commit.footers is defined %}
{% for footer in commit.footers %}> {{ footer }}
{%- endfor -%}{% endif %}{% else %}

{% endif %}
{%- endfor -%}{%- endfor -%}
```
