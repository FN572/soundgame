
# -*- coding: utf-8 -*-
# Code from https://github.com/hit9/img2txt.git by Chao Wang
import sys
from docopt import docopt


def HTMLColorToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#':
        colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError(
            "input #{0} is not in #RRGGBB format".format(colorstring))
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)


def alpha_blend(src, dst):
    # Does not assume that dst is fully opaque
    # See https://en.wikipedia.org/wiki/Alpha_compositing - section on "Alpha
    # Blending"
    src_multiplier = (src[3] / 255.0)
    dst_multiplier = (dst[3] / 255.0) * (1 - src_multiplier)
    result_alpha = src_multiplier + dst_multiplier
    if result_alpha == 0:       # special case to prevent div by zero below
        return (0, 0, 0, 0)
    else:
        return (
            int(((src[0] * src_multiplier) +
                (dst[0] * dst_multiplier)) / result_alpha),
            int(((src[1] * src_multiplier) +
                (dst[1] * dst_multiplier)) / result_alpha),
            int(((src[2] * src_multiplier) +
                (dst[2] * dst_multiplier)) / result_alpha),
            int(result_alpha * 255)
        )


def getANSIcolor_for_rgb(rgb):
    # Convert to web-safe color since that's what terminals can handle in
    # "256 color mode"
    #   https://en.wikipedia.org/wiki/ANSI_escape_code
    # http://misc.flogisoft.com/bash/tip_colors_and_formatting#bash_tipscolors_and_formatting_ansivt100_control_sequences # noqa
    # http://superuser.com/questions/270214/how-can-i-change-the-colors-of-my-xterm-using-ansi-escape-sequences # noqa
    websafe_r = int(round((rgb[0] / 255.0) * 5))
    websafe_g = int(round((rgb[1] / 255.0) * 5))
    websafe_b = int(round((rgb[2] / 255.0) * 5))
    # Return ANSI coolor
    # https://en.wikipedia.org/wiki/ANSI_escape_code (see 256 color mode
    # section)
    return int(((websafe_r * 36) + (websafe_g * 6) + websafe_b) + 16)


def getANSIfgarray_for_ANSIcolor(ANSIcolor):
    """Return array of color codes to be used in composing an SGR escape
    sequence. Using array form lets us compose multiple color updates without
    putting out additional escapes"""
    # We are using "256 color mode" which is available in xterm but not
    # necessarily all terminals
    # To set FG in 256 color you use a code like ESC[38;5;###m
    return ['38', '5', str(ANSIcolor)]


def getANSIbgarray_for_ANSIcolor(ANSIcolor):
    """Return array of color codes to be used in composing an SGR escape
    sequence. Using array form lets us compose multiple color updates without
    putting out additional escapes"""
    # We are using "256 color mode" which is available in xterm but not
    # necessarily all terminals
    # To set BG in 256 color you use a code like ESC[48;5;###m
    return ['48', '5', str(ANSIcolor)]


def getANSIbgstring_for_ANSIcolor(ANSIcolor):
    # Get the array of color code info, prefix it with ESCAPE code and
    # terminate it with "m"
    return "\x1b[" + ";".join(getANSIbgarray_for_ANSIcolor(ANSIcolor)) + "m"
