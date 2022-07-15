# -----------------------------------------------------------------------------
# calc.py
#
# A simple calculator with variables.   This is from O'Reilly's
# "Lex and Yacc", p. 63.
#
# This example uses unicode strings for tokens, docstrings, and input.
# -----------------------------------------------------------------------------

import sys
sys.path.insert(0, "../..")

tokens = (
    'NAME', 'NUMBER',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'EQUALS',
    'LPAREN', 'RPAREN',
)

# Tokens

t_PLUS = ur'\+'
t_MINUS = ur'-'
t_TIMES = ur'\*'
t_DIVIDE = ur'/'
t_EQUALS = ur'='
t_LPAREN = ur'\('
t_RPAREN = ur'\)'
t_NAME = ur'[a-zA-Z_][a-zA-Z0-9_]*'


def t_NUMBER(t):
    ur'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print "Integer value too large", t.value
        t.value = 0
    return t

t_ignore = u" \t"


def t_newline(t):
    ur'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# Build the lexer
import ply.lex as lex
lex.lex()

