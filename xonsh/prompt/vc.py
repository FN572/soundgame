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
            subprocess.che