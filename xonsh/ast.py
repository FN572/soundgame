# -*- coding: utf-8 -*-
"""The xonsh abstract syntax tree node."""
# These are imported into our module namespace for the benefit of parser.py.
# pylint: disable=unused-import
import sys
import builtins
from ast import (
    Module,
    Num,
    Expr,
    Str,
    Bytes,
    UnaryOp,
    UAdd,
    USub,
    Invert,
    BinOp,
    Add,
    Sub,
    Mult,
    Div,
    FloorDiv,
    Mod,
    Pow,
    Compare,
    Lt,
    Gt,
    LtE,
    GtE,
    Eq,
    NotEq,
    In,
    NotIn,
    Is,
    IsNot,
    Not,
    BoolOp,
    Or,
    And,
    Subscript,
    Load,
    Slice,
    ExtSlice,
    List,
    Tuple,
    Set,
    Dict,
    AST,
    NameConstant,
    Name,
    GeneratorExp,
    Store,
    comprehension,
    ListComp,
    SetComp,
    DictComp,
    Assign,
    AugAssign,
    BitXor,
    BitAnd,
    BitOr,
    LShift,
    RShift,
    Assert,
    Delete,
    Del,
    Pass,
    Raise,
    Import,
    alias,
    ImportFrom,
    Continue,
    Break,
    Yield,
    YieldFrom,
    Return,
    IfExp,
    Lambda,
    arguments,
    arg,
    Call,
    keyword,
    Attribute,
    Global,
    Nonlocal,
    If,
    While,
    For,
    withitem,
    With,
    Try,
    ExceptHandler,
    FunctionDef,
    ClassDef,
    Starred,
    NodeTransformer,
    Interactive,
    Expression,
    Index,
    literal_eval,
    dump,
    walk,
    increment_lineno,
)
from ast import Ellipsis as EllipsisNode

# pylint: enable=unused-import
import textwrap
import itertools

from xonsh.tools import subproc_toks, find_next_break, get_logical_line
from xonsh.platform import PYTHON_VERSION_INFO

if PYTHON_VERSION_INFO >= (3, 5, 0):
    # pylint: disable=unused-import
    # pylint: disable=no-name-in-module
    from ast import MatMult, AsyncFunctionDef, AsyncWith, AsyncFor, Await
else:
    MatMult = Asy