# -*- coding: utf-8 -*-
"""Implements the xonsh parser for Python v3.5."""
import xonsh.ast as ast
from xonsh.parsers.base import BaseParser


class Parser(BaseParser):
    """A Python v3.5 compliant parser for the xonsh language."""

    def __init__(
        self,
        lexer_optimize=True,
        lexer_table="