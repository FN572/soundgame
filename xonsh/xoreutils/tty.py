"""A tty implementation for xonsh"""
import os
import sys


def tty(args, stdin, stdout, stderr):
    """A tty command for xonsh."""
    if "--help" in args:
        print(TTY_HELP, file=stdout)
        return 0
    silent = False
    for i in ("-s", "--silent", "--quiet"):
        if i in args:
            silent = True
            args.remove(i)
    if len(args) > 0:
        if not silent:
            for i in args:
                print("tty: Invalid option: {}".format(i), file=stderr)
            print(