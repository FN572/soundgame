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
       