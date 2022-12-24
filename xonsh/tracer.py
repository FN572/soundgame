"""Implements a xonsh tracer."""
import os
import re
import sys
import inspect
import argparse
import linecache
import importlib
import functools

from xonsh.lazyasd import LazyObject
from xonsh.platform import HAS_PYGMENTS
from xonsh.tools import DefaultNotGiven, print_color,