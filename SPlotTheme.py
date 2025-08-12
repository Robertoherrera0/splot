#******************************************************************************
#
#  @(#)SPlotTheme.py	3.1  12/17/16 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016
#  by Certified Scientific Software.
#  All rights reserved.
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software ("splot") and associated documentation files (the
#  "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject to
#  the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  Neither the name of the copyright holder nor the names of its contributors
#  may be used to endorse or promote products derived from this software
#  without specific prior written permission.
#
#     * The software is provided "as is", without warranty of any   *
#     * kind, express or implied, including but not limited to the  *
#     * warranties of merchantability, fitness for a particular     *
#     * purpose and noninfringement.  In no event shall the authors *
#     * or copyright holders be liable for any claim, damages or    *
#     * other liability, whether in an action of contract, tort     *
#     * or otherwise, arising from, out of or in connection with    *
#     * the software or the use of other dealings in the software.  *
#
#******************************************************************************

from Constants import *

# Some predefined colors

class SPlotTheme(object):

    axes_color = "red"
    fit_curve_color = "magenta"

    canvas_background_unknown = "white"
    canvas_background_static = "white"
    canvas_background_live = "white"
    canvas_background_trend = "white"
    canvas_background_file = "white"

    marker_color_fwhm = "green"
    marker_color_com = "cyan"
    marker_color_peak = "navy"
    marker_color_motor_position = "rose"

    def __init__(self): 
        self.status_color = {
            DATA_UNKNOWN:  self.canvas_background_unknown,
            DATA_STATIC:  self.canvas_background_static,
            DATA_LIVE:  self.canvas_background_live,
            DATA_TREND:  self.canvas_background_trend,
            DATA_FILE:  self.canvas_background_file,
        }

    def __str__(self): 
        return str(self.__class__)
