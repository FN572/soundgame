"""Tools for creating command-line and web-based wizards from a tree of nodes.
"""
import os
import re
import ast
import json
import pprint
import fnmatch
import builtins
import textwrap
import collections.abc as cabc

from xonsh.tools import to_bool, to_bool_or_break, backup_file, print_color
from xonsh.jsonutils import serialize_xonsh_json


#
# Nodes themselves
#
class Node(object):
    """Base type of all nodes."""

    attrs = ()

    def __str__(self):
        return PrettyFormatter(self).visit()

    def __repr__(self):
        return str(self).replace("\n", "")


class Wizard(Node):
    """Top-level node in the tree."""

    attrs = ("children", "path")

    def __init__(self, children, path=None):
        self.children = children
        self.path = path


class Pass(Node):
    """Simple do-nothing node"""


class Message(Node):
    """Contains a simple message to report to the user."""

    attrs = "message"

    def __init__(self, message):
        self.message = message


class Question(Node):
    """Asks a question and then chooses the next node based on th