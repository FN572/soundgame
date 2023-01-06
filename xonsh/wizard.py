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

    def __init__(self, prompt="yes, no, or break [default: no]? ", path=None):
        super().__init__(
            prompt=prompt,
            converter=to_bool_or_break,
            show_conversion=False,
            confirm=False,
            path=path,
        )


class StoreNonEmpty(Input):
    """Stores the user input only if the input was not an empty string.
    This works by wrapping the converter function.
    """

    def __init__(
        self,
        prompt=">>> ",
        converter=None,
        show_conversion=False,
        confirm=False,
        retry=False,
        path=None,
        store_raw=False,
    ):
        def nonempty_converter(x):
            """Converts non-empty values and converts empty inputs to
            Unstorable.
            """
            if len(x) == 0:
                x = Unstorable
            elif converter is None:
                pass
            elif store_raw:
                converter(x)  # make sure str is valid, even if storing raw
            else:
                x = converter(x)
            return x

        super().__init__(
            prompt=prompt,
            converter=nonempty_converter,
            show_conversion=show_conversion,
            confirm=confirm,
            path=path,
            retry=retry,
        )


class StateFile(Input):
    """Node for representing the state as a file under a default or user
    given file name. This node type is likely not useful on its own.
    """

    attrs = ("default_file", "check", "ask_filename")

    def __init__(self, default_file=None, check=True, ask_filename=True):
        """
        Parameters
        ----------
        default_file : str, optional
            The default filename to save the file as.
        check : bool, optional
            Whether to print the current state and ask if it should be
            saved/loaded prior to asking for the file name and saving the
            file, default=True.
        ask_filename : bool, optional
            Whether to ask for the filename (if ``False``, always use the
            default filename)
        """
        self._df = None
        super().__init__(prompt="filename: ", converter=None, confirm=False, path=None)
        self.ask_filename = ask_filename
        self.default_file = default_file
        self.check = check

    @property
    def default_file(self):
        return self._df

    @default_file.setter
    def default_file(self, val):
        self._df = val
        if val is None:
            self.prompt = "filename: "
        else:
            self.prompt = "filename [default={0!r}]: ".format(val)


class SaveJSON(StateFile):
    """Node for saving the state as a JSON file under a default or user
    given file name.
    """


class LoadJSON(StateFile):
    """Node for loading the state as a JSON file under a default or user
    given file name.
    """


class FileInserter(StateFile):
    """Node for inserting the state into a file in between a prefix and suffix.
    The state is converted according to some dumper rules.
    """

    attrs = ("prefix", "suffix", "dump_rules", "default_file", "check", "ask_filename")

    def __init__(
        self,
        prefix,
        suffix,
        dump_rules,
        default_file=None,
        check=True,
        ask_filename=True,
    ):
        """
        Parameters
        ----------
        prefix : str
            Starting unique string in file to find and begin the insertion at,
            e.g. '# XONSH WIZARD START\n'
        suffix : str
            Ending unique string to find in the file and end the replacement at,
            e.g. '\n# XONSH WIZARD END'
        dump_rules : dict of strs to functions
            This is a dictionary that maps the path-like match strings to functions
            that take the flat path and the value as arguments and convert the state
            value at a path to a string. The keys here may use wildcards (as seen in
            the standard library fnmatch module). For example::

                dump_rules = {
                    '/path/to/exact': lambda path, x: str(x),
                    '/otherpath/*': lambda path, x: x,
                    '*ending': lambda path x: repr(x),
                    '/': None,
                    }

            If a wildcard is not used in a path, then that rule will be used
            used on an exact match. If wildcards are used, the deepest and longest
            match is used.  If None is given instead of a the function, it means to
            skip generating that key.
        default_file : str, optional
            The default filename to save the file as.
        check : bool, optional
            Wheth