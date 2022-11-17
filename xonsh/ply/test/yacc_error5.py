# -----------------------------------------------------------------------------
# yacc_error5.py
#
# Lineno and position tracking with error tokens
# -----------------------------------------------------------------------------
import sys

if ".." not in sys.path: sys.path.insert(0,"..")
import ply.yacc as yacc

from calclex import tokens

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
    names[t[1]] = t[3]

def p_statement_assign_error(t):
    'statement : NAME EQUALS error'
    line_start, line_end = t.linespan(3)
    pos_start, pos_end = t.lexspan(3)
    print("Assignment Error at %d:%d to %d:%d" % (line_start,pos_start,l