#******************************************************************************
#
#  @(#)CrossHairsMatplotlib.py	3.4  10/30/20 CSS
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

import matplotlib.pyplot as plt

import numpy as np

from Constants import *
from pyspec.css_logger import log

class CrossHairs(object):

    def __init__(self, canvas):
        self.canvas_ref = canvas

        self.lx = self.ly = self.txt = None
        self.x = 0.0
        self.y = 0.0
        self.info = ""
        self.xcen = None
        self.ycen = None

        self.enabled = False  # whether the crosshair is enabled
        self.inaxes = False # whether mouse is in axes
        self.showing = False # whether the crosshair is being shown

    def setEnabled(self, flag):
        self.enabled = flag
        self.update()

    def update(self):
        if self.enabled and self.inaxes:
            if not self.showing:
                self.show()
        else:
            self.hide()

    def show(self):
        if not self.lx:
            self.init_cross()
        else:
            self.lx.set_visible(True)
            self.ly.set_visible(True)
            self.txt.set_visible(True)

        self.showing = True

    def hide(self):

        self.showing = False

        if self.lx:
            self.lx.set_visible(False)
            self.ly.set_visible(False)
            self.txt.set_visible(False)

    def refresh(self, x, y):
        self.xcen, self.ycen = self.canvas_ref().getCenter()
        self.x, self.y = self.canvas_ref().pixelsToXY(x,y)

        self.x_refresh()
        self.y_refresh()
        self.txt_refresh()

    def init_cross(self):
        ax = self.canvas_ref().y1axes
        self.lx = ax.axhline(self.y, color=CROSSHAIRS_COLOR)  # the horiz line
        self.ly = ax.axvline(self.x, color=CROSSHAIRS_COLOR)  # the vert line
        self.txt = ax.text(self.x, self.y, self.info, ha="right",
                           color=CROSSHAIRS_COLOR, transform=ax.transData)
        return self.lx, self.ly, self.txt

    def x_refresh(self):
        self.lx.set_ydata(self.y)

    def y_refresh(self):
        self.ly.set_xdata(self.x)

    def txt_refresh(self):

        if self.y < self.ycen:
            self.txt.set_va("bottom")
        else:
            self.txt.set_va("top")

        if self.x < self.xcen:
            self.txt.set_ha("left")
        else:
            self.txt.set_ha("right")

        self.info = "x=%1.2f, y=%1.2f" % (self.x, self.y)
        self.txt.set_text(self.info)
        self.txt.set_x(self.x)
        self.txt.set_y(self.y)

        return self.txt

    def mouse_move(self, event):
        self.inaxes = event.inaxes
        self.event = event

        self.update()

        if self.showing:
            self.refresh(event.x, event.y)

class SnaptoCursor(object):
    """
    Like Cursor but the crosshair snaps to the nearest x,y point
    For simplicity, I'm assuming x is sorted
    """

    def __init__(self, ax, x, y):
        self.ax = ax
        self.lx = ax.axhline(color='k')  # the horiz line
        self.ly = ax.axvline(color='k')  # the vert line
        self.x = x
        self.y = y
        # text location in axes coords
        self.txt = ax.text(0.7, 0.9, '', transform=ax.transAxes)

    def mouse_move(self, event):

        if not event.inaxes:
            return

        x, y = event.xdata, event.ydata

        indx = np.searchsorted(self.x, [x])[0]
        x = self.x[indx]
        y = self.y[indx]
        # update the line positions
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)
        self.lx.draw(self.ax)
        self.ly.draw(self.ax)

        self.txt.set_text('x=%1.2f, y=%1.2f' % (x, y))
        print('x=%1.2f, y=%1.2f' % (x, y))
        plt.draw()


def main():
    t = np.arange(0.0, 1.0, 0.01)
    s = np.sin(2 * 2 * np.pi * t)
    fig, ax = plt.subplots()

    #cursor = CrossHairs(ax)
    # cursor.setEnabled(True)
    cursor = SnaptoCursor(ax, t, s)
    plt.connect('motion_notify_event', cursor.mouse_move)

    ax.plot(t, s, 'o')
    plt.axis([0, 1, -1, 1])
    plt.show()

if __name__ == '__main__':
    main()
