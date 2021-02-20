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

*