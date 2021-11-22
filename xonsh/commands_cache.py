# -*- coding: utf-8 -*-
"""Module for caching command & alias names as well as for predicting whether
a command will be able to be run in the background.

A background predictor is a function that accepts a single argument list
and returns whether or not the process can be run in the background (returns
True) or must be run the foreground (returns False).
"""
import os
import time
import builtins
import argparse
import collections.abc as cabc

from xonsh.platform import ON_WINDOWS, ON_POSIX, pathbasename
from xonsh.tools import executables_in
from xonsh.lazyasd import lazyobject


class CommandsCache(cabc.Mapping):
    """A lazy cache representing the commands available on the file system.
    The keys are the command names and the values a tuple of (loc, has_alias)
    where loc is either a str pointing to the executable on the file system or
    None (if no executable exists) and has_alias is a boolean flag for whether
    the command has an alias.
    """

    def __init__(self):
        self._cmds_cache = {}
        self._path_checksum = None
        self._alias_checksum = None
        self._path_mtime = -1
        self.threadable_predictors = default_threadable_predictors()

    def __contains__(self, key):
        _ = self.all_commands
        return self.lazyin(key)

    def __iter__(self):
        for cmd, (path, is_alias) in self.all_commands.items():
            if ON_WINDOWS and path is not None:
                # All command keys are stored in uppercase on Windows.
                # This ensures the original command name is returned.
                cmd = pathbasename(path)
            yield cmd

    def __len__(self):
        return len(self.all_commands)

    def __getitem__(self, key):
        _ = self.all_commands
        return self.lazyget(key)

    def is_empty(self):
        """Returns whether the cache is populated or not."""
        return len(self._cmds_cache) == 0

    @staticmethod
    def get_possible_names(name):
        """Generates the possible `PATHEXT` extension variants of a given executable
         name on Windows as a list, conserving the ordering in `PATHEXT`.
         Returns a list as `name` being the only item in it on other platforms."""
        if ON_WINDOWS:
            pathext = builtins.__xonsh__.env.get("PATHEXT", [])
            name = name.upper()
            return [name + ext for ext in ([""] + pathext)]
        else:
            return [name]

    @staticmethod
    def remove_dups(p):
        ret = list()
        for e in p:
            if e not in ret:
                ret.append(e)
        return ret

    @property
    def all_commands(self):
        paths = builtins.__xonsh__.env.get("PATH", [])
        paths = CommandsCache.remove_dups(paths)
        path_immut = tuple(x for x in paths if os.path.isdir(x))
        # did PATH change?
        path_hash = hash(path_immut)
        cache_valid = path_hash == self._path_checksum
        self._pat