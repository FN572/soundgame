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
    if len(args) not in {2, 3}:
        err = (
            "completer add takes either 2 or 3 arguments.\n"
            "For help, run:  completer help add"
        )
    else:
        name = args[0]
        func_name = args[1]
        if name in builtins.__xonsh__.completers:
            err = ("The name %s is already a registered " "completer function.") % name
        else:
            if func_name in builtins.__xonsh__.ctx:
                func = builtins.__xonsh__.ctx[func_name]
                if not callable(func):
                    err = "%s is not callable" % func_name
            else:
                for frame_info in stack:
                    frame = frame_info[0]
                    if func_name in frame.f_locals:
                        func = frame.f_locals[func_name]
                        break
                    elif func_name in frame.f_globals:
                        func = frame.f_globals[func_name]
                        break
                else:
                    err = "No such function: %s" % func_name
    if err is None:
        position = "start" if len(args) == 2 else args[2]
        _add_one_completer(name, func, position)
    e