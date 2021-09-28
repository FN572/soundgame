# -*- coding: utf-8 -*-
from ..models import GitHubCore
"""
github3.repos.issue_import
==========================

This module contains the ImportedIssue object for Github's import issue API

"""


class ImportedIssue(GitHubCore):
    """
    The :class:`ImportedIssue <ImportedIssue>` object. This represents
    information from the Import Issue API.

    See also: https://gist.github.com/jonmagic/5282384165e0f86ef105
    """

    IMPORT_CUST