import builtins
import collections

import xonsh.lazyasd as xl

from xonsh.completers.tools import justify


VALID_ACTIONS = xl.LazyObject(
    lambda: frozenset({"add", "remove", "list"}), globals(), "VALID_ACTIONS"
)


def _add_one_completer(name, func, loc="end"):
    new = collections.OrderedDict()
    if loc == "start":
        new[name] = func
        for (k, v) in builtins.__xonsh__.completers.items():
            new[k] = v
    elif loc == "end":
        for (k, v) in builtins.__xonsh__.completers.items():
            new[k] = v
        new[name] = func
    else:
        direction, rel = loc[0], loc[1:]
        found = False
        for (k, v) in builtins.__xonsh__.completers.items():
            if rel == k and direction == "<":
                new[name] = func
                found = True
            new[k] = v
            if rel == k and direction == ">":
                new[name] = func
                found = True
        if not found:
            new[name] = func
    builtins.__xonsh__.completers.clear()
    builtins.__xonsh__.completers.update(new)


def _list_completers(args, stdin=None, stack=None):
    o = "Registered Completer Functions: \n"
    _comp = builtins.__xonsh__.completers
    ml = max((len(i) for i in _comp), default=0)
    _strs = []
    for c in _comp:
        if _comp[c].__doc__ is None:
            doc = "No description provided"
        else:
            doc = " ".join(_comp[c].__doc__.split())
        doc = justify(doc, 80, ml + 3)
        _strs.append("{: >{}} : {}".format(c, ml, doc))
    return o + "\n".join(_strs) + "\n"


def _remove_completer(args, stdin=None, stack=None):
    err = None
    if len(args) != 1:
        err = "completer remove takes exactly 1 argument."
    else:
        name = args[0]
        if name not in builtins.__xonsh__.completers:
            err = ("The name %s is not a registered " "completer function.") % name
    if err is None:
        del builtins.__xonsh__.completers[name]
        return
    else:
        return None, err + "\n", 1


def _register_completer(args, stdin=None, stack=None):
    err = None