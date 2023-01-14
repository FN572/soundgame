"""Implements a simple echo command for xonsh."""


def echo(args, stdin, stdout, stderr):
    """A simple echo command."""
    opts = _echo_parse_args(args)
    if opts is None:
        return
    if opts["help"]:
        print(ECHO_HELP, file=stdout)
        return 0
    ender = opts["end"]
    args = map(str, args)
    if opts["escapes"]:
        args = map(lambda x: x.encode().decode("unicode_escape"), args)
    print(*args, end=ender, file=stdout)


def _echo_parse_args(args):
    out = {"escapes": False, "end": "\n", "help": False}
    if "-e" in args:
        args.remove("-e")
        out["escapes"] = True
    if "-E" in args:
        args.remove("-E")
        out["escapes"] = False
    if "-n" in args:
        args.remove("-n")
        out["en