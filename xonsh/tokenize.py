
"""Tokenization help for xonsh programs.

This file is a modified version of tokenize.py form the Python 3.4 and 3.5
standard libraries (licensed under the Python Software Foundation License,
version 2), which provides tokenization help for Python programs.

It is modified to properly tokenize xonsh code, including backtick regex
path and several xonsh-specific operators.

A few pieces of this file are specific to the version of Python being used.
To find these pieces, search the PY35.

Original file credits:
   __author__ = 'Ka-Ping Yee <ping@lfw.org>'
   __credits__ = ('GvR, ESR, Tim Peters, Thomas Wouters, Fred Drake, '
                  'Skip Montanaro, Raymond Hettinger, Trent Nelson, '
                  'Michael Foord')
"""

import re
import io
import sys
import codecs
import builtins
import itertools
import collections
import token
from token import (
    AMPER,
    AMPEREQUAL,
    AT,
    CIRCUMFLEX,
    CIRCUMFLEXEQUAL,
    COLON,
    COMMA,
    DEDENT,
    DOT,
    DOUBLESLASH,
    DOUBLESLASHEQUAL,
    DOUBLESTAR,
    DOUBLESTAREQUAL,
    ENDMARKER,
    EQEQUAL,
    EQUAL,
    ERRORTOKEN,
    GREATER,
    GREATEREQUAL,
    INDENT,
    LBRACE,
    LEFTSHIFT,
    LEFTSHIFTEQUAL,
    LESS,
    LESSEQUAL,
    LPAR,
    LSQB,
    MINEQUAL,
    MINUS,
    NAME,
    NEWLINE,
    NOTEQUAL,
    NUMBER,
    N_TOKENS,
    OP,
    PERCENT,
    PERCENTEQUAL,
    PLUS,
    PLUSEQUAL,
    RBRACE,
    RIGHTSHIFT,
    RIGHTSHIFTEQUAL,
    RPAR,
    RSQB,
    SEMI,
    SLASH,
    SLASHEQUAL,
    STAR,
    STAREQUAL,
    STRING,
    TILDE,
    VBAR,
    VBAREQUAL,
    tok_name,
)

from xonsh.lazyasd import LazyObject
from xonsh.platform import PYTHON_VERSION_INFO

cookie_re = LazyObject(
    lambda: re.compile(r"^[ \t\f]*#.*coding[:=][ \t]*([-\w.]+)", re.ASCII),
    globals(),
    "cookie_re",
)
blank_re = LazyObject(
    lambda: re.compile(br"^[ \t\f]*(?:[#\r\n]|$)", re.ASCII), globals(), "blank_re"
)

#
# token modifications
#
tok_name = tok_name.copy()
__all__ = token.__all__ + [
    "COMMENT",
    "tokenize",
    "detect_encoding",
    "NL",
    "untokenize",
    "ENCODING",
    "TokenInfo",
    "TokenError",
    "SEARCHPATH",
    "ATDOLLAR",
    "ATEQUAL",
    "DOLLARNAME",
    "IOREDIRECT",
]
HAS_ASYNC = (3, 5, 0) <= PYTHON_VERSION_INFO < (3, 7, 0)
if HAS_ASYNC:
    ASYNC = token.ASYNC
    AWAIT = token.AWAIT
    ADDSPACE_TOKS = (NAME, NUMBER, ASYNC, AWAIT)
else:
    ADDSPACE_TOKS = (NAME, NUMBER)
del token  # must clean up token
PY35 = (3, 5, 0) <= PYTHON_VERSION_INFO
AUGASSIGN_OPS = r"[+\-*/%&@|^=<>]=?"
if not PY35:
    AUGASSIGN_OPS = AUGASSIGN_OPS.replace("@", "")


COMMENT = N_TOKENS
tok_name[COMMENT] = "COMMENT"
NL = N_TOKENS + 1
tok_name[NL] = "NL"
ENCODING = N_TOKENS + 2
tok_name[ENCODING] = "ENCODING"
N_TOKENS += 3
SEARCHPATH = N_TOKENS
tok_name[N_TOKENS] = "SEARCHPATH"
N_TOKENS += 1
IOREDIRECT = N_TOKENS
tok_name[N_TOKENS] = "IOREDIRECT"
N_TOKENS += 1
DOLLARNAME = N_TOKENS
tok_name[N_TOKENS] = "DOLLARNAME"
N_TOKENS += 1
ATDOLLAR = N_TOKENS
tok_name[N_TOKENS] = "ATDOLLAR"
N_TOKENS += 1
ATEQUAL = N_TOKENS
tok_name[N_TOKENS] = "ATEQUAL"
N_TOKENS += 1
_xonsh_tokens = {
    "?": "QUESTION",
    "@=": "ATEQUAL",
    "@$": "ATDOLLAR",
    "||": "DOUBLEPIPE",
    "&&": "DOUBLEAMPER",
    "@(": "ATLPAREN",
    "!(": "BANGLPAREN",
    "![": "BANGLBRACKET",
    "$(": "DOLLARLPAREN",
    "$[": "DOLLARLBRACKET",
    "${": "DOLLARLBRACE",
    "??": "DOUBLEQUESTION",
    "@$(": "ATDOLLARLPAREN",
}

