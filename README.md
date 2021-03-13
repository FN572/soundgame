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
  followers            List all followers and the total follower count.
  following            List all followed users and the total followed count.
  gitignore-template   Output the gitignore template for the given language.
  gitignore-templates  Output all supported gitignore templates.
  issue                Output detailed information about the given issue.
  issues               List all issues matching the filter.
  license              Output the license template for the given license.
  licenses             Output all supported license templates.
  me                   List information about the logged in user.
  notifications        List all notifications.
  octo                 Output an Easter egg or the given message from Octocat.
  pull-request         Output detailed information about the given pull request.
  pull-requests        List all pull requests.
  rate-limit           Output the rate limit.  Not available for Enterprise.
  repo                 Output detailed information about the given filter.
  repos                List all repos matching the given filter.
  search-issues        Search for all issues matching the given query.
  search-repos         Search for all repos matching the given query.
  starred              Output starred repos.
  trending             List trending repos for the given language.
  user                 List information about the given user.
  view                 View the given index in the terminal or a browser.
```

## GitHub Integration Commands Reference: COMMANDS.md

See the [GitHub Integration Commands Reference in COMMANDS.md](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md) for a **detailed discussion** of all GitHub integration commands, parameters, options, and examples.

Check out the next section for a **quick reference**.

## GitHub Integration Commands Quick Reference

### Configuring `gitsome`

To properly integrate with GitHub, you must first configure `gitsome`:

    $ gh configure

For GitHub Enterprise users, run with the `-e/--enterprise` flag:

    $ gh configure -e

### Listing Feeds

#### Listing Your News Feed

    $ gh feed

![Imgur](http://i.imgur.com/2LWcyS6.png)

#### Listing A User's Activity Feed

View your activity feed or another user's activity feed, optionally through a pager with `-p/--pager`.  The [pager option](#option-view-in-a-pager) is available for many commands.

    $ gh feed donnemartin -p

![Imgur](http://i.imgur.com/kryGLXz.png)

#### Listing A Repo's Activity Feed

    $ gh feed donnemartin/gitsome -p

![Imgur](http://i.imgur.com/d2kxDg9.png)

### Listing Notifications

    $ gh notifications

![Imgur](http://i.imgur.com/uwmwxsW.png)

### Listing Pull Requests

View all pull requests for your repos:

    $ gh pull-requests

![Imgur](http://i.imgur.com/4A2eYM9.png)

### Filtering Issues

View all open issues where you have been mentioned:

    $ gh issues --issue_state open --issue_filter mentioned

![Imgur](http://i.imgur.com/AB5zxxo.png)

View all issues, filtering for only those assigned to you, regardless of state (open, closed):

    $ gh issues --issue_state all --issue_filter assigned

For more information about the filter and state qualifiers, visit the [`gh issues`](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md#gh-issues) reference in [COMMANDS.md](https://github.com/donnemartin/gitsome/blob/master/COMMANDS.md).

### Filtering Starred Repos

    $ gh starred "repo filter"

![Imgur](http://i.imgur.com/JB88Kw8.png)

### Searching Issues and Repos

#### Searching Issues

Search issues that have the most +1s:

    $ gh search-issues "is:open is:issue sort:reactions-+1-desc" -p

![Imgur](http://i.imgur.com/DXXxkBD.png)

Search issues that have the most comments:

    $ gh search-issues "is:open is:issue sort:comments-desc" -p

Search issues with the "help wanted" tag:

    $ gh search-issues "is:open is:issue label:\"help wanted\"" -p

Search issues that have your user name tagged **@donnemartin**:

    $ gh search-issues "is:issue donnemartin is:open" -p

Search all your open private issues:

    $ gh search-issues "is:open is:issue is:private" -p

For more information about the query qualifiers, visit the [searching issues reference](https://help.github.com/articles/searching-issues/).

#### Searching Repos

Search all Python repos created on or after 2015, with >= 1000 stars:

    $ gh search-repos "created:>=2015-01-01 stars:>=1000 language:python" --sort stars -p

![Imgur](http://i.imgur.com/kazXWWY.png)

For more information about the query qualifiers, visit the [searching repos reference](https://help.github.com/articles/searching-repositories/).

### Listing Trending Repos and Devs

View trending repos:

    $ gh trending [language] [-w/--weekly] [-m/--monthly] [-d/--devs] [-b/--browser]

![Imgur](http://i.imgur.com/aa1gOg7.png)

View trending devs (devs are currently only supported in browser):

    $ gh trending [language] --devs --browser

### Viewing Content

#### The `view` command

View the previously listed notifications, pull requests, issues, repos, users etc, with HTML nicely formatted for your terminal, or optionally in your browser:

    $ gh view [#] [-b/--browser]

![Imgur](http://i.imgur.com/NVEwGbV.png)

#### The `issue` command

View an issue:

    $ gh issue donnemartin/saws/1

![Imgur](http://i.imgur.com/ZFv9MuV.png)

#### The `pull-request` command

View a pull request:

    $ gh pull-request donnemartin/awesome-aws/2

![Imgur](http://i.imgur.com/3MtKjKy.png)

### Setting Up `.gitignore`

List all available `.gitignore` templates:

    $ gh gitignore-templates

![Imgur](http://i.imgur.com/u8qYx1s.png)

Set up your `.gitignore`:

    $ gh gitignore-template Python > .gitignore

![Imgur](http://i.imgur.com/S5m5ZcO.png)

### Setting Up `LICENSE`

List all available `LICENSE` templates:

    $ gh licenses

![Imgur](http://i.imgur.com/S9SbMLJ.png)

Set up your  or `LICENSE`:

    $ gh license MIT > LICENSE

![Imgur](http://i.imgur.com/zJHVxaA.png)

### Summoning Octocat

Call on Octocat to say the given message or an Easter egg:

    $ gh octo [say]

![Imgur](http://i.imgur.com/bNzCa5p.png)

### Viewing Profiles

#### Viewing A User's Profile

    $ gh user octocat

![Imgur](http://i.imgur.com/xVoVPVe.png)

#### Viewing Your Profile

View your profile with the `gh user [YOUR_USER_ID]` command or with the following shortcut:

    $ gh me

![Imgur](http://i.imgur.com/csk5j0S.png)

### Creating Comments, Issues, and Repos

Create a comment:

    $ gh create-comment donnemartin/gitsome/1 -t "hello world"

Create an issue:

    $ gh create-issue donnemartin/gitsome -t "title" -b "body"

Create a repo:

    $ gh create-repo gitsome

### Option: View in a Pager

Many `gh` commands support a `-p/--pager` option that displays results in a pager, where available.

Usage:

    $ gh <command> [param] [options] -p
    $ gh <command> [param] [options] --pager

### Option: View in a Browser

Many `gh` commands support a `-