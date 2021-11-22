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
from xonsh.tools i