
# lex_literal2.py
#
# Bad literal specification

import sys
if ".." not in sys.path: sys.path.insert(0,"..")

import ply.lex as lex

tokens = [
    "NUMBER",
    ]

literals = 23

def t_NUMBER(t):
    r'\d+'
    return t

def t_error(t):
    pass

lex.lex()

