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

    if len(p) == 2 and p[1]:
        p[0] = {}
        line, stat = p[1]
        p[0][line] = stat
    elif len(p) == 3:
        p[0] = p[1]
        if not p[0]:
            p[0] = {}
        if p[2]:
            line, stat = p[2]
            p[0][line] = stat

# This catch-all rule is used for any catastrophic errors.  In this case,
# we simply return nothing


def p_program_error(p):
    '''program : error'''
    p[0] = None
    p.parser.error = 1

# Format of all BASIC statements.


def p_statement(p):
    '''statement : INTEGER command NEWLINE'''
    if isinstance(p[2], str):
        print("%s %s %s" % (p[2], "AT LINE", p[1]))
        p[0] = None
        p.parser.error = 1
    else:
        lineno = int(p[1])
        p[0] = (lineno, p[2])

# Interactive statements.


def p_statement_interactive(p):
    '''statement : RUN NEWLINE
                 | LIST NEWLINE
                 | NEW NEWLINE'''
    p[0] = (0, (p[1], 0))

# Blank line number


def p_statement_blank(p):
    '''statement : INTEGER NEWLINE'''
    p[0] = (0, ('BLANK', int(p[1])))

# Error handling for malformed statements


def p_statement_bad(p):
    '''statement : INTEGER error NEWLINE'''
    print("MALFORMED STATEMENT AT LINE %s" % p[1])
    p[0] = None
    p.