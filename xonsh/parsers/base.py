
# -*- coding: utf-8 -*-
"""Implements the base xonsh parser."""
import os
import re
import time
import textwrap
from threading import Thread
from ast import parse as pyparse
from collections.abc import Iterable, Sequence, Mapping

from xonsh.ply.ply import yacc

from xonsh.tools import FORMATTER
from xonsh import ast
from xonsh.ast import has_elts, xonsh_call, load_attribute_chain
from xonsh.lexer import Lexer, LexToken
from xonsh.platform import PYTHON_VERSION_INFO
from xonsh.tokenize import SearchPath, StringPrefix
from xonsh.lazyasd import LazyObject, lazyobject
from xonsh.parsers.context_check import check_contexts


RE_SEARCHPATH = LazyObject(lambda: re.compile(SearchPath), globals(), "RE_SEARCHPATH")
RE_STRINGPREFIX = LazyObject(
    lambda: re.compile(StringPrefix), globals(), "RE_STRINGPREFIX"
)


@lazyobject
def RE_FSTR_EVAL_CHARS():
    return re.compile(".*?[!@$`]")


class Location(object):
    """Location in a file."""

    def __init__(self, fname, lineno, column=None):
        """Takes a filename, line number, and optionally a column number."""
        self.fname = fname
        self.lineno = lineno
        self.column = column

    def __str__(self):
        s = "{0}:{1}".format(self.fname, self.lineno)
        if self.column is not None:
            s += ":{0}".format(self.column)
        return s


