# An implementation of Dartmouth BASIC (1964)
#

import sys
sys.path.insert(0, "../..")

if sys.version_info[0] >= 3:
    raw_input = input

import logging
logging.basicConfig(
    level=logging.INFO,
    filename="parselog.txt",
    filemode="w"
)
log = logging.getLogger()

import basiclex
import basparse
import basinterp

# If a filename has been sp