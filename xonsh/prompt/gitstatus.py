# -*- coding: utf-8 -*-
"""Informative git status prompt formatter"""

import builtins
import collections
import os
import subprocess

import xonsh.lazyasd as xl


GitStatus = collections.namedtuple(
    "GitStatus",
    [
        "branch",
        "num_ahead",
        "num_behind",
        "untracked",
        "changed",
        "conflicts",
        "staged",
        "stashed",
        "operations",
    ],
)


def _check_output(*args, **kwargs):
    kwargs.update(
        dict(
            env=builtins.__xonsh__.env.detype(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        )
    )
    timeout = builtins.__xonsh__.env["VC_BRANCH_TIMEOUT"]
    # See https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
    with subprocess.Popen(*args, **kwargs) as proc:
        try:
            out, err = proc.communicate(timeout=timeout)
            if proc.returncode != 0:
                raise subprocess.CalledProcessError(
                    proc.returncode, proc.args, output=out, stderr=err
                )  # note err will always be empty as we redirect stderr to DEVNULL abvoe
            return out
        except subprocess.TimeoutExpired:
            # We use `.terminate()` (SIGTERM) instead of `.kill()` (SIGKILL) here
            # because otherwise we guarantee that a `.git/index.lock` file will be
            # left over, and subsequent git operations will fail.
            # We don't want that.
            # As a result, we must rely on git to exit properly on SIGTERM.
            proc.terminate()
            # We wait() to ensure that git has finished before the next
            # `gitstatus` prompt is rendered (otherwise `index.lock` still exists,
            # and it will fail).
            # We don't technically have to call `wait()` here as the
            # `with subprocess.Popen()` context manager above would do that
            # for us, but we do it to be explicit that waiting is being done.
            proc.wait()  # we ignore what git says after we sent it SIGTERM
            raise


@xl.lazyobject
def _DEFS():
    DEFS = {
        "HASH": ":",
        "BRANCH": "{CYAN}",
        "OPERATION": "{CYAN}",
        "STAGED": "{RED}●",
        "CONFLICTS": "{RED}×",
        "CHANGED": "{BLUE}+",
        "UNTRACKED": "…",
        "STASHED": "⚑",
        "CLEAN": "{BOLD_GREEN}✓",
        "AHEAD": "↑·",
        "BEHIND": "↓·",
    }
    return DEFS


def _get_def(key):
    def_ = builtins.__xonsh__.env.get("XONSH_GITSTATUS_" + 