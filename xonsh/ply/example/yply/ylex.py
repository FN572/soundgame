# lexer for yacc-grammars
#
# Author: David Beazley (dave@dabeaz.com)
# Date  : October 2, 2006

import sys
sys.path.append("../..")

from ply import *

tokens = (
    'LITERAL', 'SECTION', 'TOKEN', 'LEFT', 'RIGHT', 'PREC', 'START', 'TYPE', 'NONASSOC', 'UNION', 'CODE',
    'ID', 'QLITERAL', 'NUMBER',
)

states = (('code', 'exclusive'),)

literals = [';', ',', '<', '>', '|', ':']
t_ignore = ' \t'

t_TOKEN = r'%token'
t_LEFT = r'%left'
t_RIGHT = r'%right'
t_NONASSOC = r'%nonassoc'
t_PREC = r'%prec'
t_START = r'%start'
t_TYPE = r'%type'
t_UNION = r'%union'
t_ID = r'[a-zA-Z_][a-zA-Z_0-9]*'
t_QLITERAL  = r'''(?P<quote>['"]).*?(?P=quote)'''
t_NUMBER = r'\d+'


def t_SECTION(t):
    r'%%'
    if getattr(t.lexer, "lastsection", 0):
        t.value = t.lexer.lexdata[t.lexpos + 2:]
        t.lexer.lexpos = len(t.lexer.lexdata)
    else:
        t.lexer.