# -*- coding: utf-8 -*-
"""Environment for the xonsh shell."""
import os
import re
import sys
import pprint
import textwrap
import locale
import builtins
import warnings
import contextlib
import collections
import collections.abc as cabc
import subprocess

from xonsh import __version__ as XONSH_VERSION
from xonsh.lazyasd import LazyObject, lazyobject
from xonsh.codecache import run_script_with_cache
from xonsh.dirstack import _get_cwd
from xonsh.events import events
from xonsh.platform import (
    BASH_COMPLETIONS_DEFAULT,
    DEFAULT_ENCODING,
    PATH_DEFAULT,
    ON_WINDOWS,
    ON_LINUX,
    os_environ,
)

from xonsh.style_tools import PTK2_STYLE

from xonsh.tools import (
    always_true,
    always_false,
    detype,
    ensure_string,
    is_env_path,
    str_to_env_path,
    env_path_to_str,
    is_bool,
    to_bool,
    bool_to_str,
    is_history_tuple,
    to_history_tuple,
    history_tuple_to_str,
    is_float,
    is_string,
    is_string_or_callable,
    is_completions_display_value,
    to_completions_display_value,
    is_string_set,
    csv_to_set,
    set_to_csv,
    is_int,
    is_bool_seq,
    to_bool_or_int,
    bool_or_int_to_str,
    csv_to_bool_seq,
    bool_seq_to_csv,
    DefaultNotGiven,
    print_exception,
    setup_win_unicode_console,
    intensify_colors_on_win_setter,
    is_dynamic_cwd_width,
    to_dynamic_cwd_tuple,
    dynamic_cwd_tuple_to_str,
    is_logfile_opt,
    to_logfile_opt,
    logfile_opt_to_str,
    executables_in,
    is_nonstring_seq_of_strings,
    pathsep_to_upper_seq,
    seq_to_upper_pathsep,
    print_color,
    is_history_backend,
    to_itself,
    swap_values,
    ptk2_color_depth_setter,
    is_str_str_dict,
    to_str_str_dict,
    dict_to_str,
)
from xonsh.ansi_colors import (
    ansi_color_escape_code_to_name,
    ansi_reverse_style,
    ansi_style_by_name,
)
import xonsh.prompt.base as prompt


events.doc(
    "on_envvar_new",
    """
on_envvar_new(name: str, value: Any) -> None

Fires after a new environment variable is created.
Note: Setting envvars inside the handler might
cause a recursion until the limit.
""",
)


events.doc(
    "on_envvar_change",
    """
on_envvar_change(name: str, oldvalue: Any, newvalue: Any) -> None

Fires after an environment variable is changed.
Note: Setting envvars inside the handler might
cause a recursion until the limit.
""",
)


events.doc(
    "on_pre_spec_run_ls",
    """
on_pre_spec_run_ls(spec: xonsh.built_ins.SubprocSpec) -> None

Fires right before a SubprocSpec.run() is called for the ls
command.
""",
)


@lazyobject
def HELP_TEMPLATE():
    return (
        "{{INTENSE_RED}}{envvar}{{NO_COLOR}}:\n\n"
        "{{INTENSE_YELLOW}}{docstr}{{NO_COLOR}}\n\n"
        "default: {{CYAN}}{default}{{NO_COLOR}}\n"
        "configurable: {{CYAN}}{configurable}{{NO_COLOR}}"
    )


@lazyobject
def LOCALE_CATS():
    lc = {
        "LC_CTYPE": locale.LC_CTYPE,
        "LC_COLLATE": locale.LC_COLLATE,
        "LC_NUMERIC": locale.LC_NUMERIC,
        "LC_MONETARY": locale.LC_MONETARY,
        "LC_TIME": locale.LC_TIME,
    }
    if hasattr(locale, "LC_MESSAGES"):
        lc["LC_MESSAGES"] = locale.LC_MESSAGES
    return lc


def locale_convert(key):
    """Creates a converter for a locale key."""

    def lc_converter(val):
        try:
            locale.setlocale(LOCALE_CATS[key], val)
            val = locale.setlocale(LOCALE_CATS[key])
        except (locale.Error, KeyError):
            msg = "Failed to set locale {0!r} to {1!r}".format(key, val)
            warnings.warn(msg, RuntimeWarning)
        return val

    return lc_converter


def to_debug(x):
    """Converts value using to_bool_or_int() and sets this value on as the
    execer's debug level.
    """
    val = to_bool_or_int(x)
    if (
        hasattr(builtins, "__xonsh__")
        and hasattr(builtins.__xonsh__, "execer")
        and builtins.__xonsh__.execer is not None
    ):
        builtins.__xonsh__.execer.debug_level = val
    return val


#
# $LS_COLORS tools
#


class LsColors(cabc.MutableMapping):
    """Helps convert to/from $LS_COLORS format, respecting the xonsh color style.
    This accepts the same inputs as dict().
    """

    default_settings = {
        "*.7z": ("BOLD_RED",),
        "*.Z": ("BOLD_RED",),
        "*.aac": ("CYAN",),
        "*.ace": ("BOLD_RED",),
        "*.alz": ("BOLD_RED",),
        "*.arc": ("BOLD_RED",),
        "*.arj": ("BOLD_RED",),
        "*.asf": ("BOLD_PURPLE",),
        "*.au": ("CYAN",),
        "*.avi": ("BOLD_PURPLE",),
        "*.bmp": ("BOLD_PURPLE",),
        "*.bz": ("