# -----------------------------------------------------------------------------
# ply: lex.py
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

__version__    = '3.11'
__tabversion__ = '3.10'

import re
import sys
import types
import copy
import os
import inspect

# This tuple contains known string types
try:
    # Python 2.6
    StringTypes = (types.StringType, types.UnicodeType)
except AttributeError:
    # Python 3.0
    StringTypes = (str, bytes)

# This regular expression is used to match valid token names
_is_identifier = re.compile(r'^[a-zA-Z0-9_]+$')

# Exception thrown when invalid token encountered and no default error
# handler is defined.
class LexError(Exception):
    def __init__(self, message, s):
        self.args = (message,)
        self.text = s


# Token class.  This class is used to represent the tokens produced.
class LexToken(object):
    def __str__(self):
        return 'LexToken(%s,%r,%d,%d)' % (self.type, self.value, self.lineno, self.lexpos)

    def __repr__(self):
        return str(self)


# This object is a stand-in for a logging object created by the
# logging module.

class PlyLogger(object):
    def __init__(self, f):
        self.f = f

    def critical(self, msg, *args, **kwargs):
        self.f.write((msg % args) + '\n')

    def warning(self, msg, *args, **kwargs):
        self.f.write('WARNING: ' + (msg % args) + '\n')

    def error(self, msg, *args, **kwargs):
        self.f.write('ERROR: ' + (msg % args) + '\n')

    info = critical
    debug = critical


# Null logger is used when no output is generated. Does nothing.
class NullLogger(object):
    def __getattribute__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return self


# -----------------------------------------------------------------------------
#                        === Lexing Engine ===
#
# The following Lexer class implements the lexer runtime.   There are only
# a few public methods and attributes:
#
#    input()          -  Store a new string in the lexer
#    token()          -  Get the next token
#    clone()          -  Clone the lexer
#
#    lineno           -  Current line number
#    lexpos           -  Current position in the input string
# -----------------------------------------------------------------------------

