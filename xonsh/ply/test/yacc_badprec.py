# -----------------------------------------------------------------------------
# yacc_badprec.py
#
# Bad precedence specifier
# -----------------------------------------------------------------------------
import sys

if ".." not in sys.path: sys.path.insert(0,"..")
import ply.yacc as yacc

from calclex import tokens

# Parsing rules
precedence = "blah"

# dictionary of names
names = { }

def p_statement_assign(t):
    'statement : NAME EQUALS expressio