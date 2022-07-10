# -----------------------------------------------------------------------------
# calc.py
#
# This example shows how to run the parser in a debugging mode
# with output routed to a logging object.
# -----------------------------------------------------------------------------

import sys
sys.path.insert(0, "../..")

if sys.version_info[0] >= 3:
    raw_input = input

tokens = (
    'NAME', 'NUMBER',
)

literals = ['=', '+', '-', '*', '/', '(', ')']

# Tokens

t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_ignore = " \t"


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1