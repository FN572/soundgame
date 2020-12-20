Release Checklist
=================

A. Install in a new venv and run unit tests

Note, you can't seem to script the virtualenv calls, see:
https://bitbucket.org/dhellmann/virtualenvwrapper/issues/219/cant-deactivate-active-virtualenv-from

    $ deactivate
    $ rmvirtualenv gitsome
    $ mkvirtualenv gitsome
    $ pip install -e .
    $ pip install -r requirements-dev.txt
    $ rm -rf .tox && tox

B. Run code checks

    $ scripts/run_code_checks.sh

C. Run manual [smoke tests](#smoke-tests) on Mac, Ubuntu, Windows

D. Update and review `README.rst` and `Sphinx` docs, then check gitsome/docs/build/html/index.html

    $ scripts/update_docs.sh

E. Push changes

F. Review Travis, Codecov, and Gemnasium

G. Start a new release branch

    $ git flow release start x.y.z

H. Increment the version number in `gitsome/__init__.py`

I. Update and 