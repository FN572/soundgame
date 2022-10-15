# -----------------------------------------------------------------------------
# hedit.py
#
# Paring of Fortran H Edit descriptions (Contributed by Pearu Peterson)
#
# These tokens can't be easily tokenized because they are of the following
# form:
#
#   nHc1...cn
#
# where n is a positive integer and c1 ... cn are characters.
#
# This example shows how 