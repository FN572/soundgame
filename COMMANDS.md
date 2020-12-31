# Commands

## GitHub Integration Commands Reference

Check out the handy [autocompleter with interactive help](https://github.com/donnemartin/gitsome/blob/master/README.md#git-and-github-autocompleter-with-interactive-help) to guide you through each command.

### gh configure

Configure `gitsome`.

Attempts to authenticate the user and to set up the user's news feed.

If `gitsome` has not yet been configured, calling a `gh` command that requires authentication will automatically invoke the `configure` command.

Usage/Example(s):

    $ gh configure

For GitHub Enterprise users, run with the `-e/--enterprise` flag:

    $ gh configure -e

#### Authentication

To properly integrate with GitHub, you will be asked to enter a user name and either a password or a [personal access token](https://github.com/settings/tokens).  If you use two-factor authentication, you will also need to enter your 2FA code, or you can log in with a personal access token.

Visit the following page to generate a token:

[https://github.com/settings/tokens](https://github.com/settings/tokens)

`gitsome` will need the 'repo' and 'user' permissions.

![Imgur](http://i.imgur.com/1C7gBHz.png)

#### GitHub Enterprise

GitHub Enterprise users will be asked to enter the GitHub Enterprise url and whether they want to verify SSL certificates.

#### Authentication Source Code

Curious what's going on behind the scenes with authentication?  Check out the [authentication source code](https://github.com/donnemartin/gitsome/blob/master/gitsome/config.py#L177-L328).

#### User Feed

`gitsome` will need your news feed url to run the `gh feed` command with no arguments.

![Imgur](http://i.imgur.com/2LWcyS6.png)

To integrate `gitsome` with your news feed, visit the following url while logged into GitHub:

[https://github.com](https://github.com)

You will be asked to enter the url found when clicking 'Subscribe to your news feed', which will look something like this:

    https://github.com/donnemartin.private.atom?token=TOKEN

![Imgur](http://i.imgur.com/f2zvdIm.png)

### gh create-comment

Create a comment on the given issue.

Usage:

    $ gh create-comment [user_repo_number] [-t/--text]

Param(s):

```
:type user_repo_number: str
:param user_repo_number: The user/repo/issue_number.
```

Option(s):

```
:type text: str
:param text: The comment text.
```

Example(s):

    $ gh create-comment donnemartin/saws/1 -t "hello world"
    $ gh create-comment donnemartin