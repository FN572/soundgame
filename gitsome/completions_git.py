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
    'clone': 'Clone a repositor