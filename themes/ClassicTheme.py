#******************************************************************************
#
#  @(#)ClassicTheme.py	3.1  12/17/16 CSS
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

from SPlotTheme import SPlotTheme

theme_name = "classic"
class Classic(SPlotTheme):

    canvas_background_unknown = "gray"
    canvas_background_static = "#f6f6f6"
    canvas_background_live = "#f0f0ff"
    canvas_background_trend = "white"
    canvas_background_file = "white"

    fit_curve_color = "red"

    axes_color = 'black'

    marker_color_fwhm = "#006600"
    marker_color_com ="#000066"
    marker_color_peak = "#660000"
    marker_color_motor_position = "#666600"

    default_plot_colors = ["#60f060", "#c060c0", "#6060cc",
                      "#c06060", "#9090dd"]

    def __init__(self): 
        super(Classic,self).__init__()

themes = {"classic" : Classic }
