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
        "*.bz": ("BOLD_RED",),
        "*.bz2": ("BOLD_RED",),
        "*.cab": ("BOLD_RED",),
        "*.cgm": ("BOLD_PURPLE",),
        "*.cpio": ("BOLD_RED",),
        "*.deb": ("BOLD_RED",),
        "*.dl": ("BOLD_PURPLE",),
        "*.dwm": ("BOLD_RED",),
        "*.dz": ("BOLD_RED",),
        "*.ear": ("BOLD_RED",),
        "*.emf": ("BOLD_PURPLE",),
        "*.esd": ("BOLD_RED",),
        "*.flac": ("CYAN",),
        "*.flc": ("BOLD_PURPLE",),
        "*.fli": ("BOLD_PURPLE",),
        "*.flv": ("BOLD_PURPLE",),
        "*.gif": ("BOLD_PURPLE",),
        "*.gl": ("BOLD_PURPLE",),
        "*.gz": ("BOLD_RED",),
        "*.jar": ("BOLD_RED",),
        "*.jpeg": ("BOLD_PURPLE",),
        "*.jpg": ("BOLD_PURPLE",),
        "*.lha": ("BOLD_RED",),
        "*.lrz": ("BOLD_RED",),
        "*.lz": ("BOLD_RED",),
        "*.lz4": ("BOLD_RED",),
        "*.lzh": ("BOLD_RED",),
        "*.lzma": ("BOLD_RED",),
        "*.lzo": ("BOLD_RED",),
        "*.m2v": ("BOLD_PURPLE",),
        "*.m4a": ("CYAN",),
        "*.m4v": ("BOLD_PURPLE",),
        "*.mid": ("CYAN",),
        "*.midi": ("CYAN",),
        "*.mjpeg": ("BOLD_PURPLE",),
        "*.mjpg": ("BOLD_PURPLE",),
        "*.mka": ("CYAN",),
        "*.mkv": ("BOLD_PURPLE",),
        "*.mng": ("BOLD_PURPLE",),
        "*.mov": ("BOLD_PURPLE",),
        "*.mp3": ("CYAN",),
        "*.mp4": ("BOLD_PURPLE",),
        "*.mp4v": ("BOLD_PURPLE",),
        "*.mpc": ("CYAN",),
        "*.mpeg": ("BOLD_PURPLE",),
        "*.mpg": ("BOLD_PURPLE",),
        "*.nuv": ("BOLD_PURPLE",),
        "*.oga": ("CYAN",),
        "*.ogg": ("CYAN",),
        "*.ogm": ("BOLD_PURPLE",),
        "*.ogv": ("BOLD_PURPLE",),
        "*.ogx": ("BOLD_PURPLE",),
        "*.opus": ("CYAN",),
        "*.pbm": ("BOLD_PURPLE",),
        "*.pcx": ("BOLD_PURPLE",),
        "*.pgm": ("BOLD_PURPLE",),
        "*.png": ("BOLD_PURPLE",),
        "*.ppm": ("BOLD_PURPLE",),
        "*.qt": ("BOLD_PURPLE",),
        "*.ra": ("CYAN",),
        "*.rar": ("BOLD_RED",),
        "*.rm": ("BOLD_PURPLE",),
        "*.rmvb": ("BOLD_PURPLE",),
        "*.rpm": ("BOLD_RED",),
        "*.rz": ("BOLD_RED",),
        "*.sar": ("BOLD_RED",),
        "*.spx": ("CYAN",),
        "*.svg": ("BOLD_PURPLE",),
        "*.svgz": ("BOLD_PURPLE",),
        "*.swm": ("BOLD_RED",),
        "*.t7z": ("BOLD_RED",),
        "*.tar": ("BOLD_RED",),
        "*.taz": ("BOLD_RED",),
        "*.tbz": ("BOLD_RED",),
        "*.tbz2": ("BOLD_RED",),
        "*.tga": ("BOLD_PURPLE",),
        "*.tgz": ("BOLD_RED",),
        "*.tif": ("BOLD_PURPLE",),
        "*.tiff": ("BOLD_PURPLE",),
        "*.tlz": ("BOLD_RED",),
        "*.txz": ("BOLD_RED",),
        "*.tz": ("BOLD_RED",),
        "*.tzo": ("BOLD_RED",),
        "*.tzst": ("BOLD_RED",),
        "*.vob": ("BOLD_PURPLE",),
        "*.war": ("BOLD_RED",),
        "*.wav": ("CYAN",),
        "*.webm": ("BOLD_PURPLE",),
        "*.wim": ("BOLD_RED",),
        "*.wmv": ("BOLD_PURPLE",),
        "*.xbm": ("BOLD_PURPLE",),
        "*.xcf": ("BOLD_PURPLE",),
        "*.xpm": ("BOLD_PURPLE",),
        "*.xspf": ("CYAN",),
        "*.xwd": ("BOLD_PURPLE",),
        "*.xz": ("BOLD_RED",),
        "*.yuv": ("BOLD_PURPLE",),
        "*.z": ("BOLD_RED",),
        "*.zip": ("BOLD_RED",),
        "*.zoo": ("BOLD_RED",),
        "*.zst": ("BOLD_RED",),
        "bd": ("BACKGROUND_BLACK", "YELLOW"),
        "ca": ("BLACK", "BACKGROUND_RED"),
        "cd": ("BACKGROUND_BLACK", "YELLOW"),
        "di": ("BOLD_BLUE",),
        "do": ("BOLD_PURPLE",),
        "ex": ("BOLD_GREEN",),
        "ln": ("BOLD_CYAN",),
        "mh": ("NO_COLOR",),
        "mi": ("NO_COLOR",),
        "or": ("BACKGROUND_BLACK", "RED"),
        "ow": ("BLUE", "BACKGROUND_GREEN"),
        "pi": ("BACKGROUND_BLACK", "YELLOW"),
        "rs": ("NO_COLOR",),
        "sg": ("BLACK", "BACKGROUND_YELLOW"),
        "so": ("BOLD_PURPLE",),
        "st": ("WHITE", "BACKGROUND_BLUE"),
        "su": ("WHITE", "BACKGROUND_RED"),
        "tw": ("BLACK", "BACKGROUND_GREEN"),
    }

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._style = self._style_name = None
        self._detyped = None

    def __getitem__(self, key):
        return self._d[key]

    def __setitem__(self, key, value):
        self._detyped = None
        self._d[key] = value

    def __delitem__(self, key):
        self._detyped = None
        del self._d[key]

    def __len__(self):
        return len(self._d)

    def __iter__(self):
        yield from self._d

    def __str__(self):
        return str(self._d)

    def __repr__(self):
        return "{0}.{1}(...)".format(
            self.__class__.__module__, self.__class__.__name__, self._d
        )

    def _repr_pretty_(self, p, cycle):
        name = "{0}.{1}".format(self.__class__.__module__, self.__class__.__name__)
        with p.group(0, name + "(", ")"):
            if cycle:
                p.text("...")
            elif len(self):
                p.break_()
                p.pretty(dict(self))

    def detype(self):
        """De-types the instance, allowing it to be exported to the environment."""
        style = self.style
        if self._detyped is None:
            self._detyped = ":".join(
                [
                    key + "=" + ";".join([style[v] or "0" for v in val])
                    for key, val in sorted(self._d.items())
                ]
            )
        return self._detyped

    @property
    def style_name(self):
        """Current XONSH_COLOR_STYLE value"""
        env = builtins.__xonsh__.env
        env_style_name = env.get("XONSH_COLOR_STYLE")
        if self._style_name is None or self._style_name != env_style_name:
            self._style_name = env_style_name
            self._style = self._dtyped = None
        return self._style_name

    @property
    def style(self):
        """The ANSI color style for the current XONSH_COLOR_STYLE"""
        style_name = self.style_name
        if self._style is None:
            self._style = ansi_style_by_name(style_name)
            self._detyped = None
        return self._style

    @classmethod
    def fromstring(cls, s):
        """Creates a new instance of the LsColors class from a colon-separated
        string of dircolor-valid keys to ANSI color escape sequences.
        """
        obj = cls()
        # string inputs always use default codes, so translating into
        # xonsh names should be done from defaults
        reversed_default = ansi_reverse_style(style="default")
        data = {}
        for item in s.split(":"):
            key, eq, esc = item.partition("=")
            if not eq:
                # not a valid item
                continue
            data[key] = ansi_color_escape_code_to_name(
                esc, "default", reversed_style=reversed_default
            )
        obj._d = data
        return obj

    @classmethod
    def fromdircolors(cls, filename=None):
        """Constructs an LsColors instance by running dircolors.
        If a filename is provided, it is passed down to the dircolors command.
        """
        # assemble command
        cmd = ["dircolors", "-b"]
        if filename is not None:
            cmd.append(filename)
        # get env
        if hasattr(builtins, "__xonsh__") and hasattr(builtins.__xonsh__, "env"):
            denv = builtins.__xonsh__.env.detype()
        else:
            denv = None
        # run dircolors
        try:
            out = subprocess.check_output(
                cmd, env=denv, universal_newlines=True, stderr=subprocess.DEVNULL
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return cls(cls.default_settings)
        s = out.splitlines()[0]
        _, _, s = s.partition("'")
        s, _, _ = s.rpartition("'")
        return cls.fromstring(s)

    @classmethod
    def convert(cls, x):
        """Converts an object to LsColors, if needed."""
        if isinstance(x, cls):
            return x
        elif isinstance(x, str):
            return cls.fromstring(x)
        elif isinstance(x, bytes):
            return cls.fromstring(x.decode())
        else:
            return cls(x)


def is_lscolors(x):
    """Checks if an object is an instance of LsColors"""
    return isinstance(x, LsColors)


@events.on_pre_spec_run_ls
def ensure_ls_colors_in_env(spec=None, **kwargs):
    """This ensures that the $LS_COLORS environment variable is in the
    environment. This fires exactly once upon the first time the
    ls command is called.
    """
    env = builtins.__xonsh__.env
    if "LS_COLORS" not in env._d:
        # this adds it to the env too
        default_lscolors(env)
    events.on_pre_spec_run_ls.discard(ensure_ls_colors_in_env)


#
# Ensurerers
#

Ensurer = collections.namedtuple("Ensurer", ["validate", "convert", "detype"])
Ensurer.__doc__ = """Named tuples whose elements are functions that
represent environment variable validation, conversion, detyping.
"""


@lazyobject
def DEFAULT_ENSURERS():
    return {
        "AUTO_CD": (is_bool, to_bool, bool_to_str),
        "AUTO_PUSHD": (is_bool, to_bool, bool_to_str),
        "AUTO_SUGGEST": (is_bool, to_bool, bool_to_str),
        "AUTO_SUGGEST_IN_COMPLETIONS": (is_bool, to_bool, bool_to_str),
        "BASH_COMPLETIONS": (is_env_path, str_to_env_path, env_path_to_str),
        "CASE_SENSITIVE_COMPLETIONS": (is_bool, to_bool, bool_to_str),
        re.compile(r"\w*DIRS$"): (is_env_path, str_to_env_path, env_path_to_str),
        "COLOR_INPUT": (is_bool, to_bool, bool_to_str),
        "COLOR_RESULTS": (is_bool, to_bool, bool_to_str),
        "COMPLETIONS_BRACKETS": (is_bool, to_bool, bool_to_str),
        "COMPLETIONS_CONFIRM": (is_bool, to_bool, bool_to_str),
        "COMPLETIONS_DISPLAY": (
            is_completions_display_value,
            to_completions_display_value,
            str,
        ),
        "COMPLETIONS_MENU_ROWS": (is_int, int, str),
        "COMPLETION_QUERY_LIMIT": (is_int, int, str),
        "DIRSTACK_SIZE": (is_int, int, str),
        "DOTGLOB": (is_bool, to_bool, bool_to_str),
        "DYNAMIC_CWD_WIDTH": (
            is_dynamic_cwd_width,
            to_dynamic_cwd_tuple,
            dynamic_cwd_tuple_to_str,
        ),
        "DYNAMIC_CWD_ELISION_CHAR": (is_string, ensure_string, ensure_string),
        "EXPAND_ENV_VARS": (is_bool, to_bool, bool_to_str),
        "FORCE_POSIX_PATHS": (is_bool, to_bool, bool_to_str),
        "FOREIGN_ALIASES_SUPPRESS_SKIP_MESSAGE": (is_bool, to_bool, bool_to_str),
        "FOREIGN_ALIASES_OVERRIDE": (is_bool, to_bool, bool_to_str),
        "FUZZY_PATH_COMPLETION": (is_bool, to_bool, bool_to_str),
        "GLOB_SORTED": (is_bool, to_bool, bool_to_str),
        "HISTCONTROL": (is_string_set, csv_to_set, set_to_csv),
        "IGNOREEOF": (is_bool, to_bool, bool_to_str),
        "INTENSIFY_COLORS_ON_WIN": (
            always_false,
            intensify_colors_on_win_setter,
            bool_to_str,
        ),
        "LANG": (is_string, ensure_string, ensure_string),
        "LC_COLLATE": (always_false, locale_convert("LC_COLLATE"), ensure_string),
        "LC_CTYPE": (always_false, locale_convert("LC_CTYPE"), ensure_string),
        "LC_MESSAGES": (always_false, locale_convert("LC_MESSAGES"), ensure_string),
        "LC_MONETARY": (always_false, locale_convert("LC_MONETARY"), ensure_string),
        "LC_NUMERIC": (always_false, locale_convert("LC_NUMERIC"), ensure_string),
        "LC_TIME": (always_false, locale_convert("LC_TIME"), ensure_string),
        "LS_COLORS": (is_lscolors, LsColors.convert, detype),
        "LOADED_RC_FILES": (is_bool_seq, csv_to_bool_seq, bool_seq_to_csv),
        "MOUSE_SUPPORT": (is_bool, to_bool, bool_to_str),
        "MULTILINE_PROMPT": (is_string_or_callable, ensure_string, ensure_string),
        re.compile(r"\w*PATH$"): (is_env_path, str_to_env_path, env_path_to_str),
        "PATHEXT": (
            is_nonstring_seq_of_strings,
            pathsep_to_upper_seq,
            seq_to_upper_pathsep,
        ),
        "PRETTY_PRINT_RESULTS": (is_bool, to_bool, bool_to_str),
        "PROMPT": (is_string_or_callable, ensure_string, ensure_string),
        "PROMPT_FIELDS": (always_true, None, None),
        "PROMPT_TOOLKIT_COLOR_DEPTH": (
            always_false,
            ptk2_color_depth_setter,
            ensure_string,
        ),
        "PUSHD_MINUS": (is_bool, to_bool, bool_to_str),
        "PUSHD_SILENT": (is_bool, to_bool, bool_to_str),
        "PTK_STYLE_OVERRIDES": (is_str_str_dict, to_str_str_dict, dict_to_str),
        "RAISE_SUBPROC_ERROR": (is_bool, to_bool, bool_to_str),
        "RIGHT_PROMPT": (is_string_or_callable, ensure_string, ensure_string),
        "BOTTOM_TOOLBAR": (is_string_or_callable, ensure_string, ensure_string),
        "SUBSEQUENCE_PATH_COMPLETION": (is_bool, to_bool, bool_to_str),
        "SUGGEST_COMMANDS": (is_bool, to_bool, bool_to_str),
        "SUGGEST_MAX_NUM": (is_int, int, str),
        "SUGGEST_THRESHOLD": (is_int, int, str),
        "SUPPRESS_BRANCH_TIMEOUT_MESSAGE": (is_bool, to_bool, bool_to_str),
        "UPDATE_COMPLETIONS_ON_KEYPRESS": (is_bool, to_bool, bool_to_str),
        "UPDATE_OS_ENVIRON": (is_bool, to_bool, bool_to_str),
        "UPDATE_PROMPT_ON_KEYPRESS": (is_bool, to_bool, bool_to_str),
        "VC_BRANCH_TIMEOUT": (is_float, float, str),
        "VC_HG_SHOW_BRANCH": (is_bool, to_bool, bool_to_str),
        "VI_MODE": (is_bool, to_bool, bool_to_str),
        "VIRTUAL_ENV": (is_string, ensure_string, ensure_string),
        "WIN_UNICODE_CONSOLE": (always_false, setup_win_unicode_console, bool_to_str),
        "XONSHRC": (is_env_path, str_to_env_path, env_path_to_str),
        "XONSH_APPEND_NEWLINE": (is_bool, to_bool, bool_to_str),
        "XONSH_AUTOPAIR": (is_bool, to_bool, bool_to_str),
        "XONSH_CACHE_SCRIPTS": (is_bool, to_bool, bool_to_str),
        "XONSH_CACHE_EVERYTHING": (is_bool, to_bool, bool_to_str),
        "XONSH_COLOR_STYLE": (is_string, ensure_string, ensure_string),
        "XONSH_DEBUG": (always_false, to_debug, bool_or_int_to_str),
        "XONSH_ENCODING": (is_string, ensure_string, ensure_string),
        "XONSH_ENCODING_ERRORS": (is_string, ensure_string, ensure_string),
        "XONSH_HISTORY_BACKEND": (is_history_backend, to_itself, ensure_string),
        "XONSH_HISTORY_FILE": (is_string, ensure_string, ensure_string),
        "XONSH_HISTORY_MATCH_ANYWHERE": (is_bool, to_bool, bool_to_str),
        "XONSH_HISTORY_SIZE": (
            is_history_tuple,
            to_history_tuple,
            history_tuple_to_str,
        ),
        "XONSH_LOGIN": (is_bool, to_bool, bool_to_str),
        "XONSH_PROC_FREQUENCY": (is_float, float, str),
        "XONSH_SHOW_TRACEBACK": (is_bool, to_bool, bool_to_str),
        "XONSH_STDERR_PREFIX": (is_string, ensure_string, ensure_string),
        "XONSH_STDERR_POSTFIX": (is_string, ensure_string, ensure_string),
        "XONSH_STORE_STDOUT": (is_bool, to_bool, bool_to_str),
        "XONSH_STORE_STDIN": (is_bool, to_bool, bool_to_str),
        "XONSH_TRACEBACK_LOGFILE": (is_logfile_opt, to_logfile_opt, logfile_opt_to_str),
        "XONSH_DATETIME_FORMAT": (is_string, ensure_string, ensure_string),
    }


#
# Defaults
#
def default_value(f):
    """Decorator for making callable default values."""
    f._xonsh_callable_default = True
    return f


def is_callable_default(x):
    """Checks if a value is a callable default."""
    return callable(x) and getattr(x, "_xonsh_callable_default", False)


DEFAULT_TITLE = "{current_job:{} | }{user}@{hostname}: {cwd} | xonsh"


@default_value
def xonsh_data_dir(env):
    """Ensures and returns the $XONSH_DATA_DIR"""
    xdd = os.path.expanduser(os.path.join(env.get("XDG_DATA_HOME"), "xonsh"))
    os.makedirs(xdd, exist_ok=True)
    return xdd


@default_value
def xonsh_config_dir(env):
    """Ensures and returns the $XONSH_CONFIG_DIR"""
    xcd = os.path.expanduser(os.path.join(env.get("XDG_CONFIG_HOME"), "xonsh"))
    os.makedirs(xcd, exist_ok=True)
    return xcd


def xonshconfig(env):
    """Ensures and returns the $XONSHCONFIG"""
    xcd = env.get("XONSH_CONFIG_DIR")
    xc = os.path.join(xcd, "config.json")
    return xc


@default_value
def default_xonshrc(env):
    """Creates a new instance of the default xonshrc tuple."""
    xcdrc = os.path.join(xonsh_config_dir(env), "rc.xsh")
    if ON_WINDOWS:
        dxrc = (
            os.path.join(os_environ["ALLUSERSPROFILE"], "xonsh", "xonshrc"),
            xcdrc,
            os.path.expanduser("~/.xonshrc"),
        )
    else:
        dxrc = ("/etc/xonshrc", xcdrc, os.path.expanduser("~/.xonshrc"))
    # Check if old config file exists and issue warning
    old_config_filename = xonshconfig(env)
    if os.path.isfile(old_config_filename):
        print(
            "WARNING! old style configuration ("
            + old_config_filename
            + ") is no longer supported. "
            + "Please migrate to xonshrc."
        )
    return dxrc


@default_value
def xonsh_append_newline(env):
    """Appends a newline if we are in interactive mode"""
    return env.get("XONSH_INTERACTIVE", False)


@default_value
def default_lscolors(env):
    """Gets a default instanse of LsColors"""
    inherited_lscolors = os_environ.get("LS_COLORS", None)
    if inherited_lscolors is None:
        lsc = LsColors.fromdircolors()
    else:
        lsc = LsColors.fromstring(inherited_lscolors)
    # have to place this in the env, so it is applied
    env["LS_COLORS"] = lsc
    return lsc


# Default values should generally be immutable, that way if a user wants
# to set them they have to do a copy and write them to the environment.
# try to keep this sorted.
@lazyobject
def DEFAULT_VALUES():
    dv = {
        "AUTO_CD": False,
        "AUTO_PUSHD": False,
        "AUTO_SUGGEST": True,
        "AUTO_SUGGEST_IN_COMPLETIONS": False,
        "BASH_COMPLETIONS": BASH_COMPLETIONS_DEFAULT,
        "CASE_SENSITIVE_COMPLETIONS": ON_LINUX,
        "CDPATH": (),
        "COLOR_INPUT": True,
        "COLOR_RESULTS": False,
        "COMPLETIONS_BRACKETS": True,
        "COMPLETIONS_CONFIRM": False,
        "COMPLETIONS_DISPLAY": "single",
        "COMPLETIONS_MENU_ROWS": 5,
        "COMPLETION_QUERY_LIMIT": 100,
        "DIRSTACK_SIZE": 20,
        "DOTGLOB": False,
        "DYNAMIC_CWD_WIDTH": (float("inf"), "c"),
        "DYNAMIC_CWD_ELISION_CHAR": "",
        "EXPAND_ENV_VARS": True,
        "FORCE_POSIX_PATHS": False,
        "FOREIGN_ALIASES_SUPPRESS_SKIP_MESSAGE": False,
        "FOREIGN_ALIASES_OVERRIDE": False,
        "PROMPT_FIELDS": dict(prompt.PROMPT_FIELDS),
        "FUZZY_PATH_COMPLETION": True,
        "GLOB_SORTED": True,
        "HISTCONTROL": set(),
        "IGNOREEOF": False,
        "INDENT": "    ",
        "INTENSIFY_COLORS_ON_WIN": True,
        "LANG": "C.UTF-8",
        "LC_CTYPE": locale.setlocale(locale.LC_CTYPE),
        "LC_COLLATE": locale.setlocale(locale.LC_COLLATE),
        "LC_TIME": locale.setlocale(locale.LC_TIME),
        "LC_MONETARY": locale.setlocale(locale.LC_MONETARY),
        "LC_NUMERIC": locale.setlocale(locale.LC_NUMERIC),
        "LS_COLORS": default_lscolors,
        "LOADED_RC_FILES": (),
        "MOUSE_SUPPORT": False,
        "MULTILINE_PROMPT": ".",
        "PATH": PATH_DEFAULT,
        "PATHEXT": [".COM", ".EXE", ".BAT", ".CMD"] if ON_WINDOWS else [],
        "PRETTY_PRINT_RESULTS": True,
        "PROMPT": prompt.default_prompt(),
        "PROMPT_TOOLKIT_COLOR_DEPTH": "",
        "PTK_STYLE_OVERRIDES": dict(PTK2_STYLE),
        "PUSHD_MINUS": False,
        "PUSHD_SILENT": False,
        "RAISE_SUBPROC_ERROR": False,
        "RIGHT_PROMPT": "",
        "BOTTOM_TOOLBAR": "",
        "SHELL_TYPE": "best",
        "SUBSEQUENCE_PATH_COMPLETION": True,
        "SUPPRESS_BRANCH_TIMEOUT_MESSAGE": False,
        "SUGGEST_COMMANDS": True,
        "SUGGEST_MAX_NUM": 5,
        "SUGGEST_THRESHOLD": 3,
        "TITLE": DEFAULT_TITLE,
        "UPDATE_COMPLETIONS_ON_KEYPRESS": True,
        "UPDATE_OS_ENVIRON": False,
        "UPDATE_PROMPT_ON_KEYPRESS": False,
        "VC_BRANCH_TIMEOUT": 0.2 if ON_WINDOWS else 0.1,
        "VC_HG_SHOW_BRANCH": True,
        "VI_MODE": False,
        "WIN_UNICODE_CONSOLE": True,
        "XDG_CONFIG_HOME": os.path.expanduser(os.path.join("~", ".config")),
        "XDG_DATA_HOME": os.path.expanduser(os.path.join("~", ".local", "share")),
        "XONSHRC": default_xonshrc,
        "XONSH_APPEND_NEWLINE": xonsh_append_newline,
        "XONSH_AUTOPAIR": False,
        "XONSH_CACHE_SCRIPTS": True,
        "XONSH_CACHE_EVERYTHING": False,
        "XONSH_COLOR_STYLE": "default",
        "XONSH_CONFIG_DIR": xonsh_config_dir,
        "XONSH_DATA_DIR": xonsh_data_dir,
        "XONSH_DEBUG": 0,
        "XONSH_ENCODING": DEFAULT_ENCODING,
        "XONSH_ENCODING_ERRORS": "surrogateescape",
        "XONSH_HISTORY_BACKEND": "json",
        "XONSH_HISTORY_FILE": os.path.expanduser("~/.xonsh_history.json"),
        "XONSH_HISTORY_MATCH_ANYWHERE": False,
        "XONSH_HISTORY_SIZE": (8128, "commands"),
        "XONSH_LOGIN": False,
        "XONSH_PROC_FREQUENCY": 1e-4,
        "XONSH_SHOW_TRACEBACK": False,
        "XONSH_STDERR_PREFIX": "",
        "XONSH_STDERR_POSTFIX": "",
        "XONSH_STORE_STDIN": False,
        "XONSH_STORE_STDOUT": False,
        "XONSH_TRACEBACK_LOGFILE": None,
        "XONSH_DATETIME_FORMAT": "%Y-%m-%d %H:%M",
    }
    if hasattr(locale, "LC_MESSAGES"):
        dv["LC_MESSAGES"] = locale.setlocale(locale.LC_MESSAGES)
    return dv


VarDocs = collections.namedtuple(
    "VarDocs", ["docstr", "configurable", "default", "store_as_str"]
)
VarDocs.__doc__ = """Named tuple for environment variable documentation

Parameters
----------
docstr : str
   The environment variable docstring.
configurable : bool, optional
    Flag for whether the environment variable is configurable or not.
default : str, optional
    Custom docstring for the default value for complex defaults.
    Is this is DefaultNotGiven, then the default will be looked up
    from DEFAULT_VALUES and converted to a str.
store_as_str : bool, optional
    Flag for whether the environment variable should be stored as a
    string. This is used when persisting a variable that is not JSON
    serializable to the config file. For example, sets, frozensets, and
    potentially other non-trivial data types. default, False.
"""
# iterates from back
VarDocs.__new__.__defaults__ = (True, DefaultNotGiven, False)


# Please keep the following in alphabetic order - scopatz
@lazyobject
def DEFAULT_DOCS():
    return {
        "ANSICON": VarDocs(
            "This is used on Windows to set the title, " "if available.",
            configurable=False,
        ),
        "AUTO_CD": VarDocs(
            "Flag to enable changing to a directory by entering the dirname or "
            "full path only (without the cd command)."
        ),
        "AUTO_PUSHD": VarDocs(
            "Flag for automatically pushing directories onto the directory stack."
        ),
        "AUTO_SUGGEST": VarDocs(
            "Enable automatic command suggestions based on history, like in the fish "
            "shell.\n\nPressing the right arrow key inserts the currently "
            "displayed suggestion. Only usable with ``$SHELL_TYPE=prompt_toolkit.``"
        ),
        "AUTO_SUGGEST_IN_COMPLETIONS": VarDocs(
            "Places the auto-suggest result as the first option in the completions. "
            "This enables you to tab complete the auto-suggestion."
        ),
        "BASH_COMPLETIONS": VarDocs(
            "This is a list (or tuple) of strings that specifies where the "
            "``bash_completion`` script may be found. "
            "The first valid path will be used. For better performance, "
            "bash-completion v2.x is recommended since it lazy-loads individual "
            "completion scripts. "
            "For both bash-completion v1.x and v2.x, paths of individual completion "
            "scripts (like ``.../completes/ssh``) do not need to be included here. "
            "The default values are platform "
            "dependent, but sane. To specify an alternate list, do so in the run "
            "control file.",
            default=(
                "Normally this is:\n\n"
                "    ``('/usr/share/bash-completion/bash_completion', )``\n\n"
                "But, on Mac it is:\n\n"
                "    ``('/usr/local/share/bash-completion/bash_completion', "
                "'/usr/local/etc/bash_completion')``\n\n"
                "Other OS-specific defaults may be added in the future."
            ),
        ),
        "CASE_SENSITIVE_COMPLETIONS": VarDocs(
            "Sets whether completions should be case sensitive or case " "insensitive.",
            default="True on Linux, False otherwise.",
        ),
        "CDPATH": VarDocs(
            "A list of paths to be used as roots for a cd, breaking compatibility "
            "with Bash, xonsh always prefer an existing relative path."
        ),
        "COLOR_INPUT": VarDocs("Flag for syntax highlighting interactive input."),
        "COLOR_RESULTS": VarDocs("Flag for syntax highlighting return values."),
        "COMPLETIONS_BRACKETS": VarDocs(
            "Flag to enable/disable inclusion of square brackets and parentheses "
            "in Python attribute completions.",
            default="True",
        ),
        "COMPLETIONS_DISPLAY": VarDocs(
            "Configure if and how Python completions are displayed by the "
            "``prompt_toolkit`` shell.\n\nThis option does not affect Bash "
            "completions, auto-suggestions, etc.\n\nChanging it at runtime will "
            "take immediate effect, so you can quickly disable and enable "
            "completions during shell sessions.\n\n"
            "- If ``$COMPLETIONS_DISPLAY`` is ``none`` or ``false``, do not display\n"
            "  those completions.\n"
            "- If ``$COMPLETIONS_DISPLAY`` is ``single``, display completions in a\n"
            "  single column while typing.\n"
            "- If ``$COMPLETIONS_DISPLAY`` is ``multi`` or ``true``, display completions\n"
            "  in multiple columns while typing.\n\n"
            "- If ``$COMPLETIONS_DISPLAY`` is ``readline``, display completions\n"
            "  will emulate the behavior of readline.\n\n"
            "These option values are not case- or type-sensitive, so e.g."
            "writing ``$COMPLETIONS_DISPLAY = None`` "
            "and ``$COMPLETIONS_DISPLAY = 'none'`` are equivalent. Only usable with "
            "``$SHELL_TYPE=prompt_toolkit``"
        ),
        "COMPLETIONS_CONFIRM": VarDocs(
            "While tab-completions menu is displayed, press <Enter> to confirm "
            "completion instead of running command. This only affects the "
            "prompt-toolkit shell."
        ),
        "COMPLETIONS_MENU_ROWS": VarDocs(
            "Number of rows to reserve for tab-completions menu if "
            "``$COMPLETIONS_DISPLAY`` is ``single`` or ``multi``. This only affects the "
            "prompt-toolkit shell."
        ),
        "COMPLETION_QUERY_LIMIT": VarDocs(
            "The number of completions to display before the user is asked "
            "for confirmation."
        ),
        "DIRSTACK_SIZE": VarDocs("Maximum size of the directory stack."),
        "DOTGLOB": VarDocs(
            'Globbing files with "*" or "**" will also match '
            "dotfiles, or those 'hidden' files whose names "
            "begin with a literal '.'. Such files are filtered "
            "out by default."
        ),
        "DYNAMIC_CWD_WIDTH": VarDocs(
            "Maximum length in number of characters "
            "or as a percentage for the ``cwd`` prompt variable. For example, "
            '"20" is a twenty character width and "10%" is ten percent of the '
            "number of columns available."
        ),
        "DYNAMIC_CWD_ELISION_CHAR": VarDocs(
            "The string used to show a shortened directory in a shortened cwd, "
            "e.g. ``'…'``."
        ),
        "EXPAND_ENV_VARS": VarDocs(
            "Toggles whether environment variables are expanded inside of strings "
            "in subprocess mode."
        ),
        "FORCE_POSIX_PATHS": VarDocs(
            "Forces forward slashes (``/``) on Windows systems when using auto "
            "completion if set to anything truthy.",
            configurable=ON_WINDOWS,
        ),
        "FOREIGN_ALIASES_SUPPRESS_SKIP_MESSAGE": VarDocs(
            "Whether or not foreign aliases should suppress the message "
            "that informs the user when a foreign alias has been skipped "
            "because it already exists in xonsh.",
            configurable=True,
        ),
        "FOREIGN_ALIASES_OVERRIDE": VarDocs(
            "Whether or not foreign aliases should override xonsh aliases "
            "with the same name. Note that setting of this must happen in the "
            "environment that xonsh was started from. "
            "It cannot be set in the ``.xonshrc`` as loading of foreign aliases happens before"
            "``.xonshrc`` is parsed",
            configurable=True,
        ),
        "PROMPT_FIELDS": VarDocs(
            "Dictionary containing variables to be used when formatting $PROMPT "
            "and $TITLE. See 'Customizing the Prompt' "
            "http://xon.sh/tutorial.html#customizing-the-prompt",
            configurable=False,
            default="``xonsh.prompt.PROMPT_FIELDS``",
        ),
        "FUZZY_PATH_COMPLETION": VarDocs(
            "Toggles 'fuzzy' matching of paths for tab completion, which is only "
            "used as a fallback if no other completions succeed but can be used "
            "as a way to adjust for typographical errors. If ``True``, then, e.g.,"
            " ``xonhs`` will match ``xonsh``."
        ),
        "GLOB_SORTED": VarDocs(
            "Toggles whether globbing results are manually sorted. If ``False``, "
            "the results are returned in arbitrary order."
        ),
        "HISTCONTROL": VarDocs(
            "A set of strings (comma-separated list in string form) of options "
            "that determine what commands are saved to the history list. By "
            "default all commands are saved. The option ``ignoredups`` will not "
            "save the command if it matches the previous command. The option "
            "'ignoreerr' will cause any commands that fail (i.e. return non-zero "
            "exit status) to not be added to the history list.",
            store_as_str=True,
        ),
        "IGNOREEOF": VarDocs("Prevents Ctrl-D from exiting the shell."),
        "INDENT": VarDocs("Indentation string for multiline input"),
        "INTENSIFY_COLORS_ON_WIN": VarDocs(
            "Enhance style colors for readability "
            "when using the default terminal (``cmd.exe``) on Windows. Blue colors, "
            "which are hard to read, are replaced with cyan. Other colors are "
            "generally replaced by their bright counter parts.",
            configurable=ON_WINDOWS,
        ),
        "LANG": VarDocs("Fallback locale setting for systems where it matters"),
        "LS_COLORS": VarDocs("Color settings for ``ls`` command line utility"),
        "LOADED_RC_FILES": VarDocs(
            "Whether or not any of the xonsh run control files were loaded at "
            "startup. This is a sequence of bools in Python that is converted "
            "to a CSV list in string form, ie ``[True, False]`` becomes "
            "``'True,False'``.",
            configurable=False,
        ),
        "MOUSE_SUPPORT": VarDocs(
            "Enable mouse support in the ``prompt_toolkit`` shell. This allows "
            "clicking for positioning the cursor or selecting a completion. In "
            "some terminals however, this disables the ability to scroll back "
            "through the history of the terminal. Only usable with "
            "``$SHELL_TYPE=prompt_toolkit``"
        ),
        "MULTILINE_PROMPT": VarDocs(
            "Prompt text for 2nd+ lines of input, may be str or function which "
            "returns a str."
        ),
        "OLDPWD": VarDocs(
            "Used to represent a previous present working directory.",
            configurable=False,
        ),
        "PATH": VarDocs("List of strings representing where to look for executables."),
        "PATHEXT": VarDocs(
            "Sequence of extension strings (eg, ``.EXE``) for "
            "filtering valid executables by. Each element must be "
            "uppercase."
        ),
        "PRETTY_PRINT_RESULTS": VarDocs('Flag for "pretty printing" return values.'),
        "PROMPT": VarDocs(
            "The prompt text. May contain keyword arguments which are "
            "auto-formatted, see 'Customizing the Prompt' at "
            "http://xon.sh/tutorial.html#customizing-the-prompt. "
            "This value is never inherited from parent processes.",
            default="``xonsh.environ.DEFAULT_PROMPT``",
        ),
        "PROMPT_TOOLKIT_COLOR_DEPTH": VarDocs(
            "The color depth used by prompt toolkit 2. Possible values are: "
            "``DEPTH_1_BIT``, ``DEPTH_4_BIT``, ``DEPTH_8_BIT``, ``DEPTH_24_BIT`` "
            "colors. Default is an empty string which means that prompt toolkit decide."
        ),
        "PTK_STYLE_OVERRIDES": VarDocs(
            "A dictionary containing custom prompt_toolkit style definitions."
        ),
        "PUSHD_MINUS": VarDocs(
            "Flag for directory pushing functionality. False is the normal " "behavior."
        ),
        "PUSHD_SILENT": VarDocs(
            "Whether or not to suppress directory stack manipulation output."
        ),
        "RAISE_SUBPROC_ERROR": VarDocs(
            "Whether or not to raise an error if a subprocess (captured or "
            "uncaptured) returns a non-zero exit status, which indicates failure. "
            "This is most useful in xonsh scripts or modules where failures "
            "should cause an end to execution. This is less useful at a terminal. "
            "The error that is raised is a ``subprocess.CalledProcessError``."
        ),
        "RIGHT_PROMPT": VarDocs(
            "Template string for right-aligned text "
            "at the prompt. This may be parametrized in the same way as "
            "the ``$PROMPT`` variable. Currently, this is only available in the "
            "prompt-toolkit shell."
        ),
        "BOTTOM_TOOLBAR": VarDocs(
            "Template string for the bottom toolbar. "
            "This may be parametrized in the same way as "
            "the ``$PROMPT`` variable. Currently, this is only available in the "
            "prompt-toolkit shell."
        ),
        "SHELL_TYPE": VarDocs(
            "Which shell is used. Currently two base shell types are supported:\n\n"
            "    - ``readline`` that is backed by Python's readline module\n"
            "    - ``prompt_toolkit`` that uses external library of the same name\n"
            "    - ``random`` selects a random sh