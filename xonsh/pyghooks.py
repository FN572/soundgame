
# -*- coding: utf-8 -*-
"""Hooks for pygments syntax highlighting."""
import os
import re
import sys
import builtins
from collections import ChainMap
from collections.abc import MutableMapping

from pygments.lexer import inherit, bygroups, include
from pygments.lexers.agile import PythonLexer
from pygments.token import (
    Keyword,
    Name,
    Comment,
    String,
    Error,
    Number,
    Operator,
    Generic,
    Whitespace,
    Token,
    Punctuation,
    Text,
)
from pygments.style import Style
import pygments.util

from xonsh.commands_cache import CommandsCache
from xonsh.lazyasd import LazyObject, LazyDict, lazyobject
from xonsh.tools import (
    ON_WINDOWS,
    intensify_colors_for_cmd_exe,
    ansicolors_to_ptk1_names,
    ANSICOLOR_NAMES_MAP,
    PTK_NEW_OLD_COLOR_MAP,
    hardcode_colors_for_win10,
    FORMATTER,
)

from xonsh.color_tools import (
    RE_BACKGROUND,
    BASE_XONSH_COLORS,
    make_palette,
    find_closest_color,
)
from xonsh.style_tools import norm_name
from xonsh.lazyimps import terminal256
from xonsh.platform import (
    os_environ,
    win_ansi_support,
    ptk_version_info,
    pygments_version_info,
)

from xonsh.pygments_cache import get_style_by_name


def _command_is_valid(cmd):
    try:
        cmd_abspath = os.path.abspath(os.path.expanduser(cmd))
    except (FileNotFoundError, OSError):
        return False
    return cmd in builtins.__xonsh__.commands_cache or (
        os.path.isfile(cmd_abspath) and os.access(cmd_abspath, os.X_OK)
    )


def _command_is_autocd(cmd):
    if not builtins.__xonsh__.env.get("AUTO_CD", False):
        return False
    try:
        cmd_abspath = os.path.abspath(os.path.expanduser(cmd))
    except (FileNotFoundError, OSError):
        return False
    return os.path.isdir(cmd_abspath)


def subproc_cmd_callback(_, match):
    """Yield Builtin token if match contains valid command,
    otherwise fallback to fallback lexer.
    """
    cmd = match.group()
    yield match.start(), Name.Builtin if _command_is_valid(cmd) else Error, cmd


def subproc_arg_callback(_, match):
    """Check if match contains valid path"""
    text = match.group()
    try:
        ispath = os.path.exists(os.path.expanduser(text))
    except (FileNotFoundError, OSError):
        ispath = False
    yield (match.start(), Name.Constant if ispath else Text, text)


COMMAND_TOKEN_RE = r'[^=\s\[\]{}()$"\'`<&|;!]+(?=\s|$|\)|\]|\}|!)'


class XonshLexer(PythonLexer):
    """Xonsh console lexer for pygments."""

    name = "Xonsh lexer"
    aliases = ["xonsh", "xsh"]
    filenames = ["*.xsh", "*xonshrc"]

    def __init__(self, *args, **kwargs):
        # If the lexer is loaded as a pygment plugin, we have to mock
        # __xonsh__.env and __xonsh__.commands_cache
        if not hasattr(builtins, "__xonsh__"):
            from argparse import Namespace

            setattr(builtins, "__xonsh__", Namespace())
        if not hasattr(builtins.__xonsh__, "env"):
            setattr(builtins.__xonsh__, "env", {})
            if ON_WINDOWS:
                pathext = os_environ.get("PATHEXT", [".EXE", ".BAT", ".CMD"])
                builtins.__xonsh__.env["PATHEXT"] = pathext.split(os.pathsep)
        if not hasattr(builtins.__xonsh__, "commands_cache"):
            setattr(builtins.__xonsh__, "commands_cache", CommandsCache())
        _ = builtins.__xonsh__.commands_cache.all_commands  # NOQA
        super().__init__(*args, **kwargs)

    tokens = {
        "mode_switch_brackets": [
            (r"(\$)(\{)", bygroups(Keyword, Punctuation), "py_curly_bracket"),
            (r"(@)(\()", bygroups(Keyword, Punctuation), "py_bracket"),
            (
                r"([\!\$])(\()",
                bygroups(Keyword, Punctuation),
                ("subproc_bracket", "subproc_start"),
            ),
            (
                r"(@\$)(\()",
                bygroups(Keyword, Punctuation),
                ("subproc_bracket", "subproc_start"),
            ),
            (
                r"([\!\$])(\[)",
                bygroups(Keyword, Punctuation),
                ("subproc_square_bracket", "subproc_start"),
            ),
            (r"(g?)(`)", bygroups(String.Affix, String.Backtick), "backtick_re"),
        ],
        "subproc_bracket": [(r"\)", Punctuation, "#pop"), include("subproc")],
        "subproc_square_bracket": [(r"\]", Punctuation, "#pop"), include("subproc")],
        "py_bracket": [(r"\)", Punctuation, "#pop"), include("root")],
        "py_curly_bracket": [(r"\}", Punctuation, "#pop"), include("root")],
        "backtick_re": [
            (r"[\.\^\$\*\+\?\[\]\|]", String.Regex),
            (r"({[0-9]+}|{[0-9]+,[0-9]+})\??", String.Regex),
            (r"\\([0-9]+|[AbBdDsSwWZabfnrtuUvx\\])", String.Escape),
            (r"`", String.Backtick, "#pop"),
            (r"[^`\.\^\$\*\+\?\[\]\|]+", String.Backtick),
        ],
        "root": [
            (r"\?", Keyword),
            (r"(?<=\w)!", Keyword),
            (r"\$\w+", Name.Variable),
            (r"\(", Punctuation, "py_bracket"),
            (r"\{", Punctuation, "py_curly_bracket"),
            include("mode_switch_brackets"),
            inherit,
        ],
        "subproc_start": [
            (r"\s+", Whitespace),
            (COMMAND_TOKEN_RE, subproc_cmd_callback, "#pop"),
            (r"", Whitespace, "#pop"),
        ],
        "subproc": [
            include("mode_switch_brackets"),
            (r"&&|\|\|", Operator, "subproc_start"),
            (r'"(\\\\|\\[0-7]+|\\.|[^"\\])*"', String.Double),
            (r"'(\\\\|\\[0-7]+|\\.|[^'\\])*'", String.Single),
            (r"(?<=\w|\s)!", Keyword, "subproc_macro"),
            (r"^!", Keyword, "subproc_macro"),
            (r";", Punctuation, "subproc_start"),
            (r"&|=", Punctuation),
            (r"\|", Punctuation, "subproc_start"),
            (r"\s+", Text),
            (r'[^=\s\[\]{}()$"\'`<&|;]+', subproc_arg_callback),
            (r"<", Text),
            (r"\$\w+", Name.Variable),
        ],
        "subproc_macro": [
            (r"(\s*)([^\n]+)", bygroups(Whitespace, String)),
            (r"", Whitespace, "#pop"),
        ],
    }

    def get_tokens_unprocessed(self, text):
        """Check first command, then call super.get_tokens_unprocessed
        with root or subproc state"""
        start = 0
        state = ("root",)
        m = re.match(r"(\s*)({})".format(COMMAND_TOKEN_RE), text)
        if m is not None:
            yield m.start(1), Whitespace, m.group(1)
            cmd = m.group(2)
            cmd_is_valid = _command_is_valid(cmd)
            cmd_is_autocd = _command_is_autocd(cmd)

            if cmd_is_valid or cmd_is_autocd:
                yield (m.start(2), Name.Builtin if cmd_is_valid else Name.Constant, cmd)
                start = m.end(2)
                state = ("subproc",)

        for i, t, v in super().get_tokens_unprocessed(text[start:], state):
            yield i + start, t, v


