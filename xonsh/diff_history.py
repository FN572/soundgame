
# -*- coding: utf-8 -*-
"""Tools for diff'ing two xonsh history files in a meaningful fashion."""
import difflib
import datetime
import itertools
import argparse

from xonsh.lazyjson import LazyJSON
from xonsh.tools import print_color

NO_COLOR_S = "{NO_COLOR}"
RED_S = "{RED}"
GREEN_S = "{GREEN}"
BOLD_RED_S = "{BOLD_RED}"
BOLD_GREEN_S = "{BOLD_GREEN}"

# intern some strings
REPLACE_S = "replace"
DELETE_S = "delete"
INSERT_S = "insert"
EQUAL_S = "equal"


def bold_str_diff(a, b, sm=None):
    if sm is None:
        sm = difflib.SequenceMatcher()
    aline = RED_S + "- "
    bline = GREEN_S + "+ "
    sm.set_seqs(a, b)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == REPLACE_S:
            aline += BOLD_RED_S + a[i1:i2] + RED_S
            bline += BOLD_GREEN_S + b[j1:j2] + GREEN_S
        elif tag == DELETE_S:
            aline += BOLD_RED_S + a[i1:i2] + RED_S
        elif tag == INSERT_S:
            bline += BOLD_GREEN_S + b[j1:j2] + GREEN_S
        elif tag == EQUAL_S:
            aline += a[i1:i2]
            bline += b[j1:j2]
        else:
            raise RuntimeError("tag not understood")
    return aline + NO_COLOR_S + "\n" + bline + NO_COLOR_S + "\n"


def redline(line):
    return "{red}- {line}{no_color}\n".format(red=RED_S, line=line, no_color=NO_COLOR_S)


def greenline(line):
    return "{green}+ {line}{no_color}\n".format(
        green=GREEN_S, line=line, no_color=NO_COLOR_S
    )


def highlighted_ndiff(a, b):
    """Returns a highlighted string, with bold characters where different."""
    s = ""
    sm = difflib.SequenceMatcher()
    sm.set_seqs(a, b)
    linesm = difflib.SequenceMatcher()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == REPLACE_S:
            for aline, bline in itertools.zip_longest(a[i1:i2], b[j1:j2]):
                if bline is None:
                    s += redline(aline)
                elif aline is None:
                    s += greenline(bline)
                else:
                    s += bold_str_diff(aline, bline, sm=linesm)
        elif tag == DELETE_S:
            for aline in a[i1:i2]:
                s += redline(aline)
        elif tag == INSERT_S:
            for bline in b[j1:j2]:
                s += greenline(bline)
        elif tag == EQUAL_S:
            for aline in a[i1:i2]:
                s += "  " + aline + "\n"
        else:
            raise RuntimeError("tag not understood")
    return s


