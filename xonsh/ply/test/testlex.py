
# testlex.py

import unittest
try:
    import StringIO
except ImportError:
    import io as StringIO

import sys
import os
import warnings
import platform

sys.path.insert(0,"..")
sys.tracebacklimit = 0

import ply.lex

try:
    from importlib.util import cache_from_source
except ImportError:
    # Python 2.7, but we don't care.
    cache_from_source = None


def make_pymodule_path(filename, optimization=None):
    path = os.path.dirname(filename)
    file = os.path.basename(filename)
    mod, ext = os.path.splitext(file)

    if sys.hexversion >= 0x3050000:
        fullpath = cache_from_source(filename, optimization=optimization)
    elif sys.hexversion >= 0x3040000:
        fullpath = cache_from_source(filename, ext=='.pyc')
    elif sys.hexversion >= 0x3020000:
        import imp
        modname = mod+"."+imp.get_tag()+ext
        fullpath = os.path.join(path,'__pycache__',modname)
    else:
        fullpath = filename
    return fullpath

def pymodule_out_exists(filename, optimization=None):
    return os.path.exists(make_pymodule_path(filename,
                                             optimization=optimization))

def pymodule_out_remove(filename, optimization=None):
    os.remove(make_pymodule_path(filename, optimization=optimization))

def implementation():
    if platform.system().startswith("Java"):
        return "Jython"
    elif hasattr(sys, "pypy_version_info"):
        return "PyPy"
    else:
        return "CPython"

test_pyo = (implementation() == 'CPython')

def check_expected(result, expected, contains=False):
    if sys.version_info[0] >= 3:
        if isinstance(result,str):
            result = result.encode('ascii')
        if isinstance(expected,str):
            expected = expected.encode('ascii')
    resultlines = result.splitlines()
    expectedlines = expected.splitlines()

    if len(resultlines) != len(expectedlines):
        return False

    for rline,eline in zip(resultlines,expectedlines):
        if contains:
            if eline not in rline:
                return False
        else:
            if not rline.endswith(eline):
                return False
    return True

def run_import(module):
    code = "import "+module
    exec(code)
    del sys.modules[module]
    
# Tests related to errors and warnings when building lexers
class LexErrorWarningTests(unittest.TestCase):
    def setUp(self):
        sys.stderr = StringIO.StringIO()
        sys.stdout = StringIO.StringIO()
        if sys.hexversion >= 0x3020000:
            warnings.filterwarnings('ignore',category=ResourceWarning)

    def tearDown(self):
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__
    def test_lex_doc1(self):
        self.assertRaises(SyntaxError,run_import,"lex_doc1")
        result = sys.stderr.getvalue()
        self.assert_(check_expected(result,
                              "lex_doc1.py:18: No regular expression defined for rule 't_NUMBER'\n"))
    def test_lex_dup1(self):
        self.assertRaises(SyntaxError,run_import,"lex_dup1")
        result = sys.stderr.getvalue()
        self.assert_(check_expected(result,
                                    "lex_dup1.py:20: Rule t_NUMBER redefined. Previously defined on line 18\n" ))        
        
    def test_lex_dup2(self):
        self.assertRaises(SyntaxError,run_import,"lex_dup2")
        result = sys.stderr.getvalue()