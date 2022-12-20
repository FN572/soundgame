
"""A fast, drop-in replacement for pygments ``get_*()`` and ``guess_*()`` funtions.

The following pygments API functions are currently supplied here::

    from pygments_cache import get_lexer_for_filename, guess_lexer_for_filename
    from pygments_cache import get_formatter_for_filename, get_formatter_by_name
    from pygments_cache import get_style_by_name, get_all_styles
    from pygments_cache import get_filter_by_name

The cache itself is stored at the location given by the ``$PYGMENTS_CACHE_FILE``
environment variable, or by default at ``~/.local/share/pygments-cache/cache.py``.
The cache file is created on first use, if it does not already exist.


"""
import os
import importlib


# Global storage variables
__version__ = "0.1.1"
CACHE = None
DEBUG = False


def _print_duplicate_message(duplicates):
    import sys

    for filename, vals in sorted(duplicates.items()):
        msg = "for {0} ambiquity between:\n  ".format(filename)
        vals = [m + ":" + c for m, c in vals]
        msg += "\n  ".join(sorted(vals))
        print(msg, file=sys.stderr)


def _discover_lexers():
    import inspect
    from pygments.lexers import get_all_lexers, find_lexer_class

    # maps file extension (and names) to (module, classname) tuples
    default_exts = {
        # C / C++
        ".h": ("pygments.lexers.c_cpp", "CLexer"),
        ".hh": ("pygments.lexers.c_cpp", "CppLexer"),
        ".cp": ("pygments.lexers.c_cpp", "CppLexer"),
        # python
        ".py": ("pygments.lexers.python", "Python3Lexer"),
        ".pyw": ("pygments.lexers.python", "Python3Lexer"),
        ".sc": ("pygments.lexers.python", "Python3Lexer"),
        ".tac": ("pygments.lexers.python", "Python3Lexer"),
        "SConstruct": ("pygments.lexers.python", "Python3Lexer"),
        "SConscript": ("pygments.lexers.python", "Python3Lexer"),
        ".sage": ("pygments.lexers.python", "Python3Lexer"),
        ".pytb": ("pygments.lexers.python", "Python3TracebackLexer"),
        # perl
        ".t": ("pygments.lexers.perl", "Perl6Lexer"),