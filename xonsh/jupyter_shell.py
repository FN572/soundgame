
"""An interactive shell for the Jupyter kernel."""
import io
import sys
import builtins

from xonsh.base_shell import BaseShell


class StdJupyterRedirectBuf(io.RawIOBase):
    """Redirects standard I/O buffers to the Jupyter kernel."""

    def __init__(self, redirect):
        self.redirect = redirect
        self.encoding = redirect.encoding
        self.errors = redirect.errors

    def fileno(self):
        """Returns the file descriptor of the std buffer."""
        return self.redirect.fileno()

    def seek(self, offset, whence=io.SEEK_SET):
        """Sets the location in both the stdbuf and the membuf."""
        raise io.UnsupportedOperation("cannot seek Jupyter redirect")

    def truncate(self, size=None):
        """Truncate both buffers."""
        raise io.UnsupportedOperation("cannot truncate Jupyter redirect")

    def readinto(self, b):
        """Read bytes into buffer from both streams."""
        raise io.UnsupportedOperation("cannot read into Jupyter redirect")