#******************************************************************************
#
#  @(#)SpecTheme.py	3.1  12/17/16 CSS
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

theme_name = "spec"  # keep autoload

class GansTheme(SPlotTheme):
    # Canvases: near‑white; live gets a cool mint‑gray tint
    canvas_background_unknown = "#F9FAFB"
    canvas_background_static  = "#F9FAFB"
    canvas_background_live    = "#EEF3F2"   # mint‑gray (subtle, not green)
    canvas_background_trend   = "#F8F9FA"
    canvas_background_file    = "#F9F9F8"

    # Axes/fit: strong contrast on light backgrounds
    axes_color = "#1F2328"
    fit_curve_color = "#0B3C5D"             # deep steel‑navy

    # Markers: readable on both white and mint‑gray
    marker_color_peak = "#C62828"           # red (peak)
    marker_color_com  = "#0B5FA4"           # blue (COM)
    marker_color_fwhm = "#2E7D32"           # green (FWHM)
    marker_color_motor_position = "#B07D0D" # muted amber

    # Series palette: high contrast, not neon
    default_plot_colors = [
        "#0B5FA4",  # blue
        "#C62828",  # red
        "#2E7D32",  # green
        "#6A1B9A",  # violet
        "#00838F",  # teal
        "#B85C38",  # rust
        "#455A64",  # blue‑gray
    ]

    def __init__(self):
        super(GansTheme, self).__init__()

themes = {"spec": GansTheme}
