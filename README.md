
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
        --changelog <file>  overrides the name of the file the changelog is written to, otherwise changelog.md is the default.
        --no-semver         disable SEMVER output to STDOUT.
        --major             SEMVER Major component will start with this value, default is 0.
        --minor             SEMVER Minor component will start with this value, default is 0.
        --patch             SEMVER Patch component will start with this value, default is 0.
        --git-path <path>   overrides the path to `git` tool, otherwise `git` must be in environment PATH.

Parameters:
        repo-path           the path of the git repository to process, if not specified defaults to working directory.
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

Projects adopting Conventional Commits may need to customize the baseline SEMVER, rather than starting from `0.0.0`. This can be done with the `--major`, `--minor`, and `--patch` arguments.

When run on a repo containing three non-conventional commits:

```bash
$ conventional-semver --major 1 --minor 2 --patch 3
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
$ conventional-semver --changelog
```

```bash
$ conventional-semver --changelog CHANGELOG.md
```

#### CHANGELOG Templates

The CHANGELOG output is defined as a single template, this is meant to provide enough flexibility that you could emit templates in various structured formats such as XML, JSON, Markdown, reStructuredText, etc.

The default template is built-in, and is designed to produce a file that is markdown-friendly.

To specify a custom template, supply an additional `--changelog-template <template path>` argument that indicates where the template can be found:

```bash
$ conventional-semver --changelog --template ./templates/template_name.j2
```

```bash
$ conventional-semver --changelog ./CHANGELOG.rst --template ./templates/template_name.j2
```

##### Jinja2

Templates are Jinja2-based, offering a powerful feature set and a syntax familiar to the Python community.

###### Variables

Templates are provided a data dict having the following structure:

```json
{
    "name": <derived from working directory basename>,
    "semver": <semver of most recent commit>,
    "date": <date of most recent commit>,
    "hash": <git hash of most recent commit>,
    "versions": [
        {
            "semver": <semver of commit>,
            "commits": [
                {
                    "date": <commit date>,
                    "hash": <commit hash>,
                    "message": <original commit message>,
                    "type": <the `type` parsed from commit message>,
                    "scope": <the `scope` parsed from commit message>,
                    "header": <the first line parsed from the commit message, sans `type` and `scope`>,
                    "body": <optional, the `body` lines parsed from the commit message, if defined>,
                    "footers": <optional, the `trailing` lines parsed from the commit message, if defined>
                }
            ]
        }
    ]
}
```

For each SEMVER increment a `"versions"` entry is provided. A single semver increment may be the result of multiple commits, and so `"commits"` is an array of all commits related to the semver increment.  Typically, this will be a 1-to-1 relationship, but it depends on the practices and patterns of the developer/organization.

###### Example

The built-in template looks approximately like this:

```jinja2
        {% for version in versions %}
        #### {{ version.semver }}
        {% for commit in version.commits %}
        - {{ commit.type }}({{ commit.scope }}): {{ commit.header }}{% if commit.body is defined %}
        {{ commit.body }}
        {% if commit.footers is defined %}
        > {{ commit.footers }}{% endif %}{% else %}
        {% endif %}
        {%- endfor -%}{%- endfor -%}
```
