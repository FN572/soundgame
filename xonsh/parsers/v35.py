# -*- coding: utf-8 -*-
"""Implements the xonsh parser for Python v3.5."""
import xonsh.ast as ast
from xonsh.parsers.base import BaseParser


class Parser(BaseParser):
    """A Python v3.5 compliant parser for the xonsh language."""

    def __init__(
        self,
        lexer_optimize=True,
        lexer_table="xonsh.lexer_table",
        yacc_optimize=True,
        yacc_table="xonsh.parser_table",
        yacc_debug=False,
        outputdir=None,
    ):
        """Parameters
        ----------
        lexer_optimize : bool, optional
            Set to false when unstable and true when lexer is stable.
        lexer_table : str, optional
            Lexer module used when optimized.
        yacc_optimize : bool, optional
            Set to false when unstable and true when parser is stable.
        yacc_table : str, optional
            Parser module used when optimized.
        yacc_debug : debug, optional
            Dumps extra debug info.
        outputdir : str or None, optional
            The directory to place generated tables within.
        """
        # Rule creation and modification *must* take place before super()
        tok_rules = ["await", "async"]
        for rule in tok_rules:
            self._tok_rule(rule)
        super().__init__(
            lexer_optimize=lexer_optimize,
            lexer_table=lexer_table,
            yacc_optimize=yacc_optimize,
            yacc_table=yacc_table,
            yacc_debug=yacc_deb