def ensure_has_elts(x, lineno=None, col_offset=None):
    """Ensures that x is an AST node with elements."""
    if not has_elts(x):
        if not isinstance(x, Iterable):
            x = [x]
        lineno = x[0].lineno if lineno is None else lineno
        col_offset = x[0].col_offset if col_offset is None else col_offset
        x = ast.Tuple(elts=x, ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
    return x


def empty_list(lineno=None, col=None):
    """Creates the AST node for an empty list."""
    return ast.List(elts=[], ctx=ast.Load(), lineno=lineno, col_offset=col)


def binop(x, op, y, lineno=None, col=None):
    """Creates the AST node for a binary operation."""
    lineno = x.lineno if lineno is None else lineno
    col = x.col_offset if col is None else col
    return ast.BinOp(left=x, op=op, right=y, lineno=lineno, col_offset=col)


def call_split_lines(x, lineno=None, col=None):
    """Creates the AST node for calling the 'splitlines' attribute of an
    object, nominally a string.
    """
    return ast.Call(
        func=ast.Attribute(
            value=x, attr="splitlines", ctx=ast.Load(), lineno=lineno, col_offset=col
        ),
        args=[],
        keywords=[],
        starargs=None,
        kwargs=None,
        lineno=lineno,
        col_offset=col,
    )


def ensure_list_from_str_or_list(x, lineno=None, col=None):
    """Creates the AST node for the following expression::

        [x] if isinstance(x, str) else x

    Somewhat useful.
    """
    return ast.IfExp(
        test=ast.Call(
            func=ast.Name(
                id="isinstance", ctx=ast.Load(), lineno=lineno, col_offset=col
            ),
            args=[x, ast.Name(id="str", ctx=ast.Load(), lineno=lineno, col_offset=col)],
            keywords=[],
            starargs=None,
            kwargs=None,
            lineno=lineno,
            col_offset=col,
        ),
        body=ast.List(elts=[x], ctx=ast.Load(), lineno=lineno, col_offset=col),
        orelse=x,
        lineno=lineno,
        col_offset=col,
    )


def xonsh_help(x, lineno=None, col=None):
    """Creates the AST node for calling the __xonsh__.help() function."""
    return xonsh_call("__xonsh__.help", [x], lineno=lineno, col=col)


def xonsh_superhelp(x, lineno=None, col=None):
    """Creates the AST node for calling the __xonsh__.superhelp() function."""
    return xonsh_call("__xonsh__.superhelp", [x], lineno=lineno, col=col)


def xonsh_pathsearch(pattern, pymode=False, lineno=None, col=None):
    """Creates the AST node for calling the __xonsh__.pathsearch() function.
    The pymode argument indicate if it is called from subproc or python mode"""
    pymode = ast.NameConstant(value=pymode, lineno=lineno, col_offset=col)
    searchfunc, pattern = RE_SEARCHPATH.match(pattern).groups()
    pattern = ast.Str(s=pattern, lineno=lineno, col_offset=col)
    pathobj = False
    if searchfunc.startswith("@"):
        func = searchfunc[1:]
    elif "g" in searchfunc:
        func = "__xonsh__.globsearch"
        pathobj = "p" in searchfunc
    else:
        func = "__xonsh__.regexsearch"
        pathobj = "p" in searchfunc
    func = load_attribute_chain(func, lineno=lineno, col=col)
    pathobj = ast.NameConstant(value=pathobj, lineno=lineno, col_offset=col)
    return xonsh_call(
        "__xonsh__.pathsearch",
        args=[func, pattern, pymode, pathobj],
        lineno=lineno,
        col=col,
    )


def load_ctx(x):
    """Recursively sets ctx to ast.Load()"""
    if not hasattr(x, "ctx"):
        return
    x.ctx = ast.Load()
    if isinstance(x, (ast.Tuple, ast.List)):
        for e in x.elts:
            load_ctx(e)
    elif isinstance(x, ast.Starred):
        load_ctx(x.value)


def store_ctx(x):
    """Recursively sets ctx to ast.Store()"""
    if not hasattr(x, "ctx"):
        return
    x.ctx = ast.Store()
    if isinstance(x, (ast.Tuple, ast.List)):
        for e in x.elts:
            store_ctx(e)
    elif isinstance(x, ast.Starred):
        store_ctx(x.value)


def del_ctx(x):
    """Recursively sets ctx to ast.Del()"""
    if not hasattr(x, "ctx"):
        return
    x.ctx = ast.Del()
    if isinstance(x, (ast.Tuple, ast.List)):
        for e in x.elts:
            del_ctx(e)
    elif isinstance(x, ast.Starred):
        del_ctx(x.value)


def empty_list_if_newline(x):
    return [] if x == "\n" else x


def lopen_loc(x):
    """Extracts the line and column number for a node that may have an opening
    parenthesis, brace, or bracket.
    """
    lineno = x._lopen_lineno if hasattr(x, "_lopen_lineno") else x.lineno
    col = x._lopen_col if hasattr(x, "_lopen_col") else x.col_offset
    return lineno, col


def hasglobstar(x):
    """Returns True if a node has literal '*' for globbing."""
    if isinstance(x, ast.Str):
        return "*" in x.s
    elif isinstance(x, list):
        for e in x:
            if hasglobstar(e):
                return True
        else:
            return False
    else:
        return False


def _wrap_fstr_field(field, spec, conv):
    rtn = "{" + field
    if conv:
        rtn += "!" + conv
    if spec:
        rtn += ":" + spec
    rtn += "}"
    return rtn


def eval_fstr_fields(fstring, prefix, filename=None):
    """Takes an fstring (and its prefix, ie f") that may contain
    xonsh expressions as its field values and
    substitues them for a xonsh eval() call as needed. Roughly,
    for example, this will take f"{$HOME}" and transform it to
    be f"{__xonsh__.execer.eval(r'$HOME')}".
    """
    last = fstring[-1]
    q, r = ("'", r"\'") if last == '"' else ('"', r"\"")
    prelen = len(prefix)
    postlen = len(fstring) - len(fstring.rstrip(last))
    template = fstring[prelen:-postlen]
    repl = prefix
    for literal, field, spec, conv in FORMATTER.parse(template):
        repl += literal
        if field is None:
            continue
        elif RE_FSTR_EVAL_CHARS.match(field) is None:
            # just a normal python field, simply reconstruct.
            repl += _wrap_fstr_field(field, spec, conv)
        else:
            # the field has a special xonsh character, so we must eval it
            eval_field = "__xonsh__.execer.eval(r" + q
            eval_field += field.lstrip().replace(q, r)
            eval_field += q + ", glbs=globals(), locs=locals()"
            if filename is not None:
                eval_field += ", filename=" + q + filename + q
            eval_field += ")"
            repl += _wrap_fstr_field(eval_field, spec, conv)
    repl += last * postlen
    return repl


class YaccLoader(Thread):
    """Thread to load (but not shave) the yacc parser."""

    def __init__(self, parser, yacc_kwargs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.parser = parser
        self.yacc_kwargs = yacc_kwargs
        self.start()

    def run(self):
        self.parser.parser = yacc.yacc(**self.yacc_kwargs)


class BaseParser(object):
    """A base class that parses the xonsh language."""

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
            The directory to place generated tables within. Defaults to the root
            xonsh dir.
        """
        self.lexer = lexer = Lexer()
        self.tokens = lexer.tokens

        self._lines = None
        self.xonsh_code = None
        self._attach_nocomma_tok_rules()
        self._attach_nocloser_base_rules()
        self._attach_nodedent_base_rules()
        self._attach_nonewline_base_rules()
        self._attach_subproc_arg_part_rules()

        opt_rules = [
            "newlines",
            "arglist",
            "func_call",
            "rarrow_test",
            "typedargslist",
            "equals_test",
            "colon_test",
            "tfpdef",
            "comma_tfpdef_list",
            "comma_pow_tfpdef",
            "vfpdef",
            "comma_vfpdef_list",
            "comma_pow_vfpdef",
            "equals_yield_expr_or_testlist_list",
            "testlist",
            "as_name",
            "period_or_ellipsis_list",
            "comma_import_as_name_list",
            "comma_dotted_as_name_list",
            "comma_name_list",
            "comma_test",
            "elif_part_list",
            "finally_part",
            "varargslist",
            "or_and_test_list",
            "and_not_test_list",
            "comp_op_expr_list",
            "xor_and_expr_list",
            "ampersand_shift_expr_list",
            "shift_arith_expr_list",
            "op_factor_list",
            "trailer_list",
            "testlist_comp",
            "yield_expr_or_testlist_comp",
            "dictorsetmaker",
            "comma_subscript_list",
            "test",
            "sliceop",
            "comp_iter",
            "yield_arg",
            "test_comma_list",
            "macroarglist",
            "any_raw_toks",
        ]
        for rule in opt_rules:
            self._opt_rule(rule)

        list_rules = [
            "comma_tfpdef",
            "comma_vfpdef",
            "semi_small_stmt",
            "comma_test_or_star_expr",
            "period_or_ellipsis",
            "comma_import_as_name",
            "comma_dotted_as_name",
            "period_name",
            "comma_name",
            "elif_part",
            "except_part",
            "comma_with_item",
            "or_and_test",
            "and_not_test",
            "comp_op_expr",
            "pipe_xor_expr",
            "xor_and_expr",
            "ampersand_shift_expr",
            "shift_arith_expr",
            "pm_term",
            "op_factor",
            "trailer",
            "comma_subscript",
            "comma_expr_or_star_expr",
            "comma_test",
            "comma_argument",
            "comma_item",
            "attr_period_name",
            "test_comma",
            "equals_yield_expr_or_testlist",
            "comma_nocomma",
        ]
        for rule in list_rules:
            self._list_rule(rule)

        tok_rules = [
            "def",
            "class",
            "return",
            "number",
            "name",
            "bang",
            "none",
            "true",
            "false",
            "ellipsis",
            "if",
            "del",
            "assert",
            "lparen",
            "lbrace",
            "lbracket",
            "string",
            "times",
            "plus",
            "minus",
            "divide",
            "doublediv",
            "mod",
            "at",
            "lshift",
            "rshift",
            "pipe",
            "xor",
            "ampersand",
            "for",
            "colon",
            "import",
            "except",
            "nonlocal",
            "global",
            "yield",
            "from",
            "raise",
            "with",
            "dollar_lparen",
            "dollar_lbrace",
            "dollar_lbracket",
            "try",
            "bang_lparen",
            "bang_lbracket",
            "comma",
            "rparen",
            "rbracket",
            "at_lparen",
            "atdollar_lparen",
            "indent",
            "dedent",
            "newline",
            "lambda",
            "ampersandequal",
            "as",
            "atdollar",
            "atequal",
            "break",
            "continue",
            "divequal",
            "dollar_name",
            "double_question",
            "doubledivequal",
            "elif",
            "else",
            "eq",
            "equals",
            "errortoken",
            "finally",
            "ge",
            "in",
            "is",
            "le",
            "lshiftequal",
            "minusequal",
            "modequal",
            "ne",
            "pass",
            "period",
            "pipeequal",
            "plusequal",
            "pow",
            "powequal",
            "question",
            "rarrow",
            "rshiftequal",
            "semi",
            "tilde",
            "timesequal",
            "while",
            "xorequal",
        ]
        for rule in tok_rules:
            self._tok_rule(rule)

        yacc_kwargs = dict(
            module=self,
            debug=yacc_debug,
            start="start_symbols",
            optimize=yacc_optimize,
            tabmodule=yacc_table,
        )
        if not yacc_debug:
            yacc_kwargs["errorlog"] = yacc.NullLogger()
        if outputdir is None:
            outputdir = os.path.dirname(os.path.dirname(__file__))
        yacc_kwargs["outputdir"] = outputdir
        if yacc_debug:
            # create parser on main thread
            self.parser = yacc.yacc(**yacc_kwargs)
        else:
            self.parser = None
            YaccLoader(self, yacc_kwargs)

        # Keeps track of the last token given to yacc (the lookahead token)
        self._last_yielded_token = None

    def reset(self):
        """Resets for clean parsing."""
        self.lexer.reset()
        self._last_yielded_token = None
        self._lines = None
        self.xonsh_code = None

    def parse(self, s, filename="<code>", mode="exec", debug_level=0):
        """Returns an abstract syntax tree of xonsh code.

        Parameters
        ----------
        s : str
            The xonsh code.
        filename : str, optional
            Name of the file.
        mode : str, optional
            Execution mode, one of: exec, eval, or single.
        debug_level : str, optional
            Debugging level passed down to yacc.

        Returns
        -------
        tree : AST
        """
        self.reset()
        self.xonsh_code = s
        self.lexer.fname = filename
        while self.parser is None:
            time.sleep(0.01)  # block until the parser is ready
        tree = self.parser.parse(input=s, lexer=self.lexer, debug=debug_level)
        if tree is not None:
            check_contexts(tree)
        # hack for getting modes right
        if mode == "single":
            if isinstance(tree, ast.Expression):
                tree = ast.Interactive(body=[self.expr(tree.body)])
            elif isinstance(tree, ast.Module):
                tree = ast.Interactive(body=tree.body)
        return tree

    def _lexer_errfunc(self, msg, line, column):
        self._parse_error(msg, self.currloc(line, column))

    def _yacc_lookahead_token(self):
        """Gets the next-to-last and last token seen by the lexer."""
        return self.lexer.beforelast, self.lexer.last

    def _opt_rule(self, rulename):
        """For a rule name, creates an associated optional rule.
        '_opt' is appended to the rule name.
        """

        def optfunc(self, p):
            p[0] = p[1]

        optfunc.__doc__ = ("{0}_opt : empty\n" "        | {0}").format(rulename)
        optfunc.__name__ = "p_" + rulename + "_opt"
        setattr(self.__class__, optfunc.__name__, optfunc)

    def _list_rule(self, rulename):
        """For a rule name, creates an associated list rule.
        '_list' is appended to the rule name.
        """

        def listfunc(self, p):
            p[0] = p[1] if len(p) == 2 else p[1] + p[2]

        listfunc.__doc__ = ("{0}_list : {0}\n" "         | {0}_list {0}").format(
            rulename
        )