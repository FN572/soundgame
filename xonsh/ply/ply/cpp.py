# -----------------------------------------------------------------------------
# ply: cpp.py
#
# Copyright (C) 2001-2019
# David M. Beazley (Dabeaz LLC)
# All rights reserved.
#
# Latest version: https://github.com/dabeaz/ply
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of David Beazley or Dabeaz LLC may be used to
#   endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------

# This module implements an ANSI-C style lexical preprocessor for PLY.
# -----------------------------------------------------------------------------
from __future__ import generators

import sys

# Some Python 3 compatibility shims
if sys.version_info.major < 3:
    STRING_TYPES = (str, unicode)
else:
    STRING_TYPES = str
    xrange = range

# -----------------------------------------------------------------------------
# Default preprocessor lexer definitions.   These tokens are enough to get
# a basic preprocessor working.   Other modules may import these if they want
# -----------------------------------------------------------------------------

tokens = (
   'CPP_ID','CPP_INTEGER', 'CPP_FLOAT', 'CPP_STRING', 'CPP_CHAR', 'CPP_WS', 'CPP_COMMENT1', 'CPP_COMMENT2', 'CPP_POUND','CPP_DPOUND'
)

literals = "+-*/%|&~^<>=!?()[]{}.,;:\\\'\""

# Whitespace
def t_CPP_WS(t):
    r'\s+'
    t.lexer.lineno += t.value.count("\n")
    return t

t_CPP_POUND = r'\#'
t_CPP_DPOUND = r'\#\#'

# Identifier
t_CPP_ID = r'[A-Za-z_][\w_]*'

# Integer literal
def CPP_INTEGER(t):
    r'(((((0x)|(0X))[0-9a-fA-F]+)|(\d+))([uU][lL]|[lL][uU]|[uU]|[lL])?)'
    return t

t_CPP_INTEGER = CPP_INTEGER

# Floating literal
t_CPP_FLOAT = r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?'

# String literal
def t_CPP_STRING(t):
    r'\"([^\\\n]|(\\(.|\n)))*?\"'
    t.lexer.lineno += t.value.count("\n")
    return t

# Character constant 'c' or L'c'
def t_CPP_CHAR(t):
    r'(L)?\'([^\\\n]|(\\(.|\n)))*?\''
    t.lexer.lineno += t.value.count("\n")
    return t

# Comment
def t_CPP_COMMENT1(t):
    r'(/\*(.|\n)*?\*/)'
    ncr = t.value.count("\n")
    t.lexer.lineno += ncr
    # replace with one space or a number of '\n'
    t.type = 'CPP_WS'; t.value = '\n' * ncr if ncr else ' '
    return t

# Line comment
def t_CPP_COMMENT2(t):
    r'(//.*?(\n|$))'
    # replace with '/n'
    t.type = 'CPP_WS'; t.value = '\n'
    return t

def t_error(t):
    t.type = t.value[0]
    t.value = t.value[0]
    t.lexer.skip(1)
    return t

import re
import copy
import time
import os.path

# -----------------------------------------------------------------------------
# trigraph()
#
# Given an input string, this function replaces all trigraph sequences.
# The following mapping is used:
#
#     ??=    #
#     ??/    \
#     ??'    ^
#     ??(    [
#     ??)    ]
#     ??!    |
#     ??<    {
#     ??>    }
#     ??-    ~
# -----------------------------------------------------------------------------

_trigraph_pat = re.compile(r'''\?\?[=/\'\(\)\!<>\-]''')
_trigraph_rep = {
    '=':'#',
    '/':'\\',
    "'":'^',
    '(':'[',
    ')':']',
    '!':'|',
    '<':'{',
    '>':'}',
    '-':'~'
}

def trigraph(input):
    return _trigraph_pat.sub(lambda g: _trigraph_rep[g.group()[-1]],input)

# ------------------------------------------------------------------
# Macro object
#
# This object holds information about preprocessor macros
#
#    .name      - Macro name (string)
#    .value     - Macro value (a list of tokens)
#    .arglist   - List of argument names
#    .variadic  - Boolean indicating whether or not variadic macro
#    .vararg    - Name of the variadic parameter
#
# When a macro is created, the macro replacement token sequence is
# pre-scanned and used to create patch lists that are later used
# during macro expansion
# ------------------------------------------------------------------

class Macro(object):
    def __init__(self,name,value,arglist=None,variadic=False):
        self.n