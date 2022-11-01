# -----------------------------------------------------------------------------
# yacc_simple.py
#
# A simple, properly specifier grammar
# -----------------------------------------------------------------------------

from .calclex import tokens
from ply import yacc

# Parsing rules
precedence = (
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE'),
    ('right','UMINUS'),
    )

# dictionary of names
names = { }

def p_statement_assign(t):
    'statement : NAME