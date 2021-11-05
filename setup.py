#!/usr/bin/env python
# coding=utf-8

"""The gitsome installer."""
from __future__ import print_function, unicode_literals
import os
import sys
try:
    from setuptools import setup, find_packages
    from setuptools.command.sdist import sdist
    from setuptools.command.install import install
    from setuptools.command.develop import develop
    HAVE_SETUPTOOLS = True
except ImportError:
    from distutils.core import setup
    from distutils.command.sdist import sdist as sdist
    from distutils.command.install import install as install
    HAVE_SETUPTOOLS = False
from gitsome.__init__ import __version__ as VERSION


TABLES = ['xonsh/lexer_table.py', 'xonsh/parser_table.py']


def clean_tables():
    for f in TABLES:
        if os.path.isfile(f):
            os.remove(f)
            print('Remove ' + f)


def build_tables():
    print('Building lexer and parser tables.')
    sys.path.insert(0, os.path.dirname(__file__))
    