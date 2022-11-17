# -----------------------------------------------------------------------------
# yacc_error6.py
#
# Panic mode recovery test
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

def p_statements(t):
    'statements : statements statement'
    pass

def p_statements_1(t):
    'statements : statement'
    pass

def p_statement_assign(p):
    'statement : LPAREN NAME EQUALS expression RPAREN'
    print("%s=%s" % (p[2],p[4]))

def p_statement_expr(t):
    'statement : LPAREN expression RPAREN'
    print(t[1])

def p_expression_binop(t):
    '''expression : exp