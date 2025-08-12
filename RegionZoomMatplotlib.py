#******************************************************************************
#
#  @(#)RegionZoomMatplotlib.py	3.3  04/28/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2020
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
from pyspec.css_logger import log

class RegionZoom(object):

    def __init__(self, plot):
        self.plot_ref = plot
        self.enabled = False
        self.selecting = False

    def setEnabled(self, flag):
        self.enabled = flag

    def begin(self,event):
        canvas = self.plot_ref().canvas
        x, y = canvas.pixelsToXY(event.x, event.y)
        self.begin_x = self.end_x = x
        self.bkg = canvas.y1axes.axvspan(x,x,edgecolor=REGIONLINE_COLOR,facecolor=REGIONBKG_COLOR, alpha=0.5)
        self.selecting = True

    def mouse_move(self,event):
        if self.selecting:
            x, y = self.plot_ref().canvas.pixelsToXY(event.x, event.y)
            self.end_x = x
            pol_coord = [
                [self.begin_x, 0.0],
                [self.begin_x, 1.0],
                [self.end_x, 1.0],
                [self.end_x, 0.0],
            ]
            self.bkg.set_xy(pol_coord)

    def end(self,event):
        if self.selecting:
            self.bkg.remove()
            self.bkg = None
            self.selecting = False
            self.zoomin()

    def isSelecting(self):
        return self.selecting

    def zoomout(self):
        self.plot_ref().resetRange()

    def zoomin(self):
        if self.begin:
            self.plot_ref().setRange(self.begin_x, self.end_x)

    def zoomout(self):
        self.plot_ref().resetRange()


