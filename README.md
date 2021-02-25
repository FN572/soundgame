<p align="center">
  <img src="http://i.imgur.com/0SXZ90y.gif">
</p>
<p align="center">
  An <a href="https://github.com/works-with/category/desktop-tools">Official Integration</a> for GitHub and <a href="#for-github-enterprise-users">GitHub Enterprise</a>.
</p>

gitsome
=======

[![Build Status](https://travis-ci.org/donnemartin/gitsome.svg?branch=master)](https://travis-ci.org/donnemartin/gitsome) [![PyPI version](https://badge.fury.io/py/gitsome.svg)](http://badge.fury.io/py/gitsome) [![PyPI](https://img.shields.io/pypi/pyversions/gitsome.svg)](https://pypi.python.org/pypi/gitsome/) [![License](https://img.shields.io/:license-apache-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)

## Why `gitsome`?

### The Git Command Line

Although the standard Git command line is a great tool to manage your Git-powered repos, it can be **tough to remember the usage** of:

* 150+ porcelain and plumbing commands
* Countless command-specific options
* Resources such as tags and branches

The Git command line **does not integrate with GitHub**, forcing you to toggle between command line and browser.

## `gitsome` - A Supercharged Git/GitHub CLI With Autocomplete

<p align="center">
  <img src="https://raw.githubusercontent.com/donnemartin/gitsome/develop/images/logo.png">
</p>

`gitsome` aims to supercharge your standard git/shell interface by focusing on:

* **Improving ease-of-use**
* **Increasing productivity**

### Deep GitHub Integration

Not all GitHub workflows work well in a terminal; `gitsome` attempts to target those that do.

`gitsome` includes 29 GitHub integrated commands that work with **[ALL](#enabling-gh-tab-completions-outside-of-gitsome)** shells:

    $ gh <command> [param] [options]

* [Quick reference](#github-integration-commands-quick-reference)
* [General reference](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md)

Run `gh` commands along with [Git-Extras](https://github.com/tj/git-extras/blob/master/Commands.md) and [hub](https://hub.github.com/) commands to unlock even more GitHub integrations!

![Imgur](http://i.imgur.com/sG09AJH.png)

### Git and GitHub Autocompleter With Interactive Help

You can run the <u>**optional**</u> shell:

     $ gitsome

to enable **autocompletion** and **interactive help** for the following:

* Git commands
* Git options
* Git branches, tags, etc
* [Git-Extras commands](https://github.com/tj/git-extras/blob/master/Commands.md)
* [GitHub integration commands](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md)

![Imgur](http://i.imgur.com/08OMNjz.png)

![Imgur](http://i.imgur.com/fHjMwlh.png)

### General Autocompleter

`gitsome` autocompletes the following:

* Shell commands
* Files and directories
* Environment variables
* Man pages
* Python

To enable additional autocompletions, check out the [Enabling Bash Completions](#enabling-bash-completions) section.

![Imgur](http://i.imgur.com/hg1dpk6.png)

## Fish-Style Auto-Suggestions

`gitsome` supports Fish-style auto-suggestions.  Use the `right arrow` key to complete a suggestion.

![Imgur](http://i.imgur.com/ZRaFGpY.png)

## Python REPL

`gitsome` is powered by [`xonsh`](https://github.com/scopatz/xonsh), which supports a Python REPL.

Run Python commands alongside shell commands:

![Imgur](http://i.imgur.com/NYk7WYO.png)

Additional `xonsh` features can be found in the [`xonsh tutorial`](http://xon.sh/tutorial.html).

## Command History

`gitsome` keeps track of commands you enter and stores them in `~/.xonsh_history.json`.  Use the up and down arrow keys to cycle through the command history.

![Imgur](http://i.imgur.com/wq0caZu.png)

## Customizable Highlighting

You can control the ansi colors used for highlighting by updating your `~/.gitsomeconfig` file.

Color options include:

```
'black', 'red', 'green', 'yellow',
'blue', 'magenta', 'cyan', 'white'
```

For no color, set the value(s) to `None`.  `white` can appear as light gray on some terminals.

![Imgur](http://i.imgur.com/BN1lfEf.png)

## Available Platforms

`gitsome` is available for Mac, Linux, Unix, [Windows](#windows-support), and [Docker](#running-as-docker-container).

## TODO

>Not all GitHub workflows work well in a terminal; `gitsome` attempts to target those that do.

* Add additional GitHub API integrations

`gitsome` is just getting started.  Feel free to [contribute!](#contributing)

## Index

### GitHub Integration Commands

* [GitHub Integration Commands Syntax](#github-integration-commands-syntax)
* [GitHub Integration Commands Listing](#github-integration-commands-listing)
* [GitHub Integration Commands Quick Reference](#github-integration-commands-quick-reference)
* [GitHub Integration Commands Reference in COMMANDS.md](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md)
    * [`gh configure`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-configure)
    * [`gh create-comment`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-create-comment)
    * [`gh create-issue`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-create-issue)
    * [`gh create-repo`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-create-repo)
    * [`gh emails`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-emails)
    * [`gh emojis`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-emojis)
    * [`gh feed`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-feed)
    * [`gh followers`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-followers)
    * [`gh following`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-following)
    * [`gh gitignore-template`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-gitignore-template)
    * [`gh gitignore-templates`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-gitignore-templates)
    * [`gh issue`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-issue)
    * [`gh issues`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-issues)
    * [`gh license`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-license)
    * [`gh licenses`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-licenses)
    * [`gh me`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-me)
    * [`gh notifications`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-notifications)
    * [`gh octo`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-octo)
    * [`gh pull-request`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-pull-request)
    * [`gh pull-requests`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-pull-requests)
    * [`gh rate-limit`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-rate-limit)
    * [`gh repo`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-repo)
    * [`gh repos`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-repos)
    * [`gh search-issues`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-search-issues)
    * [`gh search-repos`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-search-repos)
    * [`gh starred`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-starred)
    * [`gh trending`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-trending)
    * [`gh user`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-user)
    * [`gh view`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-view)
* [Option: View in a Pager](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#option-view-in-a-pager)
* [Option: View in a Browser](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#option-view-in-a-browser)

### Installation and Tests

* [Installation](#installation)
    * [Pip Installation](#pip-installation)
    * [Virtual Environment Installation](#virtual-environment-installation)
    * [Running as a Docker Container](#running-as-a-docker-container)
    * [Running the `gh configure` Command](#running-the-gh-configure-command)
        * [For GitHub Enterprise Users](#for-github-enterprise-users)
    * [Enabling Bash Completions](#enabling-bash-completions)
    * [Enabling `gh` Tab Completions Outside of `gitsome`](#enabling-gh-tab-completions-outside-of-gitsome)
        * [For Zsh Users](#for-zsh-users)
    * [Optional: Installing `PIL` or `Pillow`](#optional-installing-pil-or-pillow)
    * [Supported Python Versions](#supported-python-versions)
    * [Supported Platforms](#supported-platforms)
    * [Windows Support](#windows-support)
* [Developer Installation](#developer-installation)
    * [Continuous Integration](#continuous-integration)
    * [Unit Tests and Code Coverage](#unit-tests-and-code-coverage)
    * [Documentation](#documentation)

### Misc

* [Contributing](#contributing)
* [Credits](#credits)
* [Contact Info](#contact-info)
* [License](#license)

## GitHub Integration Commands Syntax

Usage:

    $ gh <command> [param] [options]

## GitHub Integration Commands Listing

```
  configure            Configure gitsome.
  create-comment       Create a comment on the given issue.
  create-issue         Create an issue.
  create-repo          Create a repo.
  emails               List all the user's registered emails.
  emojis               List all GitHub supported emojis.
  feed                 List all activity for the given user or repo.
  followers  