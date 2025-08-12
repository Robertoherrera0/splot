#******************************************************************************
#
#  @(#)RegionZoom.py	3.3  04/28/20 CSS
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

import time

from pyspec.graphics.QVariant import *
from Constants import *
from pyspec.css_logger import log

class RegionBackground(Qwt.QwtPlotItem):

    def __init__(self):
        Qwt.QwtPlotItem.__init__(self)
        self.setZ(100.0)
        self.leftvalue = None
        self.rightvalue = None

    def draw(self, painter, xMap, yMap, rect):
        c = QColor(REGIONBKG_COLOR)
        r = QRect(rect)

        if (self.leftvalue is not None) and (self.rightvalue is not None):
            r.setX(xMap.transform(self.leftvalue) + 1)
            r.setRight(xMap.transform(self.rightvalue))
            painter.fillRect(r, c)

    def setLeft(self, leftvalue):
        self.leftvalue = leftvalue

    def setRight(self, rightvalue):
        self.rightvalue = rightvalue

    def reset(self):
        self.leftvalue = None
        self.rightvalue = None


class RegionZoom(Qwt.QwtPlotPicker):

    def __init__(self, plot):

        self.plot = plot
        self.selecting = False

        Qwt.QwtPlotPicker.__init__(self,
                                   Qwt.QwtPlot.xBottom,
                                   Qwt.QwtPlot.yLeft,
                                   Qwt.Qwt.QwtPicker.PointSelection | Qwt.QwtPicker.DragSelection,
                                   Qwt.QwtPlotPicker.VLineRubberBand,
                                   Qwt.QwtPicker.AlwaysOn,
                                   self.plot.canvas())

        self.moved.connect(self.moveSelection)
        self.selected.connect(self.endSelection)

        self.initRegion()

        self.movingBeyond = False
        self.regbkg = RegionBackground()
        self.regbkg.attach(self.plot)
        self.color = QColor(REGIONLINE_COLOR)

    def setEnabled(self, flag):
        if flag:
            self.setRubberBandPen(QPen(self.color))
            self.setTrackerPen(QPen(self.color))
        else:
            self.initRegion()
        Qwt.QwtPlotPicker.setEnabled(self, flag)

    def moveSelection(self, point):

        if not self.selecting:

            if self.begin:
                self.fullrange = self.plot.getFullRange()
                self.rangex = list(self.plot.getRange())
                self.reselection = True
            else:
                self.reselection = False

            self.selecting = True
            self.regbkg.attach(self.plot)
            self.begin = point.x()
            self.regBeginMarker = Qwt.QwtPlotMarker()
            self.regBeginMarker.attach(self.plot)
            self.regBeginMarker.setLabelAlignment(
                Qt.AlignRight | Qt.AlignTop)
            self.regBeginMarker.setLineStyle(Qwt.QwtPlotMarker.VLine)
            self.regBeginMarker.setLinePen(QPen(self.color, 1))
            self.regBeginMarker.setValue(self.begin, 0.0)
            self.regbkg.setLeft(self.begin)

        self.end = point.x()
        self.regbkg.setRight(self.end)
        self.plot.replot()

        if self.reselection:
            if self.end < self.rangex[0] or self.end > self.rangex[1]:
                self.moveBeyond(True)
            else:
                self.moveBeyond(False)

    def moveBeyond(self, flag):

        if not flag:
            self.movingBeyond = False
            return

        # Calculate stepsize first time we move beyond
        if flag and (not self.movingBeyond):
            self.movingBeyond = 1
            self.beyondLastStep = time.time()
            self.fullsize = self.fullrange[1] - self.fullrange[0]
            self.rangesize = self.rangex[1] - self.rangex[0]
            hidden_part = self.fullsize - self.rangesize
            # lets do the whole hidden range in 4 seconds - 20 steps
            self.stepsize = hidden_part / 30.0

        # Move once every 0.2 seconds
        if self.movingBeyond:
            self.moveRange()

    def moveRange(self):
        if self.end < self.rangex[0]:
            newstart = self.rangex[0] - self.stepsize
            if newstart <= self.fullrange[0]:
                newstart = self.fullrange[0]
            self.rangex[0] = newstart
        elif self.end > self.rangex[1]:
            newend = self.rangex[1] + self.stepsize
            if newend >= self.fullrange[1]:
                newend = self.fullrange[1]
            self.rangex[1] = newend
        self.plot.setRange(self.rangex[0], self.rangex[1])

    def endSelection(self, point):

        if self.begin:
            self.end = point.x()
            self.zoomin()
            self.regBeginMarker.detach()

        self.selecting = False
        self.regbkg.detach()
        self.regbkg.reset()
        self.plot.replot()

    def zoomout(self):
        self.plot.resetRange()

    def zoomin(self):
        if self.begin:
            self.plot.setRange(self.begin, self.end)

    def initRegion(self):
        self.begin = self.end = None

    def widgetKeyPressEvent(self, e):

        if e.key() == Qt.Key_Minus:
            self.zoomout()
        elif e.key() == Qt.Key_Plus:
            self.zoomin()
        elif e.key() == Qt.Key_Escape:
            self.zoomout()
