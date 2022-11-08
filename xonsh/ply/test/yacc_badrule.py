# -----------------------------------------------------------------------------
# yacc_badrule.py
#
# Syntax problems in the rule strings
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
    'statement NAME EQUALS expression'
    names[t[1]] = t[3]

def p_statement_expr(t):
    'statement'
    print(t[1])

def p_expression_binop(t):
    '''