additional_parenlevs = frozenset({"@(", "!(", "![", "$(", "$[", "${", "@$("})

_glbs = globals()
for v in _xonsh_tokens.values():
    _glbs[v] = N_TOKENS
    tok_name[N_TOKENS] = v
    N_TOKENS += 1
    __all__.append(v)
del _glbs, v

EXACT_TOKEN_TYPES = {
    "(": LPAR,
    ")": RPAR,
    "[": LSQB,
    "]": RSQB,
    ":": COLON,
    ",": COMMA,
    ";": SEMI,
    "+": PLUS,
    "-": MINUS,
    "*": STAR,
    "/": SLASH,
    "|": VBAR,
    "&": AMPER,
    "<": LESS,
    ">": GREATER,
    "=": EQUAL,
    ".": DOT,
    "%": PERCENT,
    "{": LBRACE,
    "}": RBRACE,
    "==": EQEQUAL,
    "!=": NOTEQUAL,
    "<=": LESSEQUAL,
    ">=": GREATEREQUAL,
    "~": TILDE,
    "^": CIRCUMFLEX,
    "<<": LEFTSHIFT,
    ">>": RIGHTSHIFT,
    "**": DOUBLESTAR,
    "+=": PLUSEQUAL,
    "-=": MINEQUAL,
    "*=": STAREQUAL,
    "/=": SLASHEQUAL,
    "%=": PERCENTEQUAL,
    "&=": AMPEREQUAL,
    "|=": VBAREQUAL,
    "^=": CIRCUMFLEXEQUAL,
    "<<=": LEFTSHIFTEQUAL,
    ">>=": RIGHTSHIFTEQUAL,
    "**=": DOUBLESTAREQUAL,
    "//": DOUBLESLASH,
    "//=": DOUBLESLASHEQUAL,
    "@": AT,
}

EXACT_TOKEN_TYPES.update(_xonsh_tokens)


class TokenInfo(collections.namedtuple("TokenInfo", "type string start end line")):
    def __repr__(self):
        annotated_type = "%d (%s)" % (self.type, tok_name[self.type])
        return (
            "TokenInfo(type=%s, string=%r, start=%r, end=%r, line=%r)"
            % self._replace(type=annotated_type)
        )

    @property
    def exact_type(self):
        if self.type == OP and self.string in EXACT_TOKEN_TYPES:
            return EXACT_TOKEN_TYPES[self.string]
        else:
            return self.type


def group(*choices):
    return "(" + "|".join(choices) + ")"


def tokany(*choices):
    return group(*choices) + "*"


def maybe(*choices):
    return group(*choices) + "?"


# Note: we use unicode matching for names ("\w") but ascii matching for
# number literals.
Whitespace = r"[ \f\t]*"
Comment = r"#[^\r\n]*"
Ignore = Whitespace + tokany(r"\\\r?\n" + Whitespace) + maybe(Comment)
Name_RE = r"\$?\w+"

Hexnumber = r"0[xX](?:_?[0-9a-fA-F])+"
Binnumber = r"0[bB](?:_?[01])+"
Octnumber = r"0[oO](?:_?[0-7])+"
Decnumber = r"(?:0(?:_?0)*|[1-9](?:_?[0-9])*)"
Intnumber = group(Hexnumber, Binnumber, Octnumber, Decnumber)
Exponent = r"[eE][-+]?[0-9](?:_?[0-9])*"
Pointfloat = group(
    r"[0-9](?:_?[0-9])*\.(?:[0-9](?:_?[0-9])*)?", r"\.[0-9](?:_?[0-9])*"
) + maybe(Exponent)
Expfloat = r"[0-9](?:_?[0-9])*" + Exponent
Floatnumber = group(Pointfloat, Expfloat)
Imagnumber = group(r"[0-9](?:_?[0-9])*[jJ]", Floatnumber + r"[jJ]")
Number = group(Imagnumber, Floatnumber, Intnumber)

StringPrefix = r"(?:[bB][rR]?|[p][fFrR]?|[rR][bBpfF]?|[uU]|[fF][rR]?[p]?)?"

