# -*- coding: utf-8 -*-

# Copyright 2015 Donne Martin. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

META_LOOKUP_GIT = {
    'git': 'The stupid content tracker.',
    '--version': 'Prints the Git suite version that the git program came from.',
    '--help': 'Prints the synopsis and a list of the most commonly used commands.',
    '-C': 'Run as if git was started in <path> instead of the current working directory.',
    '-c': 'Pass a configuration parameter to the command.',
    '--exec-path': 'Path to wherever your core Git programs are installed.',
    '--html-path': "Print the path, without trailing slash, where Git's HTML documentation is installed and exit.",
    '--man-path': 'Print the manpath (see man(1)) for the man pages for this version of Git and exit.',
    '--info-path': 'Print the path where the Info files documenting this version of Git are installed and exit.',
    '-p': 'Pipe all output into less (or if set, $PAGER) if standard output is a terminal.',
    '--paginate': 'Pipe all output into less (or if set, $PAGER) if standard output is a terminal.',
    '--no-pager': 'Do not pipe Git output into a pager.',
    '--git-dir=<path>': 'Set the path to the repository. This can also be controlled by setting the GIT_DIR environment variable.',
    '--work-tree=<path>': 'Set the path to the working tree. It can be an absolute path or a path relative to the current working directory.',
    '--namespace=<path>': 'Set the Git namespace. See gitnamespaces(7) for more details.',
    '--bare': 'Treat the repository as a bare repository. If GIT_DIR environment is not set, it is set to the current working directory.',
    '--no-replace-objects': 'Do not use replacement refs to replace Git objects.',
    '--literal-pathspecs': 'Treat pathspecs literally (i.e. no globbing, no pathspec magic).',
    '--glob-pathspecs': 'Add "glob" magic to all pathspec.',
    '--noglob-pathspecs': 'Add "literal" magic to all pathspec.',
    '--icase-pathspecs': 'Add "icase" magic to all pathspec.',
    'add': 'Add file contents to the index.',
    'am': 'Apply a series of patches from a mailbox.',
    'amend': 'Amend the previous commit.',
    'archive': 'Create an archive of files from a named tree.',
    'bisect': 'Use binary search to find the commit that introduced a bug.',
    'branch': 'List, create, or delete branches.',
    'branches': 'List all branches, including remotes.',
    'bundle': 'Move objects and refs by archive.',
    'c': 'Alias for git clone.',
    'ca': 'Alias for git add -A && git commit -av.',
    'checkout': 'Switch branches or restore working tree files.',
    'cherry-pick': 'Apply the changes introduced by some existing commits.',
    'citool': 'Graphical alternative to git-commit.',
    'clean': 'Remove untracked files from the working tree.',
    'clone': 'Clone a repository into a new directory.',
    'commit': 'Record changes to the repository.',
    'contributors': 'List repo contributors.',
    'describe': 'Describe a commit using the most recent tag reachable from it.',
    'diff': 'Show changes between commits, commit and working tree, etc.',
    'fetch': 'Download objects and refs from another repository.',
    'flow': 'Git branching model extensions.',
    'format-patch': 'Prepare patches for e-mail submission.',
    'gc': 'Cleanup unnecessary files and optimize the local repository.',
    'grep': 'Print lines matching a pattern.',
    'gui': 'A portable graphical interface to Git.',
    'init': 'Create an empty Git repository or reinitialize an existing one.',
    'log': 'Show commit logs.',
    'merge': 'Join two or more development histories together.',
    'mv': 'Move or rename a file, a directory, or a symlink.',
    'notes': 'Add or inspect object notes.',
    'pull': 'Fetch from and integrate with another repository or a local branch.',
    'push': 'Update remote refs along with associated objects.',
    'rebase': 'Forward-port local commits to the updated upstream head.',
    'reset': 'Reset current HEAD to the specified state.',
    'revert': 'Revert some existing commits.',
    'rm': 'Remove files from the working tree and from the index.',
    'shortlog': 'Summarize git log output.',
    'show': 'Show various types of objects.',
    'stage': 'Add file contents to the staging area.',
    'stash': 'Stash the changes in a dirty working directory away.',
    'status': 'Show the working tree status.',
    'submodule': 'Initialize, update or inspect submodules.',
    'tag': 'Create, list, delete or verify a tag object signed with GPG.',
    'tags': 'List all tags.',
    'worktree': 'Manage multiple working trees.',
    'gitk': 'The Git repository browser.',
    'config': 'Get and set repository or global options.',
    'fast-export': 'Git data exporter.',
    'fast-import': 'Backend for fast Git data importers.',
    'filter-branch': 'Rewrite branches.',
    'mergetool': 'Run merge conflict resolution tools to resolve merge conflicts.',
    'pack-refs': 'Pack heads and tags for efficient repository access.',
    'prune': 'Prune all unreachable objects from the object database.',
    'reflog': 'Manage reflog information.',
    'relink': 'Hardlink common objects in local repositories.',
    'remote': 'Manage set of tracked repositories.',
    'remotes': 'List set of tracked repositories.',
    'repack': 'Pack unpacked objects in a repository.',
    'replace': 'Create, list, delete refs to replace objects.',
    'annotate': 'Annotate file lines with commit information.',
    'blame': 'Show what revision and author last modified each line of a file.',
    'cherry': 'Find commits yet to be applied to upstream.',
    'count-objects': 'Count unpacked number of objects and their disk consumption.',
    'difftool': 'Show changes using common diff tools.',
    'fsck': 'Verifies the connectivity and validity of the objects in the database.',
    'get-tar-commit-id': 'Extract commit ID from an archive created using git-archive.',
    'help': 'Display help information about Git.',
    'instaweb': 'Instantly browse your working repository in gitweb.',
    'merge-tree': 'Show three-way merge without touching index.',
    'rerere': 'Reuse recorded resolution of conflicted merges.',
    'rev-parse': 'Pick out and massage parameters.',
    'show-branch': 'Show branches and their commits.',
    'verify-commit': 'Check the GPG signature of commits.',
    'verify-tag': 'Check the GPG signature of tags.',
    'whatchanged': 'Show logs with difference each commit introduces.',
    'gitweb': 'Git web interface (web frontend to Git repositories).',
    'archimport': 'Import an Arch repository into Git.',
    'cvsexportcommit': 'Export a single commit to a CVS checkout.',
    'cvsimport': 'Salvage your data out of another SCM people love to hate.',
    'cvsserver': 'A CVS server emulator for Git.',
    'imap-send': 'Send a collection of patches from stdin to an IMAP folder.',
    'p4': 'Import from and submit to Perforce repositories.',
    'quiltimport': 'Applies a quilt patchset onto the current branch.',
    'request-pull': 'Generates a summary of pending changes.',
    'send-email': 'Send a collection of patches as emails.',
    'svn': 'Bidirectional operation between a Subversion repository and Git.',
    'apply': 'Apply a patch to files and/or to the index.',
    'checkout-index': 'Copy files from the index to the working tree.',
    'commit-tree': 'Create a new commit object.',
    'hash-object': 'Compute object ID and optionally creates a blob from a file.',
    'index-pack': 'Build pack index file for an existing packed archive.',
    'lfs': 'Git extension for versioning large files.',
    'merge-file': 'Run a three-way file merge.',
    'merge-index': 'Run a merge for files needing merging.',
    'mktag': 'Creates a tag object.',
    'mktree': 'Build a tree-object from ls-tree formatted text.',
    'pack-objects': 'Create a packed archive of objects.',
    'prune-packed': 'Remove extra objects that are already in pack files.',
    'read-tree': 'Reads tree information into the index.',
    'symbolic-ref': 'Read, modify and delete symbolic refs.',
    'unpack-objects': 'Unpack objects from a packed archive.',
    'update-index': 'Register file contents in the working tree to the index.',
    'update-ref': 'Update the object name stored in a ref safely.',
    'write-tree': 'Create a tree object from the current index.',
    'cat-file': 'Provide content or type and size information for repository objects.',
    'diff-files': 'Compares files in the working tree and the index.',
    'diff-index': 'Compare a tree to the working tree or index.',
    'diff-tree': 'Compares the content and mode of blobs found via two tree objects.',
    'for-each-ref': 'Output information on each ref.',
    'ls-files': 'Show information about files in the index and the working tree.',
    'ls-remote': 'List references in a remote repository.',
    'ls-tree': 'List the contents of a tree object.',
    'merge-base': 'Find as good common ancestors as possible for a merge.',
    'name-rev': 'Find symbolic names for given revs.',
    'pack-redundant': 'Find redundant pack files.',
    'rev-list': 'Lists commit objects in reverse chronological order.',
    'show-index': 'Show packed archive index.',
    'show-ref': 'List references in a local repository.',
    'unpack-file': "Creates a temporary file with a blob's contents.",
    'var': 'Show a Git logical variable.',
    'verify-pack': 'Validate packed Git archive files.',
    'daemon': 'A really simple server for Git repositories.',
    'fetch-pack': 'Receive missing objects from another repository.',
    'http-backend': 'Server side implementation of Git over HTTP.',
    'send-pack': 'Push objects over Git protocol to another repository.',
    'update-server-info': 'Update auxiliary info file to help dumb servers.',
    'http-fetch': 'Download from a remote Git repository via HTTP.',
    'http-push': 'Push objects over HTTP/DAV to another repository.',
    'parse-remote': 'Routines to help parsing remote repository access parameters.',
    'receive-pack': 'Receive what is pushed into the repository.',
    'shell': 'Restricted login shell for Git-only SSH access.',
    'upload-archive': 'Send archive back to git-archive.',
    'upload-pack': 'Send objects packed back to git-fetch-pack.',
    'check-attr': 'Display gitattributes information.',
    'check-ignore': 'Debug gitignore / exclude files.',
    'check-mailmap': 'Show canonical names and email addresses of contacts.',
    'check-ref-format': 'Ensures that a reference name is well formed.',
    'column': 'Display data in columns.',
    'credential': 'Retrieve and store user credentials.',
    'credential-cache': 'Helper to temporarily store passwords in memory.',
    'credential-store': 'Helper to store credentials on disk.',
    'fmt-merge-msg': 'Produce a merge commit message.',
    'interpret-trailers': 'help add structured information into commit messages.',
    'mailinfo': 'Extracts patch and authorship from a single e-mail message.',
    'mailsplit': 'Simple UNIX mbox splitter program.',
    'merge-one-file': 'The standard helper program to use with git-merge-index.',
    'patch-id': 'Compute unique ID for a patch.',
    'sh-i18n': "Git's i18n setup code for shell scripts.",
    'sh-setup': 'Common Git shell script setup code.',
    'stripspace': 'Remove unnecessary whitespace.',
    'subtree': 'Merge subtrees together and split repository into subtrees.',
    'git-cvsserver': 'A CVS server emulator for Git.',
    'git-credential-osxkeychain': 'Cache GitHub credentials in the OS X Keychain.',
    'git-lfs': 'Git extension for versioning large files.',
    'git-receive-pack': 'Receive what is pushed into the repository',
    'git-shell': 'Restricted login shell for Git-only SSH access.',
    'git-subtree': 'Merge subtrees together and split repository into subtrees.',
    'git-upload-archive': 'Send archive back to git-archive.',
    'git-upload-pack': 'Send objects packed back to git-fetch-pack.',
    'git-flow': 'Git branching model extensions.',
    'gitchangelog': 'Generates a changelog from git tags and commit messages.',
}
META_LOOKUP_GIT_EXTRAS = {
    'git-extras': 'Various Git utilities.',
    'git-alias': 'Define, search and show aliases.',
    'git-archive-file': 'Export the current HEAD of the git repository to a archive.',
    'git-authors': 'Generate authors report.',
    'git-back': 'Undo and Stage latest commits.',
    'git-bug': 'Create bug branch.',
    'git-changelog': 'Generate a changelog report.',
    'git-chore': 'Create chore branch.',
    'git-clear': 'Rigorously clean up a repository.',
    'git-commits-since': 'Show commit logs since some date.',
    'git-contrib': "Show user's contributions",
    'git-count': 'Show commit count.',
    'git-create-branch': 'Create branches.',
    'git-delete-branch': 'Delete branches.',
    'git-delete-merged-branches': 'Delete merged branches.',
    'git-delete-submodule': 'Delete submodules.',
    'git-delete-tag': 'Delete tags.',
    'git-delta': 'Lists changed files.',
    'git-effort': 'Show effort statistics on file(s).',
    'git-feature': 'Create/Merge feature branch.',
    'git-fork': 'Fork a repo on github.',
    'git-fresh-branch': 'Create fresh branches.',
    'git-gh-pages': 'Create the GitHub Pages branch.',
    'git-graft': 'Merge and destroy a given branch.',
    'git-guilt': 'calculate change between two revisions.',
    'git-ignore-io': 'Get sample gitignore file.',
    'git-ignore': 'Add .gitignore patterns.',
    'git-info': 'Returns information on current repository.',
    'git-line-summary': 'Show repository summary by line.',
    'git-local-commits': 'List local commits.',
    'git-lock': 'Lock a file excluded from version control.',
    'git-locked': 'ls files that have been locked.',
    'git-merge-into': 'Merge one branch into another.',
    'git-merge-repo': 'Merge two repo histories.',
    'git-missing': 'Show commits missing from another branch.',
    'git-obliterate': 'Completely remove a file from the repository, including past commits and tags.',
    'git-pr': 'Checks out a pull request locally.',
    'git-psykorebase': 'Rebase a branch with a merge commit.',
    'git-pull-request': 'Checks out a pull request from GitHub.',
    'git-rebase-patch': 'Rebases a patch.',
    'git-refactor': 'Create refactor branch.',
    'git-release': 'Commit, tag and push changes to the repository.',
    'git-rename-tag': 'R