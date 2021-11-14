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
    MatMult = AsyncFunctionDef = AsyncWith = AsyncFor = Await = None

if PYTHON_VERSION_INFO >= (3, 6, 0):
    # pylint: disable=unused-import
    # pylint: disable=no-name-in-module
    from ast import JoinedStr, FormattedValue, AnnAssign
else:
    JoinedStr = FormattedValue = AnnAssign = None

STATEMENTS = (
    FunctionDef,
    ClassDef,
    Return,
    Delete,
    Assign,
    AugAssign,
    For,
    While,
    If,
    With,
    Raise,
    Try,
    Assert,
    Import,
    ImportFrom,
    Global,
    Nonlocal,
    Expr,
    Pass,
    Break,
    Continue,
)
if PYTHON_VERSION_INFO >= (3, 6, 0):
    STATEMENTS += (AnnAssign,)


def leftmostname(node):
    """Attempts to find the first name in the tree."""
    if isinstance(node, Name):
        rtn = node.id
    elif isinstance(node, (BinOp, Compare)):
        rtn = leftmostname(node.left)
    elif isinstance(node, (Attribute, Subscript, Starred, Expr)):
        rtn = leftmostname(node.value)
    elif isinstance(node, Call):
        rtn = leftmostname(node.func)
    elif isinstance(node, UnaryOp):
        rtn = leftmostname(node.operand)
    elif isinstance(node, BoolOp):
        rtn = leftmostname(node.values[0])
    elif isinstance(node, (Assign, AnnAssign)):
        rtn = leftmostname(node.targets[0])
    elif isinstance(node, (Str, Bytes, JoinedStr)):
        # handles case of "./my executable"
        rtn = leftmostname(node.s)
    elif isinstance(node, Tuple) and len(node.elts) > 0:
        # handles case of echo ,1,2,3
        rtn = leftmostname(node.elts[0])
    else:
        rtn = None
    return rtn


def get_lineno(node, default=0):
    """Gets the lineno of a node or returns the default."""
    return getattr(node, "lineno", default)


def min_line(node):
    """Computes the minimum lineno."""
    node_line = get_lineno(node)
    return min(map(get_lineno, walk(node), itertools.repeat(node_line)))


def max_line(node):
    """Computes the maximum lineno."""
    return max(map(get_lineno, walk(node)))


def get_col(node, default=-1):
    """Gets the col_offset of a node, or returns the default"""
    return getattr(node, "col_offset", default)


def min_col(node):
    """Computes the minimum col_offset."""
    return min(map(get_col, walk(node), itertools.repeat(node.col_offset)))


def max_col(node):
    """Returns the maximum col_offset of the node and all sub-nodes."""
    col = getattr(node, "max_col", None)
    if col is not None:
        return col
    highest = max(walk(node), key=get_col)
    col = highest.col_offset + node_len(highest)
    return col


def node_len(node):
    """The length of a node as a string"""
    val = 0
    for n in walk(node):
        if isinstance(n, Name):
            val += len(n.id)
        elif isinstance(n, Attribute):
            val += 1 + (len(n.attr) if isinstance(n.attr, str) else 0)
        # this may need to be added to for more nodes as more cases are found
    return val


def get_id(node, default=None):
    """Gets the id attribute of a node, or returns a default."""
    return getattr(node, "id", default)


def gather_names(node):
    """Returns the set of all names present in the node's tree."""
    rtn = set(map(get_id, walk(node)))
    rtn.discard(None)
    return rtn


def get_id_ctx(node):
    """Gets the id and attribute of a node, or returns a default."""
    nid = getattr(node, "id", None)
    if nid is None:
        return (None, None)
    return (nid, node.ctx)


def gather_load_store_names(node):
    """Returns the names present in the node's tree in a set of load nodes and
    a set of store nodes.
    """
    load = set()
    store = set()
    for nid, ctx in map(get_id_ctx, walk(node)):
        if nid is None:
            continue
        elif isinstance(ctx, Load):
            load.add(nid)
        else:
            store.add(nid)
    return (load, store)


def has_elts(x):
    """Tests if x is an AST node with elements."""
    return isinstance(x, AST) and hasattr(x, "elts")


def load_attribute_chain(name, lineno=None, col=None):
    """Creates an AST that loads variable name that may (or may not)
    have attribute chains. For example, "a.b.c"
    """
    names = name.split(".")
    node = Name(id=names.pop(0), ctx=Load(), lineno=lineno, col_offset=col)
    for attr in names:
        node = Attribute(
            value=node, attr=attr, ctx=Load(), lineno=lineno, col_offset=col
        )
    return node


def xonsh_call(name, args, lineno=None, col=None):
    """Creates the AST node for calling a function of a given name.
    Functions names may contain attribute access, e.g. __xonsh__.env.
    """
    return Call(
        func