
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