class HistoryDiffer(object):
    """This class helps diff two xonsh history files."""

    def __init__(self, afile, bfile, reopen=False, verbose=False):
        """
        Parameters
        ----------
        afile : file handle or str
            The first file to diff
        bfile : file handle or str
            The second file to diff
        reopen : bool, optional
            Whether or not to reopen the file handles each time. The default here is
            opposite from the LazyJSON default because we know that we will be doing
            a lot of reading so it is best to keep the handles open.
        verbose : bool, optional
            Whether to print a verbose amount of information.
        """
        self.a = LazyJSON(afile, reopen=reopen)
        self.b = LazyJSON(bfile, reopen=reopen)
        self.verbose = verbose
        self.sm = difflib.SequenceMatcher(autojunk=False)

    def __del__(self):
        self.a.close()
        self.b.close()

    def __str__(self):
        return self.format()

    def _header_line(self, lj):
        s = lj._f.name if hasattr(lj._f, "name") else ""
        s += " (" + lj["sessionid"] + ")"
        s += " [locked]" if lj["locked"] else " [unlocked]"
        ts = lj["ts"].load()
        ts0 = datetime.datetime.fromtimestamp(ts[0])
        s += " started: " + ts0.isoformat(" ")
        if ts[1] is not None:
            ts1 = datetime.datetime.fromtimestamp(ts[1])
            s += " stopped: " + ts1.isoformat(" ") + " runtime: " + str(ts1 - ts0)
        return s

    def header(self):
        """Computes a header string difference."""
        s = "{red}--- {aline}{no_color}\n" "{green}+++ {bline}{no_color}"
        s = s.format(
            aline=self._header_line(self.a),
            bline=self._header_line(self.b),
            red=RED_S,
            green=GREEN_S,
            no_color=NO_COLOR_S,
        )
        return s

    def _env_both_diff(self, in_both, aenv, benv):
        sm = self.sm
        s = ""
        for key in sorted(in_both):
            aval = aenv[key]
            bval = benv[key]
            if aval == bval:
                continue
            s += "{0!r} is in both, but differs\n".format(key)
            s += bold_str_diff(aval, bval, sm=sm) + "\n"
        return s

    def _env_in_one_diff(self, x, y, color, xid, xenv):
        only_x = sorted(x - y)
        if len(only_x) == 0:
            return ""
        if self.verbose:
            xstr = ",\n".join(
                ["    {0!r}: {1!r}".format(key, xenv[key]) for key in only_x]
            )
            xstr = "\n" + xstr
        else:
            xstr = ", ".join(["{0!r}".format(key) for key in only_x])
        in_x = "These vars are only in {color}{xid}{no_color}: {{{xstr}}}\n\n"
        return in_x.format(xid=xid, color=color, no_color=NO_COLOR_S, xstr=xstr)

    def envdiff(self):
        """Computes the difference between the environments."""
        aenv = self.a["env"].load()
        benv = self.b["env"].load()
        akeys = frozenset(aenv)
        bkeys = frozenset(benv)
        in_both = akeys & bkeys
        if len(in_both) == len(akeys) == len(bkeys):
            keydiff = self._env_both_diff(in_both, aenv, benv)
            if len(keydiff) == 0:
                return ""
            in_a = in_b = ""
        else:
            keydiff = self._env_both_diff(in_both, aenv, benv)
            in_a = self._env_in_one_diff(akeys, bkeys, RED_S, self.a["sessionid"], aenv)
            in_b = self._env_in_one_diff(
                bkeys, akeys, GREEN_S, self.b["sessionid"], benv
            )
        s = "Environment\n-----------\n" + in_a + keydiff + in_b
        return s

    def _cmd_in_one_diff(self, inp, i, xlj, xid, color):
        s = "cmd #{i} only in {color}{xid}{no_color}:\n"
        s = s.format(i=i, color=color, xid=xid, no_color=NO_COLOR_S)
        lines = inp.splitlines()
        lt = "{color}{pre}{no_color} {line}\n"
        s += lt.format(color=color, no_color=NO_COLOR_S, line=lines[0], pre=">>>")
        for line in lines[1:]:
            s += lt.format(color=color, no_color=NO_COLOR_S, line=line, pre="...")
        if not self.verbose:
            return s + "\n"
        out = xlj["cmds"][0].get("out", "Note: no output stored")
        s += out.rstrip() + "\n\n"
        return s

    def _cmd_out_and_rtn_diff(self, i, j):
        s = ""
        aout = self.a["cmds"][i].get("out", None)
        bout = self.b["cmds"][j].get("out", None)
        if aout is None and bout is None:
            # s += 'Note: neither output stored\n'
            pass
        elif bout is None:
            aid = self.a["sessionid"]
            s += "Note: only {red}{aid}{no_color} output stored\n".format(
                red=RED_S, aid=aid, no_color=NO_COLOR_S
            )
        elif aout is None:
            bid = self.b["sessionid"]
            s += "Note: only {green}{bid}{no_color} output stored\n".format(
                green=GREEN_S, bid=bid, no_color=NO_COLOR_S
            )
        elif aout != bout:
            s += "Outputs differ\n"
            s += highlighted_ndiff(aout.splitlines(), bout.splitlines())
        else:
            pass
        artn = self.a["cmds"][i]["rtn"]
        brtn = self.b["cmds"][j]["rtn"]
        if artn != brtn:
            s += (
                "Return vals {red}{artn}{no_color} & {green}{brtn}{no_color} differ\n"
            ).format(
                red=RED_S, green=GREEN_S, no_color=NO_COLOR_S, artn=artn, brtn=brtn
            )
        return s

    def _cmd_replace_diff(self, i, ainp, aid, j, binp, bid):
        s = (
            "cmd #{i} in {red}{aid}{no_color} is replaced by \n"
            "cmd #{j} in {green}{bid}{no_color}:\n"
        )
        s = s.format(
            i=i, aid=aid, j=j, bid=bid, red=RED_S, green=GREEN_S, no_color=NO_COLOR_S
        )
        s += highlighted_ndiff(ainp.splitlines(), binp.splitlines())
        if not self.verbose:
            return s + "\n"
        s += self._cmd_out_and_rtn_diff(i, j)
        return s + "\n"

    def cmdsdiff(self):
        """Computes the difference of the commands themselves."""
        aid = self.a["sessionid"]
        bid = self.b["sessionid"]
        ainps = [c["inp"] for c in self.a["cmds"]]
        binps = [c["inp"] for c in self.b["cmds"]]
        sm = self.sm
        sm.set_seqs(ainps, binps)
        s = ""
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == REPLACE_S:
                zipper = itertools.zip_longest
                for i, ainp, j, binp in zipper(
                    range(i1, i2), ainps[i1:i2], range(j1, j2), binps[j1:j2]
                ):
                    if j is None:
                        s += self._cmd_in_one_diff(ainp, i, self.a, aid, RED_S)
                    elif i is None:
                        s += self._cmd_in_one_diff(binp, j, self.b, bid, GREEN_S)
                    else:
                        self._cmd_replace_diff(i, ainp, aid, j, binp, bid)
            elif tag == DELETE_S:
                for i, inp in enumerate(ainps[i1:i2], i1):
                    s += self._cmd_in_one_diff(inp, i, self.a, aid, RED_S)
            elif tag == INSERT_S:
                for j, inp in enumerate(binps[j1:j2], j1):
                    s += self._cmd_in_one_diff(inp, j, self.b, bid, GREEN_S)
            elif tag == EQUAL_S:
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    odiff = self._cmd_out_and_rtn_diff(i, j)
                    if len(odiff) > 0:
                        h = (
                            "cmd #{i} in {red}{aid}{no_color} input is the same as \n"
                            "cmd #{j} in {green}{bid}{no_color}, but output differs:\n"
                        )
                        s += h.format(
                            i=i,
                            aid=aid,
                            j=j,
                            bid=bid,
                            red=RED_S,
                            green=GREEN_S,
                            no_color=NO_COLOR_S,
                        )
                        s += odiff + "\n"
            else:
                raise RuntimeError("tag not understood")
        if len(s) == 0:
            return s
        return "Commands\n--------\n" + s

    def format(self):
        """Formats the difference between the two history files."""
        s = self.header()
        ed = self.envdiff()
        if len(ed) > 0:
            s += "\n\n" + ed
        cd = self.cmdsdiff()
        if len(cd) > 0:
            s += "\n\n" + cd
        return s.rstrip()


_HD_PARSER = None


def dh_create_parser(p=None):
    global _HD_PARSER
    p_was_none = p is None
    if _HD_PARSER is not None and p_was_none:
        return _HD_PARSER
    if p_was_none:
        p = argparse.ArgumentParser(
            "diff-history", description="diffs two xonsh history files"
        )
    p.add_argument(
        "--reopen",
        dest="reopen",
        default=False,
        action="store_true",
        help="make lazy file loading reopen files each time",
    )
    p.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        default=False,
        action="store_true",
        help="whether to print even more information",
    )
    p.add_argument("a", help="first file in diff")
    p.add_argument("b", help="second file in diff")
    if p_was_none:
        _HD_PARSER = p
    return p


def dh_main_action(ns, hist=None, stdout=None, stderr=None):
    hd = HistoryDiffer(ns.a, ns.b, reopen=ns.reopen, verbose=ns.verbose)
    print_color(hd.format(), file=stdout)