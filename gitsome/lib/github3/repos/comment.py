# -*- coding: utf-8 -*-
"""
github3.repos.comment
=====================

This module contains the RepoComment class

"""
from __future__ import unicode_literals

from ..decorators import requires_auth
from ..models import BaseComment
from ..users import User


class RepoComment(BaseComment):
    """The :class:`RepoComment <RepoComment>` object. This stores the
    information about a comment on a file in a repository.

    Two comment instances can be checked like so::

        c1 == c2
        c1 != c2

    And is equivalent to::

        c1.id == c2.id
        c1.id != c2.id

    """
    def _update_attributes(self, comment):
        super(RepoComment, self)._update_attributes(comment)
        #: Commit id on which the comment was made.
        self.commit_id = comment.get('commit_id')
        #: URL of the comment on GitHub.
        self.html_url = comment.get('html_url')
        #: The line number where the comment is located.
        self.line = comment.get('line')
        #: The path to the file where the comment was made.
        self.path = comment.get('path')
        #: The position in the diff where the comment was made.
        self.position = comment.get('position')
        #: datetime object r