# Tail end of ' string.
Single = r"[^'\\]*(?:\\.[^'\\]*)*'"
# Tail end of " string.
Double = r'[^"\\]*(?:\\.[^"\\]*)*"'
# Tail end of ''' string.
Single3 = r"[^'\\]*(?:(?:\\.|'(?!''))[^'\\]*)*'''"
# Tail end of """ string.
Double3 = r'[^"\\]*(?:(?:\\.|"(?!""))[^"\\]*)*"""'
Triple = group(StringPrefix + "'''", StringPrefix + '"""')
# Single-line ' or " string.
String = group(
    StringPrefix + r"'[^\n'\\]*(?:\\.[^\n'\\]*)*'",
    StringPrefix + r'"[^\n"\\]*(?:\\.[^\n"\\]*)*"',
)

# Xonsh-specific Syntax
SearchPath = r"((?:[rgp]+|@\w*)?)`([^\n`\\]*(?:\\.[^\n`\\]*)*)`"

# Because of leftmost-then-longest match semantics, be sure to put the
# longest operators first (e.g., if = came before ==, == would get
# recognized as two instances of =).
_redir_names = ("out", "all", "err", "e", "2", "a", "&", "1", "o")
_redir_map = (
    # stderr to stdout
    "err>out",
    "err>&1",
    "2>out",
    "err>o",
    "err>1",
    "e>out",
    "e>&1",
    "2>&1",
    "e>o",
    "2>o",
    "e>1",
    "2>1",
    # stdout to stderr
    "out>err",
    "out>&2",
    "1>err",
    "out>e",
    "out>2",
    "o>err",
    "o>&2",
    "1>&2",
    "o>e",
    "1>e",
    "o>2",
    "1>2",
)
IORedirect = group(group(*_redir_map), "{}>>?".format(group(*_redir_names)))
_redir_check = set(_redir_map)
_redir_check = {"{}>".format(i) for i in _redir_names}.union(_redir_check)
_redir_check = {"{}>>".format(i) for i in _redir_names}.union(_redir_check)
_redir_check = frozenset(_redir_check)
Operator = group(
    r"\*\*=?",
    r">>=?",
    r"<<=?",
    r"!=",
    r"//=?",
    r"->",
    r"@\$\(?",
    r"\|\|",
    "&&",
    r"@\(",
    r"!\(",
    r"!\[",
    r"\$\(",
    r"\$\[",
    r"\${",
    r"\?\?",
    r"\?",
    AUGASSIGN_OPS,
    r"~",
)

Bracket = "[][(){}]"
Special = group(r"\r?\n", r"\.\.\.", r"[:;.,@]")
Funny = group(Operator, Bracket, Special)

PlainToken = group(IORedirect, Number, Funny, String, Name_RE, SearchPath)

# First (or only) line of ' or " string.
ContStr = group(
    StringPrefix + r"'[^\n'\\]*(?:\\.[^\n'\\]*)*" + group("'", r"\\\r?\n"),
    StringPrefix + r'"[^\n"\\]*(?:\\.[^\n"\\]*)*' + group('"', r"\\\r?\n"),
)
PseudoExtras = group(r"\\\r?\n|\Z", Comment, Triple, SearchPath)
PseudoToken = Whitespace + group(
    PseudoExtras, IORedirect, Number, Funny, ContStr, Name_RE
)


def _compile(expr):
    return re.compile(expr, re.UNICODE)


endpats = {
    "'": Single,
    '"': Double,
    "'''": Single3,
    '"""': Double3,
    "r'''": Single3,
    'r"""': Double3,
    "b'''": Single3,
    'b"""': Double3,
    "f'''": Single3,
    'f"""': Double3,
    "R'''": Single3,
    'R"""': Double3,
    "B'''": Single3,
    'B"""': Double3,
    "F'''": Single3,
    'F"""': Double3,
    "br'''": Single3,
    'br"""': Double3,
    "fr'''": Single3,
    'fr"""': Double3,
    "fp'''": Single3,
    'fp"""': Double3,
    "bR'''": Single3,
    'bR"""': Double3,
    "Br'''": Single3,
    'Br"""': Double3,
    "BR'''": Single3,
    'BR"""': Double3,
    "rb'''": Single3,
    'rb"""': Double3,
    "rf'''": Single3,
    'rf"""': Double3,
    "Rb'''": Single3,
    'Rb"""': Double3,
    "Fr'''": Single3,
    'Fr"""': Double3,
    "Fp'''": Single3,
    'Fp"""': Double3,
    "rB'''": Single3,
    'rB"""': Double3,
    "rF'''": Single3,
    'rF"""': Double3,
    "RB'''": Single3,
    'RB"""': Double3,
    "RF'''": Single3,
    'RF"""': Double3,
    "u'''": Single3,
    'u"""': Double3,
    "U'''": Single3,
    'U"""': Double3,
    "p'''": Single3,