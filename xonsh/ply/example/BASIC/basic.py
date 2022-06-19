# An implementation of Dartmouth BASIC (1964)
#

import sys
sys.path.insert(0, "../..")

if sys.version_info[0] >= 3:
    raw_input = input

import basiclex
import basparse
import basinterp

# If a filename has been specified, we try to run it.
# If a runtime error occurs, we bail out and enter
# interactive mode below
if len(sys.argv) == 2:
    with open(sys.argv[1]) as f:
        data = f.read()
    prog = basparse.parse(data)
    if not prog:
        raise SystemExit
    b = basinterp.BasicInterpreter(prog)
    try:
        b.run()
        raise SystemExit
    except RuntimeError:
        pass

else:
    b = basinterp.BasicInterpreter({})

# Interactive mode.  