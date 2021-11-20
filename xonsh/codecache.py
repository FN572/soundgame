"""Tools for caching xonsh code."""
import os
import sys
import hashlib
import marshal
import builtins

from xonsh import __version__ as XONSH_VERSION
from xonsh.lazyasd import lazyobject
from xonsh.platform import PYTHON_VERSION_INFO_BYTES


def _splitpath(path, sofar=[]):
    folder, path = os.path.split(path)
    if path == "":
        return sofar[::-1]
    elif folder == "":
        return (sofar + [path])[::-1]
    else:
        return _splitpath(folder, sofar + [path])


@lazyobject
def _CHARACTER_MAP():
    cmap = {chr(o): "_%s" % chr(o + 32) for o in range(65, 91)}
    cmap.update({".": "_.", "_": "__"})
    return cmap


def _cache_renamer(path, code=False):
    if not code:
        path = os.path.realpath(path)
    o = ["".join(_CHARACTER_MAP.get(i, i) for i in w) for w in _splitpath(path)]
    o[-1] = "{}.{}".format(o[-1], sys.implementation.cache_tag)
    return o


def _make_if_not_exists(dirname):
    if not os.path.isdir(dirname):
        os.makedirs(dirname)


def should_use_cache(execer, mode):
    """
    Return ``True`` if caching has been enabled for this mode (through command
    line flags or environment variables)
    """
    if mode == "exec":
        return (execer.scriptcache or execer.cacheall) and (
            builtins.__xonsh__.env["XONSH_CACHE_SCRIPTS"]
            or builtins.__xonsh__.env["XONSH_CACHE_EVERYTHING"]
        )
    else:
        return execer.cacheall or builtins.__xonsh__.env["XONSH_CACHE_EVERYTHING"]


def run_compiled_code(code, glb, loc, mode):
    """
    Helper to run code in a given mode and context
    """
    if code is None:
        return
    if mode in {"exec", "single"}:
        func = exec
    else:
        func = eval
    func(code, glb, loc)


def get_cache_filename(fname, code=True):
    """
    Return the filename of the cache for the given filename.

    Cache filenames are similar to those used by the Mercurial DVCS for its
    internal store.

    The ``code`` switch should be true if we should use the code store rather
    than the script store.
    """
    datadir = builtins.__xonsh__.env["XONSH_DATA_DIR"]
    cachedir = os.path.join(
        datadir, "xonsh_code_cache" if code else "xonsh_script_cache"
    )
    cachefname = os.path.join(cachedir, *_cache_renamer(fname, code=code))
    return cachefname


def update_cache(ccode, cache_file_name):
    """
    Update the cache at ``cache_file_name`` to contain the compiled code
    represented by ``ccode``.
    """
    if cache_file_name is not None:
        _make_if_not_exists(os.path.dirname(cache_file_name))
        with open(cache_file_name, "wb") as cfile:
            cfile.write(XONSH_VERSION.encode() + b"\n")
            cfile.write(bytes(PYTHON_VERSION_INFO_BYTES) + b"\n")
            marshal.dump(ccode, cfile)


def _check_cache_versions(cfile):
    # version data should be < 1 kb
    ver = cfile.readline(1024).strip()
    if ver != XONSH_VERSION.encode():
        return False
    ver = cfile.readline(1024).strip()
    return ver == PYTHON_VERSION_INFO_BYTES


def compile_code(filename, code, execer, glb, loc, mode):
    """
    Wrapper for ``execer.compile`` to compile the given code
    """
    try:
        if not code.endswith("\n"):
            code += "\n"
        old_filename = execer.filename
        execer.filename = filename
        ccode = execer.compile(code, glbs=glb, locs=loc, mode=mode, filename=filename)
    except Exception:
        raise
    finally:
        execer.filename = old_filename
    return ccode


def script_cache_check(filename, cachefname):
    """
    Check whether the script cache for a particular file is valid.

    Returns a tuple containing: a boolean representing whether the cached code
    should be used, and the cached code (or ``None`` if the cache should not be
    used).
    """
    ccode = None
    run_cached = False
    if o