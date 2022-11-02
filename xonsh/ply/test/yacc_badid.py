# -----------------------------------------------------------------------------
# yacc_badid.py
#
# Attempt to define a rule with a bad-identifier name
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

def p_statement_expr(t):
    'statement : expression'
    print(t[1])

def p_statement_expr2(t):
    'statement : bad&rule'
    pass

def p_badrule(t):
    'bad&rule : expression'
    pass


def p_expression_binop(t):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TI