class Lexer:
    def __init__(self):
        self.lexre = None             # Master regular expression. This is a list of
                                      # tuples (re, findex) where re is a compiled
                                      # regular expression and findex is a list
                                      # mapping regex group numbers to rules
        self.lexretext = None         # Current regular expression strings
        self.lexstatere = {}          # Dictionary mapping lexer states to master regexs
        self.lexstateretext = {}      # Dictionary mapping lexer states to regex strings
        self.lexstaterenames = {}     # Dictionary mapping lexer states to symbol names
        self.lexstate = 'INITIAL'     # Current lexer state
        self.lexstatestack = []       # Stack of lexer states
        self.lexstateinfo = None      # State information
        self.lexstateignore = {}      # Dictionary of ignored characters for each state
        self.lexstateerrorf = {}      # Dictionary of error functions for each state
        self.lexstateeoff = {}        # Dictionary of eof functions for each state
        self.lexreflags = 0           # Optional re compile flags
        self.lexdata = None           # Actual input data (as a string)
        self.lexpos = 0               # Current position in input text
        self.lexlen = 0               # Length of the input text
        self.lexerrorf = None         # Error rule (if any)
        self.lexeoff = None           # EOF rule (if any)
        self.lextokens = None         # List of valid tokens
        self.lexignore = ''           # Ignored characters
        self.lexliterals = ''         # Literal characters that can be passed through
        self.lexmodule = None         # Module
        self.lineno = 1               # Current line number
        self.lexoptimize = False      # Optimized mode

    def clone(self, object=None):
        c = copy.copy(self)

        # If the object parameter has been supplied, it means we are attaching the
        # lexer to a new object.  In this case, we have to rebind all methods in
        # the lexstatere and lexstateerrorf tables.

        if object:
            newtab = {}
            for key, ritem in self.lexstatere.items():
                newre = []
                for cre, findex in ritem:
                    newfindex = []
                    for f in findex:
                        if not f or not f[0]:
                            newfindex.append(f)
                            continue
                        newfindex.append((getattr(object, f[0].__name__), f[1]))
                newre.append((cre, newfindex))
                newtab[key] = newre
            c.lexstatere = newtab
            c.lexstateerrorf = {}
            for key, ef in self.lexstateerrorf.items():
                c.lexstateerrorf[key] = getattr(object, ef.__name__)
            c.lexmodule = object
        return c

    # ------------------------------------------------------------
    # writetab() - Write lexer information to a table file
    # ------------------------------------------------------------
    def writetab(self, lextab, outputdir=''):
        if isinstance(lextab, types.ModuleType):
            raise IOError("Won't overwrite existing lextab module")
        basetabmodule = lextab.split('.')[-1]
        filename = os.path.join(outputdir, basetabmodule) + '.py'
        with open(filename, 'w') as tf:
            tf.write('# %s.py. This file automatically created by PLY (version %s). Don\'t edit!\n' % (basetabmodule, __version__))
            tf.write('_tabversion   = %s\n' % repr(__tabversion__))
            tf.write('_lextokens    = set(%s)\n' % repr(tuple(sorted(self.lextokens))))
            tf.write('_lexreflags   = %s\n' % repr(int(self.lexreflags)))
            tf.write('_lexliterals  = %s\n' % repr(self.lexliterals))
            tf.write('_lexstateinfo = %s\n' % repr(self.lexstateinfo))

            # Rewrite the lexstatere table, replacing function objects with function names
            tabre = {}
            for statename, lre in self.lexstatere.items():
                titem = []
                for (pat, func), retext, renames in zip(lre, self.lexstateretext[statename], self.lexstaterenames[statename]):
                    titem.append((retext, _funcs_to_names(func, renames)))
                tabre[statename] = titem

            tf.write('_lexstatere   = %s\n' % repr(tabre))
            tf.write('_lexstateignore = %s\n' % repr(self.lexstateignore))

            taberr = {}
            for statename, ef in self.lexstateerrorf.items():
                taberr[statename] = ef.__name__ if ef else None
            tf.write('_lexstateerrorf = %s\n' % repr(taberr))

            tabeof = {}
            for statename, ef in self.lexstateeoff.items():
                tabeof[statename] = ef.__name__ if ef else None
            tf.write('_lexstateeoff = %s\n' % repr(tabeof))

    # ------------------------------------------------------------
    # readtab() - Read lexer information from a tab file
    # ------------------------------------------------------------
    def readtab(self, tabfile, fdict):
        if isinstance(tabfile, types.ModuleType):
            lextab = tabfile
        else:
            exec('import %s' % tabfile)
            lextab = sys.modules[tabfile]

        if getattr(lextab, '_tabversion', '0.0') != __tabversion__:
            raise ImportError('Inconsistent PLY version')

        self.lextokens      = lextab._lextokens
        self.lexreflags     = lextab._lexreflags
        self.lexliterals    = lextab._lexliterals
        self.lextokens_all  = self.lextokens | set(self.lexliterals)
        self.lexstateinfo   = lextab._lexstateinfo
        self.lexstateignore = lextab._lexstateignore
        self.lexstatere     = {}
        self.lexstateretext = {}
        for statename, lre in lextab._lexstatere.items():
            titem = []
            txtitem = []
            for pat, func_name in lre:
                titem.append((re.compile(pat, lextab._lexreflags), _names_to_funcs(func_name, fdict)))

            self.lexstatere[statename] = titem
            self.lexstateretext[statename] = txtitem

        self.lexstateerrorf = {}
        for statename, ef in lextab._lexstateerrorf.items():
            self.lexstateerrorf[statename] = fdict[ef]

        self.lexstateeoff = {}
        for statename, ef in lextab._lexstateeoff.items():
            self.lexstateeoff[statename] = fdict[ef]

        self.begin('INITIAL')

    # ------------------------------------------------------------
    # input() - Push a new string into the lexer
    # ------------------------------------------------------------
    def input(self, s):
        # Pull off the first character to see if s looks like a string
        c = s[:1]
        if not isinstance(c, StringTypes):
            raise ValueError('Expected a string')
      