class XonshConsoleLexer(XonshLexer):
    """Xonsh console lexer for pygments."""

    name = "Xonsh console lexer"
    aliases = ["xonshcon"]
    filenames = []

    tokens = {
        "root": [
            (r"^(>>>|\.\.\.) ", Generic.Prompt),
            (r"\n(>>>|\.\.\.)", Generic.Prompt),
            (r"\n(?![>.][>.][>.] )([^\n]*)", Generic.Output),
            (r"\n(?![>.][>.][>.] )(.*?)$", Generic.Output),
            inherit,
        ]
    }


#
# Colors and Styles
#

Color = Token.Color  # alias to new color token namespace


def color_by_name(name, fg=None, bg=None):
    """Converts a color name to a color token, foreground name,
    and background name.  Will take into consideration current foreground
    and background colors, if provided.

    Parameters
    ----------
    name : str
        Color name.
    fg : str, optional
        Foreground color name.
    bg : str, optional
        Background color name.

    Returns
    -------
    tok : Token
        Pygments Token.Color subclass
    fg : str or None
        New computed foreground color name.
    bg : str or None
        New computed background color name.
    """
    name = name.upper()
    if name == "NO_COLOR":
        return Color.NO_COLOR, None, None
    m = RE_BACKGROUND.search(name)
    if m is None:  # must be foreground color
        fg = norm_name(name)
    else:
        bg = norm_name(name)
    # assemble token
    if fg is None and bg is None:
        tokname = "NO_COLOR"
    elif fg is None:
        tokname = bg
    elif bg is None:
        tokname = fg
    else:
        tokname = fg + "__" + bg
    tok = getattr(Color, tokname)
    return tok, fg, bg


def code_by_name(name, styles):
    """Converts a token name into a pygments-style color code.

    Parameters
    ----------
    name : str
        Color token name.
    styles : Mapping
        Mapping for looking up non-hex colors

    Returns
    -------
    code : str
        Pygments style color code.
    """
    fg, _, bg = name.lower().partition("__")
    if fg.startswith("background_"):
        fg, bg = bg, fg
    codes = []
    # foreground color
    if len(fg) == 0:
        pass
    elif "hex" in fg:
        for p in fg.split("_"):
            codes.append("#" + p[3:] if p.startswith("hex") else p)
    else:
        fgtok = getattr(Color, fg.upper())
        if fgtok in styles:
            codes.append(styles[fgtok])
        else:
            codes += fg.split("_")
    # background color
    if len(bg) == 0:
        pass
    elif bg.startswith("background_hex"):
        codes.append("bg:#" + bg[14:])
    else:
        bgtok = getattr(Color, bg.upper())
        if bgtok in styles:
            codes.append(styles[bgtok])
        else:
            codes.append(bg.replace("background_", "bg:"))
    code = " ".join(codes)
    return code


def partial_color_tokenize(template):
    """Tokenizes a template string containing colors. Will return a list
    of tuples mapping the token to the string which has that color.
    These sub-strings maybe templates themselves.
    """
    if builtins.__xonsh__.shell is not None:
        styles = __xonsh__.shell.shell.styler.styles
    else:
        styles = None
    color = Color.NO_COLOR
    try:
        toks, color = _partial_color_tokenize_main(template, styles)
    except Exception:
        toks = [(Color.NO_COLOR, template)]
    if styles is not None:
        styles[color]  # ensure color is available
    return toks