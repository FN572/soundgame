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
        "IGNORE