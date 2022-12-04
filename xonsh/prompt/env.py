# -*- coding: utf-8 -*-
"""Prompt formatter for virtualenv and others"""

import os
import builtins

import xonsh.platform as xp


def find_env_name():
    """Finds the current environment name from $VIRTUAL_ENV or
    $CONDA_DEFAULT_ENV if that is set.
    """
    env_path = builtins.__xonsh__.env.get("VIRTUAL_ENV", "")
    if len(env_path) == 0 and xp.ON_ANACONDA:
        env_path = builtins.__xonsh__.env.get("CONDA_DEFAULT_ENV", "")
    env_name = os.path.basename(env_path)
    return env_name


def env_name():
    """Returns the current env_name if it non-empty, surrounded by the
    ``{env_prefix}`` and ``{env_postfix}`` fields.
    """
    env_name = find_env_name()
    if (
        builti