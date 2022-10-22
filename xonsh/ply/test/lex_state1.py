# lex_state1.py
#
# Bad state declaration

import sys
if ".." not in sys.path: sys.path.insert(0,"..")

import ply.lex as lex

tokens = [ 
    "PLUS",
    "MINUS",
    "NUMBER",
    ]

states = 'comment'

t_PLUS = r'\+'
t_MINUS = r'-'
t_NUMBER = r'\d+'

# Comments
def t_comment(t):
    r'/\*'
    t.le