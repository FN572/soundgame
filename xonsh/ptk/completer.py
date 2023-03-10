
# -*- coding: utf-8 -*-
"""Completer implementation to use with prompt_toolkit."""
import os
import builtins

from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory


class PromptToolkitCompleter(Completer):
    """Simple prompt_toolkit Completer object.

    It just redirects requests to normal Xonsh completer.
    """

    def __init__(self, completer, ctx, shell):
        """Takes instance of xonsh.completer.Completer, the xonsh execution
        context, and the shell instance itself.
        """
        self.completer = completer
        self.ctx = ctx
        self.shell = shell
        self.hist_suggester = AutoSuggestFromHistory()

    def get_completions(self, document, complete_event):
        """Returns a generator for list of completions."""
        env = builtins.__xonsh__.env
        should_complete = complete_event.completion_requested or env.get(
            "UPDATE_COMPLETIONS_ON_KEYPRESS"
        )
        #  Only generate completions when the user hits tab.
        if not should_complete or self.completer is None:
            return
        # generate actual completions
        line = document.current_line.lstrip()
        line_ex = builtins.aliases.expand_alias(line)

        endidx = document.cursor_position_col
        begidx = line[:endidx].rfind(" ") + 1 if line[:endidx].rfind(" ") >= 0 else 0
        prefix = line[begidx:endidx]
        expand_offset = len(line_ex) - len(line)
        # get normal completions
        completions, l = self.completer.complete(
            prefix, line_ex, begidx + expand_offset, endidx + expand_offset, self.ctx
        )
        # completions from auto suggest
        sug_comp = None
        if env.get("AUTO_SUGGEST") and env.get("AUTO_SUGGEST_IN_COMPLETIONS"):
            sug_comp = self.suggestion_completion(document, line)
            if sug_comp is None:
                pass
            elif len(completions) == 0:
                completions = (sug_comp,)
            else:
                completions = set(completions)
                completions.discard(sug_comp)
                completions = (sug_comp,) + tuple(sorted(completions))
        # reserve space, if needed.
        if len(completions) <= 1:
            pass
        elif len(os.path.commonprefix(completions)) <= len(prefix):
            self.reserve_space()
        # Find common prefix (strip quoting)
        c_prefix = os.path.commonprefix([a.strip("'\"") for a in completions])
        # Find last split symbol, do not trim the last part
        while c_prefix:
            if c_prefix[-1] in r"/\.:@,":
                break
            c_prefix = c_prefix[:-1]
        # yield completions
        if sug_comp is None:
            pre = min(document.cursor_position_col - begidx, len(c_prefix))
        else:
            pre = len(c_prefix)
        for comp in completions:
            # do not display quote
            disp = comp[pre:].strip("'\"")
            yield Completion(comp, -l, display=disp)

    def suggestion_completion(self, document, line):
        """Provides a completion based on the current auto-suggestion."""
        cli = self.shell.prompter.cli
        sug = self.hist_suggester.get_suggestion(cli, cli.current_buffer, document)
        if sug is None:
            return None
        comp, _, _ = sug.text.partition(" ")
        _, _, prev = line.rpartition(" ")
        return prev + comp

    def reserve_space(self):
        cli = builtins.__xonsh__.shell.shell.prompter.cli
        window = cli.application.layout.children[0].content.children[1]

        if window and window.render_info:
            h = window.render_info.content_height
            r = builtins.__xonsh__.env.get("COMPLETIONS_MENU_ROWS")
            size = h + r

            def comp_height(cli):
                # If there is an autocompletion menu to be shown, make sure that o
                # layout has at least a minimal height in order to display it.
                if not cli.is_done:
                    return LayoutDimension(min=size)
                else:
                    return LayoutDimension()

            window._height = comp_height