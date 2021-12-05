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

Fires after an