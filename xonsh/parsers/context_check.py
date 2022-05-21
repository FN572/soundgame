import ast
import keyword
import collections

_all_keywords = frozenset(keyword.kwlist)


def _not_assignable(x, augassign=False):
    """
    If ``x`` represents a value that can be assigned to, return ``None``.
    Otherwise, return a string describing the object.  For use in generating
    meaningful syntax errors.
    """
    if augassign and isinstance(x, (ast.Tuple, ast.List)):
        return "literal"
    elif isinstance(x, (ast.Tuple, ast.List)):
        if len(x.elts) == 0:
            return "()"
        for i in x.elts:
            res = _not_assignable(i)
            if res is not None:
                return res
    elif isinstance(x, (ast.Set, ast.Dict, ast.Num, ast.Str, ast.Bytes)):
        return "literal"
    elif isinstance(x, ast.Call):
        return "function call"
    elif isinstance(x, ast.Lambda):
        return "lambda"
    eli