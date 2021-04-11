
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

COMPLETIONS_GH = {
    'configure': {
        'desc': "Configures gitsome.",
        'args': {},
        'opts': {
            '-e': 'flag (opt) configure GitHub Enterprise.',
            '--enterprise': 'flag (opt) configure GitHub Enterprise.',
        },
    },
    'create-comment': {
        'desc': 'Creates a comment on the given issue.',
        'args': {
            'octocat/Spoon-Knife/1': 'str (req) user/repo/issue_number combo.',
        },
        'opts': {
            '-t': 'see associated -- option for details.',
            '--text': 'str (req) comment text.',
        },
    },
    'create-issue': {
        'desc': 'Creates an issue.',
        'args': {
            'octocat/Spoon-Knife': 'str (req) user/repository combo.',
        },
        'opts': {
            '-t': 'see associated -- option for details.',
            '--issue_title': 'str (req) issue title.',
            '-d': 'str (opt) issue description.',
            '--issue_desc': 'str (opt) issue description.',
        },
    },
    'create-repo': {
        'desc': 'Creates a repository.',
        'args': {
            'Spoon-Knife': 'str (req) repository name.',
        },
        'opts': {
            '-d': 'str (opt) repo description',
            '--repo_desc': 'str (opt) repo description.',
            '-pr': 'flag (opt) create a private repo',
            '--private': 'flag (opt) create a private repo',
        },
    },
    'emails': {
        'desc': "Lists all the user's registered emails.",
        'args': {},
        'opts': {},
    },
    'emojis': {
        'desc': 'Lists all GitHub supported emojis.',
        'args': {},
        'opts': {
            '-p': 'flag (req) show results in a pager.',
            '--pager': 'flag (req) show results in a pager.',
        },
    },
    'feed': {
        'desc': "Lists all activity for the given user or repo, if called with no arg, shows the logged in user's feed.",
        'args': {
            'octocat/Hello-World --pager': "str (opt) user or user/repository combo, if blank, shows the logged in user's feed.",
        },
        'opts': {
            '-pr': 'flag (req) also show private events.',
            '--private': 'flag (req) also show private events.',
            '-p': 'flag (req) show results in a pager.',
            '--pager': 'flag (req) show results in a pager.',
        },
    },
    'followers': {
        'desc': 'Lists all followers and the total follower count.',
        'args': {
            'octocat': "str (req) the user's login id, if blank, shows logged in user's info.",
        },
        'opts': {
            '-p': 'flag (opt) show results in a pager.',
            '--pager': 'flag (opt) show results in a pager.',
        },
    },
    'following': {
        'desc': 'Lists all followed users and the total followed count.',
        'args': {
            'octocat': "str (req) the user's login id, if blank, shows logged in user's info.",
        },
        'opts': {
            '-p': 'flag (opt) show results in a pager.',
            '--pager': 'flag (opt) show results in a pager.',
        },
    },
    'gitignore-template': {
        'desc': 'Outputs the gitignore template for the given language.',
        'args': {
            'Python': 'str (req) the language-specific .gitignore.',
        },
        'opts': {},
    },
    'gitignore-templates': {
        'desc': 'Outputs all supported gitignore templates.',
        'args': {},
        'opts': {
            '-p': 'flag (opt) show results in a pager.',
            '--pager': 'flag (opt) show results in a pager.',
        },
    },
    'issue': {
        'desc': 'Outputs detailed information about the given issue.',
        'args': {
            'octocat/Spoon-Knife/1': 'str (req) user/repo/issue_number combo.',
        },
        'opts': {},
    },
    'issues': {
        'desc': 'Lists all issues matching the filter.',
        'args': {},
        'opts': {
            '-f': 'str (opt) "assigned", "created", "mentioned", "subscribed" (default).',
            '--issue_filter': 'str (opt) "assigned", "created", "mentioned", "subscribed" (default).',
            '-s': 'str (opt) "all", "open" (default), "closed".',
            '--issue_state': 'str (opt) "all", "open" (default), "closed".',
            '-l': 'flag (opt) num items to show, defaults to 1000.',
            '--limit': 'flag (opt) num items to show, defaults to 1000.',
            '-p': 'flag (opt) show results in a pager.',
            '--pager': 'flag (opt) show results in a pager.',
        },
    },
    'license': {
        'desc': 'Outputs the license template for the given license.',
        'args': {
            'apache-2.0': 'str (req) the license name.',
        },
        'opts': {},
    },
    'licenses': {
        'desc': 'Outputs all supported license templates.',
        'args': {},
        'opts': {},
    },
    'me': {
        'desc': 'Lists information about the logged in user.',
        'args': {},
        'opts': {
            '-b': 'flag (opt) view profile in a browser instead of the terminal.',
            '--browser': 'flag (opt) view profile in a browser instead of the terminal.',
            '-t': 'see associated -- option for details.',
            '--text_avatar': 'flag (opt) view profile pic in plain text.',
            '-l': 'flag (opt) num items to show, defaults to 1000.',
            '--limit': 'flag (opt) num items to show, defaults to 1000.',
            '-p': 'flag (opt) show results in a pager.',
            '--pager': 'flag (opt) show results in a pager.',
        },
    },
    'notifications': {
        'desc': 'Lists all notifications.',
        'args': {},
        'opts': {
            '-l': 'flag (opt) num items to show, defaults to 1000.',
            '--limit': 'flag (opt) num items to show, defaults to 1000.',
            '-p': 'flag (opt) show results in a pager.',
            '--pager': 'flag (opt) show results in a pager.',
        },
    },
    'octo': {
        'desc': 'Outputs an Easter egg or the given message from Octocat.',
        'args': {
            '"Keep it logically awesome"': 'str (req) a message from Octocat, if empty, Octocat speaks an Easter egg.',
        },
        'opts': {},
    },
    'pull-request': {
        'desc': 'Outputs detailed information about the given pull request.',
        'args': {
            'octocat/Spoon-Knife/3': 'str (req) user/repo/pull_number combo.',
        },