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
    """Asks a question and then chooses the next node based on the response.
    """

    attrs = ("question", "responses", "converter", "path")

    def __init__(self, question, responses, converter=None, path=None):
        """
        Parameters
        ----------
        question : str
            The question itself.
        responses : dict with str keys and Node values
            Mapping from user-input responses to nodes.
        converter : callable, optional
            Converts the string the user typed into another object
            that serves as a key to the responses dict.
        path : str or sequence of str, optional
            A path within the storage object.
        """
        self.question = question
        self.responses = responses
        self.converter = converter
        self.path = path


class Input(Node):
    """Gets input from the user."""

    attrs = ("prompt", "converter", "show_conversion", "confirm", "path")

    def __init__(
        self,
        prompt=">>> ",
        converter=None,
        show_conversion=False,
        confirm=False,
        retry=False,
        path=None,
    ):
        """
        Parameters
        ----------
        prompt : str, optional
            Prompt string prior to input
        converter : callable, optional
            Converts the string the user typed into another object
            prior to storage.
        show_conversion : bool, optional
            Flag for whether or not to show the results of the conversion
            function if the conversion function was meaningfully executed.
            Default False.
        confirm : bool, optional
            Whether the input should be confirmed until true or broken,
            default False.
        retry : bool, optional
            In the event that the conversion operation fails, should
            users be re-prompted until they provide valid input. Default False.
        path : str or sequence of str, optional
            A path within the storage object.
        """
        self.prompt = prompt
        self.converter = converter
        self.show_conversion = show_conversion
        self.confirm = confirm
        self.retry = retry
        self.path = path


class While(Node):
    """Computes a body while a condition function evaluates to true.

    The condition function has the form ``cond(visitor=None, node=None)`` and
    must return an object that responds to the Python magic method ``__bool__``.
    The beg attribute specifies the number to start the loop iteration at.
    """

    attrs = ("cond", "body", "idxname", "beg", "path")

    def __init__(self, cond, body, idxname="idx", beg=0, path=None):
        """
        Parameters
        ----------
        cond : callable
            Function that determines if the next loop iteration should
            be executed.
        body : sequence of nodes
            A list of node to execute on each iteration. The condition function
            has the form ``cond(visitor=None, node=None)`` and must return an
            object that responds to the Python magic method ``__bool__``.
        idxname : str, optional
            The variable name for the index.
        beg : int, optional
            The first index value when evaluating path format strings.
        path : str or sequence of str, optional
            A path within the storage object.
        """
        self.cond = cond
        self.body = body
        self.idxname = idxname
        self.beg = beg
        self.path = path


#
# Helper nodes
#


class YesNo(Question):
    """Represents a simple yes/no question."""

    def __init__(self, question, yes, no, path=None):
        """
        Parameters
        ----------
        question : str
            The question itself.
        yes : Node
            Node to execute if the response is True.
        no : Node
            Node to execute if the response is False.
        path : str or sequence of str, optional
            A path within the storage object.
        """
        responses = {True: yes, False: no}
        super().__init__(question, responses, converter=to_bool, path=path)


class TrueFalse(Input):
    """Input node the returns a True or False value."""

    def __init__(self, prompt="yes or no [default: no]? ", path=None):
        super().__init__(
            prompt=prompt,
            converter=to_bool,
            show_conversion=False,
            confirm=False,
            path=path,
        )


class TrueFalseBreak(Input):
    """Input node the returns a True, False, or 'break' value."""

    def __init_