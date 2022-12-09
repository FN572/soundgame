# -*- coding: utf-8 -*-
"""Prompt formatter for simple version control branches"""
# pylint:disable=no-member, invalid-name

import os
import sys
import queue
import builtins
import threading
import subprocess

import xonsh.tools as xt


def _get_git_branch(q):
    denv = builtins.__xonsh__.env.detype()
    try:
        branches = xt.decode_bytes(
            subprocess.check_output(
                ["git", "branch"], env=denv, stderr=subprocess.DEVNULL
            )
        ).splitlines()
    except (subprocess.CalledProcessError, OSError, FileNotFoundError):
        q.put(None)
    else:
        for branch in branches:
            if not branch.startswith("* "):
                continue
            elif branch.endswith(")"):
                branch = branch.split()[-1][:-1]
            else:
                branch = branch.split()[-1]

            q.put(branch)
            break
        else:
            q.put(None)


def get_git_branch():
    """Attempts to find the current git branch. If this could not
    be determined (timeout, not in a git repo, etc.) then this returns None.
    """
    branch = None
    timeout = builtins.__xonsh__.env.get("VC_BRANCH_TIMEOUT")
    q = queue.Queue()

    t = threading.Thread(target=_get_git_branch, args=(q,))
    t.start()
    t.join(timeout=timeout)
    try:
        branch = q.get_nowait()
    except queue.Empty:
        branch = None
    return branch


def _get_hg_root(q):
    _curpwd = builtins.__xonsh__.env["PWD"]
    while True:
        if not os.path.isdir(_curpwd):
            return False
        if any([b.name == ".hg" for b in xt.scandir(_curpwd)]):
            q.put(_curpwd)
            break
        else:
            _oldpwd = _curpwd
            _curpwd = os.path.split(_curpwd)[0]
            if _oldpwd == _curpwd:
                return False


def get_hg_branch(root=None):
    """Try to get the mercurial branch of the current directory,
    return None if not in a repo or subprocess.TimeoutExpired if timed out.
    """
    env = builtins.__xonsh__.env
    timeout = env["VC_BRANCH_TIMEOUT"]
    q = queue.Queue()
    t = threading.Thread(target=_get_hg_root, args=(q,))
    t.start()
    t.join(timeout=timeout)
    try:
        root = q.get_nowait()
    except queue.Empty:
        return None
    if env.get("VC_HG_SHOW_BRANCH"):
        # get branch name
        branch_path = os.path.sep.join([root, ".hg", "branch"])
        if os.path.exists(branch_path):
            with open(branch_path, "r") as branch_file:
                branch = branch_file.read()
        else:
            branch = "default"
    else:
        branch = ""
    # add bookmark, if we can
    bookmark_path = os.path.sep.join([root, ".hg", "bookmarks.current"])
    if os.path.exist