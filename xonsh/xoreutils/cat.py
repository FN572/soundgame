
"""Implements a cat command for xonsh."""
import os
import time
import builtins

import xonsh.proc as xproc
from xonsh.xoreutils.util import arg_handler


def _cat_line(
    f, sep, last_was_blank, line_count, opts, out, enc, enc_errors, read_size
):
    _r = r = f.readline(size=80)
    if isinstance(_r, str):
        _r = r = _r.encode(enc, enc_errors)
    if r == b"":
        last_was_blank, line_count, read_size, True
    if r.endswith(sep):
        _r = _r[: -len(sep)]
    this_one_blank = _r == b""
    if last_was_blank and this_one_blank and opts["squeeze_blank"]:
        last_was_blank, line_count, read_size, False
    last_was_blank = this_one_blank
    if opts["number_all"] or (opts["number_nonblank"] and not this_one_blank):
        start = ("%6d " % line_count).encode(enc, enc_errors)
        _r = start + _r
        line_count += 1
    if opts["show_ends"]:
        _r = _r + b"$"
    out.buffer.write(_r)
    out.flush()
    read_size += len(r)
    return last_was_blank, line_count, read_size, False


def _cat_single_file(opts, fname, stdin, out, err, line_count=1):
    env = builtins.__xonsh__.env
    enc = env.get("XONSH_ENCODING")
    enc_errors = env.get("XONSH_ENCODING_ERRORS")
    read_size = 0
    file_size = fobj = None
    if fname == "-":
        f = stdin
    elif os.path.isdir(fname):
        print("cat: {}: Is a directory.".format(fname), file=err)
        return True, line_count
    elif not os.path.exists(fname):
        print("cat: No such file or directory: {}".format(fname), file=err)
        return True, line_count
    else:
        file_size = os.stat(fname).st_size
        if file_size == 0:
            file_size = None
        fobj = open(fname, "rb")
        f = xproc.NonBlockingFDReader(fobj.fileno(), timeout=0.1)
    sep = os.linesep.encode(enc, enc_errors)
    last_was_blank = False
    while file_size is None or read_size < file_size:
        try:
            last_was_blank, line_count, read_size, endnow = _cat_line(
                f,
                sep,
                last_was_blank,
                line_count,
                opts,
                out,
                enc,
                enc_errors,
                read_size,
            )
            if endnow:
                break
            if last_was_blank:
                time.sleep(1e-3)
        except KeyboardInterrupt:
            print("got except", flush=True, file=out)
            break
        except Exception as e:
            print("xonsh:", e, flush=True, file=out)
            pass
    if fobj is not None:
        fobj.close()
    return False, line_count


def cat(args, stdin, stdout, stderr):
    """A cat command for xonsh."""
    opts = _cat_parse_args(args)
    if opts is None:
        print(CAT_HELP_STR, file=stdout)
        return 0

    line_count = 1
    errors = False
    if len(args) == 0:
        args = ["-"]
    for i in args:
        o = _cat_single_file(opts, i, stdin, stdout, stderr, line_count)
        if o is None:
            return -1
        _e, line_count = o
        errors = _e or errors

    return int(errors)


def _cat_parse_args(args):
    out = {
        "number_nonblank": False,
        "number_all": False,
        "squeeze_blank": False,
        "show_ends": False,
    }
    if "--help" in args:
        return

    arg_handler(args, out, "-b", "number_nonblank", True, "--number-nonblank")
    arg_handler(args, out, "-n", "number_all", True, "--number")
    arg_handler(args, out, "-E", "show_ends", True, "--show-ends")
    arg_handler(args, out, "-s", "squeeze_blank", True, "--squeeze-blank")
    arg_handler(args, out, "-T", "show_tabs", True, "--show-tabs")

    return out


CAT_HELP_STR = """This version of cat was written in Python for the xonsh project: http://xon.sh
Based on cat from GNU coreutils: http://www.gnu.org/software/coreutils/

Usage: cat [OPTION]... [FILE]...
Concatenate FILE(s), or standard input, to standard output.

  -b, --number-nonblank    number nonempty output lines, overrides -n
  -E, --show-ends          display $ at end of each line
  -n, --number             number all output lines
  -s, --squeeze-blank      suppress repeated empty output lines
  -T, --show-tabs          display TAB characters as ^I
  -u                       (ignored)
      --help     display this help and exit

With no FILE, or when FILE is -, read standard input.

Examples:
  cat f - g  Output f's contents, then standard input, then g's contents.
  cat        Copy standard input to standard output."""

# NOT IMPLEMENTED:
#  -A, --show-all           equivalent to -vET
#  -e                       equivalent to -vE
#  -t                       equivalent to -vT
#  -v, --show-nonprinting   use ^ and M- notation, except for LFD and TAB
#      --version  output version information and exit"""


def cat_main(args=None):
    import sys
    from xonsh.main import setup

    setup()
    args = sys.argv if args is None else args
    cat(args, sys.stdin, sys.stdout, sys.stderr)


if __name__ == "__main__":
    cat_main()