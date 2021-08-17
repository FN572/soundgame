
# -*- coding: utf-8 -*-
"""
github3.gists.history
---------------------

Module containing the logic for the GistHistory object.

"""
from __future__ import unicode_literals

from ..models import GitHubCore
from ..users import User


class GistHistory(GitHubCore):

    """Thisobject represents one version (or revision) of a gist.

    Two history instances can be checked like so::

        h1 == h2
        h1 != h2

    And is equivalent to::

        h1.version == h2.version
        h1.version != h2.version

    """
