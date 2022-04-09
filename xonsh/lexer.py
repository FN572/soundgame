
# -*- coding: utf-8 -*-
"""Lexer for xonsh code.

Written using a hybrid of ``tokenize`` and PLY.
"""
import io
import re

# 'keyword' interferes with ast.keyword
import keyword as kwmod

from xonsh.ply.ply.lex import LexToken

from xonsh.lazyasd import lazyobject
from xonsh.platform import PYTHON_VERSION_INFO
from xonsh.tokenize import (
    OP,
    IOREDIRECT,
    STRING,
    DOLLARNAME,
    NUMBER,
    SEARCHPATH,
    NEWLINE,
    INDENT,
    DEDENT,
    NL,
    COMMENT,
    ENCODING,
    ENDMARKER,
    NAME,
    ERRORTOKEN,
    GREATER,
    LESS,
    RIGHTSHIFT,
    tokenize,
    TokenError,
)


@lazyobject
def token_map():
    """Mapping from ``tokenize`` tokens (or token types) to PLY token types. If
    a simple one-to-one mapping from ``tokenize`` to PLY exists, the lexer will
    look it up here and generate a single PLY token of the given type.
    Otherwise, it will fall back to handling that token using one of the
    handlers in``special_handlers``.
    """
    tm = {}
    # operators
    _op_map = {
        # punctuation
        ",": "COMMA",
        ".": "PERIOD",
        ";": "SEMI",
        ":": "COLON",
        "...": "ELLIPSIS",
        # basic operators
        "+": "PLUS",
        "-": "MINUS",
        "*": "TIMES",
        "@": "AT",
        "/": "DIVIDE",
        "//": "DOUBLEDIV",
        "%": "MOD",
        "**": "POW",
        "|": "PIPE",
        "~": "TILDE",
        "^": "XOR",
        "<<": "LSHIFT",
        ">>": "RSHIFT",
        "<": "LT",
        "<=": "LE",
        ">": "GT",
        ">=": "GE",
        "==": "EQ",
        "!=": "NE",
        "->": "RARROW",
        # assignment operators
        "=": "EQUALS",
        "+=": "PLUSEQUAL",
        "-=": "MINUSEQUAL",
        "*=": "TIMESEQUAL",
        "@=": "ATEQUAL",
        "/=": "DIVEQUAL",
        "%=": "MODEQUAL",
        "**=": "POWEQUAL",
        "<<=": "LSHIFTEQUAL",
        ">>=": "RSHIFTEQUAL",
        "&=": "AMPERSANDEQUAL",
        "^=": "XOREQUAL",
        "|=": "PIPEEQUAL",
        "//=": "DOUBLEDIVEQUAL",
        # extra xonsh operators
        "?": "QUESTION",
        "??": "DOUBLE_QUESTION",
        "@$": "ATDOLLAR",
        "&": "AMPERSAND",
    }
    for (op, typ) in _op_map.items():