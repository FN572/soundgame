
# -*- coding: utf-8 -*-
"""Aliases for the xonsh shell."""
import os
import re
import sys
import inspect
import argparse
import builtins
import collections.abc as cabc

from xonsh.lazyasd import lazyobject
from xonsh.dirstack import cd, pushd, popd, dirs, _get_cwd
from xonsh.environ import locate_binary, make_args_env
from xonsh.foreign_shells import foreign_shell_data
from xonsh.jobs import jobs, fg, bg, clean_jobs
from xonsh.platform import (
    ON_ANACONDA,
    ON_DARWIN,
    ON_WINDOWS,
    ON_FREEBSD,
    ON_NETBSD,
    ON_DRAGONFLY,
)
from xonsh.tools import (
    XonshError,
    argvquote,
    escape_windows_cmd_string,
    to_bool,
    swap_values,
    strip_simple_quotes,
    ALIAS_KWARG_NAMES,
    unthreadable,
    print_color,
)
from xonsh.replay import replay_main
from xonsh.timings import timeit_alias
from xonsh.xontribs import xontribs_main
from xonsh.ast import isexpression

import xonsh.completers._aliases as xca
import xonsh.history.main as xhm
import xonsh.xoreutils.which as xxw


@lazyobject
def SUB_EXEC_ALIAS_RE():
    return re.compile(r"@\(|\$\(|!\(|\$\[|!\[")


class Aliases(cabc.MutableMapping):
    """Represents a location to hold and look up aliases."""

    def __init__(self, *args, **kwargs):
        self._raw = {}
        self.update(*args, **kwargs)

    def get(self, key, default=None):
        """Returns the (possibly modified) value. If the key is not present,
        then `default` is returned.
        If the value is callable, it is returned without modification. If it
        is an iterable of strings it will be evaluated recursively to expand
        other aliases, resulting in a new list or a "partially applied"
        callable.
        """
        val = self._raw.get(key)
        if val is None:
            return default
        elif isinstance(val, cabc.Iterable) or callable(val):
            return self.eval_alias(val, seen_tokens={key})
        else:
            msg = "alias of {!r} has an inappropriate type: {!r}"
            raise TypeError(msg.format(key, val))

    def eval_alias(self, value, seen_tokens=frozenset(), acc_args=()):
        """
        "Evaluates" the alias ``value``, by recursively looking up the leftmost
        token and "expanding" if it's also an alias.

        A value like ``["cmd", "arg"]`` might transform like this:
        ``> ["cmd", "arg"] -> ["ls", "-al", "arg"] -> callable()``
        where ``cmd=ls -al`` and ``ls`` is an alias with its value being a
        callable.  The resulting callable will be "partially applied" with
        ``["-al", "arg"]``.
        """
        # Beware of mutability: default values for keyword args are evaluated
        # only once.
        if callable(value):
            return partial_eval_alias(value, acc_args=acc_args)
        else:
            expand_path = builtins.__xonsh__.expand_path
            token, *rest = map(expand_path, value)
            if token in seen_tokens or token not in self._raw:
                # ^ Making sure things like `egrep=egrep --color=auto` works,
                # and that `l` evals to `ls --color=auto -CF` if `l=ls -CF`
                # and `ls=ls --color=auto`
                rtn = [token]
                rtn.extend(rest)
                rtn.extend(acc_args)
                return rtn
            else:
                seen_tokens = seen_tokens | {token}
                acc_args = rest + list(acc_args)
                return self.eval_alias(self._raw[token], seen_tokens, acc_args)

    def expand_alias(self, line):
        """Expands any aliases present in line if alias does not point to a
        builtin function and if alias is only a single command.
        """
        word = line.split(" ", 1)[0]
        if word in builtins.aliases and isinstance(self.get(word), cabc.Sequence):
            word_idx = line.find(word)
            expansion = " ".join(self.get(word))
            line = line[:word_idx] + expansion + line[word_idx + len(word) :]
        return line

    #
    # Mutable mapping interface
    #

    def __getitem__(self, key):
        return self._raw[key]

    def __setitem__(self, key, val):
        if isinstance(val, str):
            f = "<exec-alias:" + key + ">"
            if SUB_EXEC_ALIAS_RE.search(val) is not None:
                # We have a sub-command, e.g. $(cmd), to evaluate
                self._raw[key] = ExecAlias(val, filename=f)
            elif isexpression(val):
                # expansion substitution
                lexer = builtins.__xonsh__.execer.parser.lexer
                self._raw[key] = list(map(strip_simple_quotes, lexer.split(val)))
            else:
                # need to exec alias
                self._raw[key] = ExecAlias(val, filename=f)
        else:
            self._raw[key] = val

    def __delitem__(self, key):
        del self._raw[key]

    def update(self, *args, **kwargs):
        for key, val in dict(*args, **kwargs).items():
            self[key] = val

    def __iter__(self):
        yield from self._raw

    def __len__(self):
        return len(self._raw)

    def __str__(self):
        return str(self._raw)

    def __repr__(self):
        return "{0}.{1}({2})".format(
            self.__class__.__module__, self.__class__.__name__, self._raw
        )

    def _repr_pretty_(self, p, cycle):
        name = "{0}.{1}".format(self.__class__.__module__, self.__class__.__name__)
        with p.group(0, name + "(", ")"):
            if cycle:
                p.text("...")
            elif len(self):
                p.break_()
                p.pretty(dict(self))


class ExecAlias:
    """Provides a callable alias for xonsh source code."""

    def __init__(self, src, filename="<exec-alias>"):
        """
        Parameters
        ----------
        src : str
            Source code that will be
        """
        self.src = src if src.endswith("\n") else src + "\n"
        self.filename = filename

    def __call__(
        self, args, stdin=None, stdout=None, stderr=None, spec=None, stack=None
    ):
        execer = builtins.__xonsh__.execer
        frame = stack[0][0]  # execute as though we are at the call site