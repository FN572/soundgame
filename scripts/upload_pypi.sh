#!/usr/bin/env bash

# N. Set CHANGELOG as `README.md`
scripts/set_changelog_as_readme.sh
# O. Register package with PyPi
python setup.py register -r pyp