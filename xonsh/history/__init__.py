# amalgamate exclude
import os as _os

if _os.getenv("XONSH_DEBUG", ""):
    pass
else:
    import sys as _sys

    try:
        from xonsh.history import __amalgam__

        base = __amalgam__
        _sys.modules["xonsh.history.base"] = __amalgam__
   