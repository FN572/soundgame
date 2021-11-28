
import os
import re
import ast
import glob
import builtins

import xonsh.tools as xt
import xonsh.platform as xp
import xonsh.lazyasd as xl

from xonsh.completers.tools import get_filter_function


@xl.lazyobject
def PATTERN_NEED_QUOTES():
    pattern = r'\s`\$\{\}\,\*\(\)"\'\?&#'
    if xp.ON_WINDOWS:
        pattern += "%"
    pattern = "[" + pattern + "]" + r"|\band\b|\bor\b"
    return re.compile(pattern)


def cd_in_command(line):
    """Returns True if "cd" is a token in the line, False otherwise."""
    lexer = builtins.__xonsh__.execer.parser.lexer
    lexer.reset()
    lexer.input(line)
    have_cd = False
    for tok in lexer:
        if tok.type == "NAME" and tok.value == "cd":
            have_cd = True
            break
    return have_cd


def _path_from_partial_string(inp, pos=None):
    if pos is None:
        pos = len(inp)
    partial = inp[:pos]
    startix, endix, quote = xt.check_for_partial_string(partial)
    _post = ""
    if startix is None:
        return None
    elif endix is None:
        string = partial[startix:]
    else:
        if endix != pos:
            _test = partial[endix:pos]
            if not any(i == " " for i in _test):
                _post = _test
            else:
                return None
        string = partial[startix:endix]
    end = xt.RE_STRING_START.sub("", quote)
    _string = string
    if not _string.endswith(end):
        _string = _string + end
    try:
        val = ast.literal_eval(_string)
    except (SyntaxError, ValueError):
        return None
    if isinstance(val, bytes):
        env = builtins.__xonsh__.env
        val = val.decode(
            encoding=env.get("XONSH_ENCODING"), errors=env.get("XONSH_ENCODING_ERRORS")
        )
    return string + _post, val + _post, quote, end


def _normpath(p):
    """
    Wraps os.normpath() to avoid removing './' at the beginning
    and '/' at the end. On windows it does the same with backslashes
    """
    initial_dotslash = p.startswith(os.curdir + os.sep)
    initial_dotslash |= xp.ON_WINDOWS and p.startswith(os.curdir + os.altsep)
    p = p.rstrip()
    trailing_slash = p.endswith(os.sep)
    trailing_slash |= xp.ON_WINDOWS and p.endswith(os.altsep)
    p = os.path.normpath(p)
    if initial_dotslash and p != ".":
        p = os.path.join(os.curdir, p)
    if trailing_slash:
        p = os.path.join(p, "")
    if xp.ON_WINDOWS and builtins.__xonsh__.env.get("FORCE_POSIX_PATHS"):
        p = p.replace(os.sep, os.altsep)
    return p


def _startswithlow(x, start, startlow=None):
    if startlow is None:
        startlow = start.lower()
    return x.startswith(start) or x.lower().startswith(startlow)


def _startswithnorm(x, start, startlow=None):
    return x.startswith(start)


def _env(prefix):
    if prefix.startswith("$"):
        key = prefix[1:]
        return {
            "$" + k for k in builtins.__xonsh__.env if get_filter_function()(k, key)
        }
    return ()


def _dots(prefix):
    slash = xt.get_sep()
    if slash == "\\":
        slash = ""
    if prefix in {"", "."}:
        return ("." + slash, ".." + slash)
    elif prefix == "..":
        return (".." + slash,)
    else:
        return ()
