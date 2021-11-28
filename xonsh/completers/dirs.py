from xonsh.completers.man import complete_from_man
from xonsh.completers.path import complete_dir


def complete_cd(prefix, line, start, end, ctx):
    """
    Completion for "cd", includes only valid directory names.
    """
    if start != 0 and line.split(" ")[0] == "cd":