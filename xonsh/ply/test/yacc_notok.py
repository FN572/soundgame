# -----------------------------------------------------------------------------
# yacc_notok.py
#
# A grammar, but we forgot to import the tokens list
# -----------------------------------------------------------------------------

import sys

if ".." not in sys.path: sys.path.insert(0,"..")
import ply.yacc as yacc

# Parsing rules
precedence = (
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE'),
    ('right','UMINUS'),
    )

# dictionary of names
names = { }

def p_statement_assign(t):
    'statement : NAME EQUALS expression'
  