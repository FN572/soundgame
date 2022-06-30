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
    p.parser.error = 1

# Blank line


def p_statement_newline(p):
    '''statement : NEWLINE'''
    p[0] = None

# LET statement


def p_command_let(p):
    '''command : LET variable EQUALS expr'''
    p[0] = ('LET', p[2], p[4])


def p_command_let_bad(p):
    '''command : LET variable EQUALS error'''
    p[0] = "BAD EXPRESSION IN LET"

# READ statement


def p_command_read(p):
    '''command : READ varlist'''
    p[0] = ('READ', p[2])


def p_command_read_bad(p):
    '''command : READ error'''
    p[0] = "MALFORMED VARIABLE LIST IN READ"

# DATA statement


def p_command_data(p):
    '''command : DATA numlist'''
    p[0] = ('DATA', p[2])


def p_command_data_bad(p):
    '''command : DATA error'''
    p[0] = "MALFORMED NUMBER LIST IN DATA"

# PRINT statement


def p_command_print(p):
    '''command : PRINT plist optend'''
    p[0] = ('PRINT', p[2], p[3])


def p_command_print_bad(p):
    '''command : PRINT error'''
    p[0] = "MALFORMED PRINT STATEMENT"

# Optional ending on PRINT. Either a comma (,) or semicolon (;)


def p_optend(p):
    '''optend : COMMA 
              | SEMI
              |'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = None

# PRINT statement with no arguments


def p_command_print_empty(p):
    '''command : PRINT'''
    p[0] = ('PRINT', [], None)

# GOTO statement


def p_command_goto(p):
    '''command : GOTO INTEGER'''
    p[0] = ('GOTO', int(p[2]))


def p_command_goto_bad(p):
    '''command : GOTO error'''
    p[0] = "INVALID LINE NUMBER IN GOTO"

# IF-THEN statement


def p_command_if(p):
    '''command : IF relexpr THEN INTEGER'''
    p[0] = ('IF', p[2], int(p[4]))


def p_command_if_bad(p):
    '''command : IF error THEN INTEGER'''
    p[0] = "BAD RELATIONAL EXPRESSION"


def p_command_if_bad2(p):
    '''command : IF relexpr THEN error'''
    p[0] = "INVALID LINE NUMBER IN THEN"

# FOR statement


def p_command_for(p):
    '''command : FOR ID EQUALS expr TO expr optstep'''
    p[0] = ('FOR', p[2], p[4], p[6], p[7])


def p_command_for_bad_initial(p):
    '''command : FOR ID EQUALS error TO expr optstep'''
    p[0] = "BAD INITIAL VALUE IN FOR STATEMENT"


def p_command_for_bad_final(p):
    '''command : FOR ID EQUALS expr TO error optstep'''
    p[0] = "BAD FINAL VALUE IN FOR STATEMENT"


def p