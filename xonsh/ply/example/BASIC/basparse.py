# An implementation of Dartmouth BASIC (1964)
#

from ply import *
import basiclex

tokens = basiclex.tokens

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('left', 'POWER'),
    ('right', 'UMINUS')
)

# A BASIC program is a series of statements.  We represent the program as a
# dictionary of tuples indexed by line number.


def p_program(p):
    '''program : program statement
               | statement'''

    if len(p) == 2 and 