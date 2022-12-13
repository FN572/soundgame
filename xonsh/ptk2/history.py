# -*- coding: utf-8 -*-
"""History object for use with prompt_toolkit."""
import builtins

import prompt_toolkit.history


class PromptToolkitHistory(prompt_toolkit.history.History):
    """History class that implements the prompt-toolkit histo