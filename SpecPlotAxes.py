#******************************************************************************
#
#  @(#)SpecPlotAxes.py	3.4  04/28/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2020
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

import math
import themes

from pyspec.css_logger import log

from PyQt4 import Qwt5 as Qwt
from PyQt4.Qt import QColor

from Preferences import Preferences
import Colors

class InsideScaleDraw(Qwt.QwtScaleDraw):

    def __init__(self, alignment):
        Qwt.QwtScaleDraw.__init__(self)
        self.setAlignment(alignment)
        self.setSpacing(-4)
        self._onlybackbone = False

        prefs = Preferences() 
        theme = themes.get_theme( prefs["theme"] )
        if theme is not None:
            self.axes_color = QColor( theme.axes_color )

    def drawLabel(self, painter, value):
        pass

    def drawTick(self, painter, value, length):
        painter.setPen(self.axes_color)
        if not self._onlybackbone:
            Qwt.QwtScaleDraw.drawTick(self, painter, value, length)

    def drawBackbone(self, painter):
        painter.setPen(self.axes_color)
        Qwt.QwtScaleDraw.drawBackbone(self, painter)

    def setOnlyBackbone(self, flag):
        self._onlybackbone = flag


class OutsideScaleDraw(Qwt.QwtScaleDraw):

    def __init__(self, axis, *args):
        Qwt.QwtScaleDraw.__init__(self, *args)
        self.axis = axis
        self._ExtraLabelsToDraw = []
        self.setSpacing(-10)
        self.logMode = False

    def setLogMode(self, flag):
        self.logMode = flag

    def draw(self, painter, palette):
        if self.logMode and self._ExtraLabelsToDraw:
            self.drawExtraLabels(painter, palette)
        Qwt.QwtScaleDraw.draw(self, painter, palette)

    def drawExtraLabels(self, painter, palette):
        font = painter.font()
        pointsize = font.pointSize()
        newsize = pointsize - 2

        font.setPointSize(newsize)
        painter.setFont(font)

        for label in self._ExtraLabelsToDraw:
            self.drawLabel(painter, label)

        font.setPointSize(pointsize)
        painter.setFont(font)

    def setExtraToDraw(self, ticks):
        self._ExtraLabelsToDraw = ticks

    def drawTick(self, painter, value, length):
        pass

    def drawLabel(self, painter, value):
        Qwt.QwtScaleDraw.drawLabel(self, painter, value)

    def drawBackbone(self, painter):
        pass


class SpecPlotLogScaleEngine(Qwt.QwtLog10ScaleEngine):

    def __init__(self, plot, axis):
        Qwt.QwtLog10ScaleEngine.__init__(self)
        self.plot = plot
        self.axis = axis
        self.first = True

        # some default
        self.minval = 0.001
        self.maxval = 10
        self.minlog = int(math.log10(self.minval))
        self.maxlog = int(math.log10(self.maxval))

        self.majticks = []  # major
        self.medticks = []  # extra labels
        self.minticks = []  # minor ticks

        self.min2show = 0
        self.max2show = 100

    def setScaleDraw(self, scaleDraw):
        self._scaleDraw = scaleDraw

    def setMinMax(self, minval, maxval):

        self.minval = minval
        self.maxval = maxval

        # we have to do clever calculation here to leave space between min and
        # max, but not too much

        minlog = math.log10(self.minval)
        maxlog = math.log10(self.maxval)

        if maxlog != int(maxlog):
            maxlog += 1

        # min and max log values to hold the whole range
        self.minlog = int(minlog)
        self.maxlog = int(maxlog)

        self.calculateTicks()

        # find the first values to cover the range.
        # If they happen to be medticks, use then as limits to show and make
        # then become majtick
        if self.medticks:

            stickidx = None
            btickidx = None

            for tickidx in range(len(self.medticks)):
                tick = self.medticks[tickidx]
                if tick < self.minval:
                    stickidx = tickidx
                if tick > self.maxval:
                    btickidx = tickidx
                    break

            if stickidx is not None:
                self.min2show = self.medticks[stickidx]
                self.majticks[0] = self.min2show
            else:
                self.min2show = self.majticks[0]
                stickidx = -1

            if btickidx is not None:
                self.max2show = self.medticks[btickidx]
                self.majticks[-1] = self.max2show
            else:
                self.max2show = self.majticks[-1]
                btickidx = len(self.medticks)

            self.medticks = self.medticks[stickidx + 1:btickidx]
        else:
            self.min2show = self.minval
            self.max2show = self.maxval

        # actual ranges to show
        # if self.maxlog > (self.minlog+1):
        #   # if extends over two or more decades, just adjust range limits by a little margin
        #   self.min2show = self.minval * 0.9
        #   self.max2show = self.maxval * 1.1
        # else:
        #   # if all range in same decade set min and max to show to actual values

    def getMinMax(self):
        return self.min2show, self.max2show

    def autoScale(self, maxSteps):
        # it does not matter. The real value is the one returned by divideScale
        return (math.pow(10, self.minlog), math.pow(10, self.maxlog), 1)
        # return (self.min2show, self.max2show, 1)

    def calculateTicks(self):

        self.majticks = []  # major
        self.medticks = []  # extra labels
        self.minticks = []  # minor ticks

        # First calculate to hold the range in exact decades
        for i in range(self.minlog, self.maxlog + 1):
            self.majticks.append(pow(10, i))

        nb_majors = len(self.majticks)

        if nb_majors <= 2:
            for i in range(nb_majors - 1):
                majval = self.majticks[i]
                for j in range(2, 10):  # the first one is already a major
                    self.medticks.append(majval * j)
                for j in range(2, 10):
                    self.minticks.append(majval * j)

        elif nb_majors <= 4:  # at 2 and 5
            for i in range(nb_majors - 1):
                majval = self.majticks[i]
                self.medticks.append(majval * 2)
                self.medticks.append(majval * 5)
        elif nb_majors < 6:  # medium ticks at 5
            for i in range(nb_majors - 1):
                majval = self.majticks[i]
                self.medticks.append(majval * 5)
        else:  # show only majors
            pass

    def divideScale(self, x1, x2, numMajorSteps, numMinorSteps, stepSize=0.0):

        notick_shown = False
        majticks = self.majticks

        is_zoomed = self.plot.isZoomed()

        if self.plot.isZoomed():
            zmin, zmax = self.plot.getZoomLimits(self.axis)
            x1, x2 = zmin, zmax
        else:
            x1, x2 = self.min2show, self.max2show

        medticks = []
        for val in self.medticks:
            if val >= x1 and val <= x2:
                medticks.append(val)

        majticks = []
        for val in self.majticks:
            if val >= x1 and val <= x2:
                majticks.append(val)

        # if no major ticks. use medium ticks
        if not majticks:
            if medticks:
                majticks = medticks
                medticks = []

        # if still no enough ticks. set at least three. the visible limits plus
        # other one
        if len(majticks) < 3:
            if x1 not in majticks:
                majticks.append(x1)
            if x2 not in majticks:
                majticks.append(x2)
            if (len(majticks) + len(medticks)) == 2:
                step = (x2 - x1) / 2.0
                majticks.append(x1 + step)
            majticks.sort()

        if self._scaleDraw:
            pass
            # if notick_shown:
            # put something on the screen !
            #log.log(3, "setting something to draw %s" % str(majticks))
            # else:
            #log.log(3,"divide scale calculates min/max to %s / %s" % (x1, x2))

            self._scaleDraw.setExtraToDraw(medticks)

        ival = Qwt.QwtDoubleInterval(x1, x2)
        #log.log(3, "self axis %s / x1 = %s / x2 = %s" % (self.axis, x1, x2))
        if self.first:
            self.plot.setAxisMinMax(self.axis, x1, x2)
            #self.first = False

        return Qwt.QwtScaleDiv(ival, self.minticks, medticks, majticks)


class InsideAxis(Qwt.QwtPlotScaleItem):

    def __init__(self, axis, plot):

        self.plot = plot
        self.axis = axis
        self.pos = 0

        if axis == Qwt.QwtPlot.xBottom:
            alignment = Qwt.QwtScaleDraw.TopScale
        elif axis == Qwt.QwtPlot.xTop:
            alignment = Qwt.QwtScaleDraw.BottomScale
        elif axis == Qwt.QwtPlot.yLeft:
            alignment = Qwt.QwtScaleDraw.RightScale
        elif axis == Qwt.QwtPlot.yRight:
            alignment = Qwt.QwtScaleDraw.LeftScale

        Qwt.QwtPlotScaleItem.__init__(self, alignment, 0.0)
        self.setScaleDraw(InsideScaleDraw(alignment))

        if axis == Qwt.QwtPlot.yLeft or axis == Qwt.QwtPlot.yRight:
            self.setYAxis(axis)

        if axis == Qwt.QwtPlot.xBottom or axis == Qwt.QwtPlot.xTop:
            self.setXAxis(axis)

        self.setScaleDivFromAxis(True)

        self.setFont(self.plot.axisWidget(Qwt.QwtPlot.xBottom).font())
        self.setZ(10000)
        self.attach(self.plot)

    def setPosition(self, pos):
        self.pos = pos
        self.redraw()

    def redraw(self):
        Qwt.QwtPlotScaleItem.setPosition(self, self.pos)

    def followAxis(self, axis):

        if self.axis != Qwt.QwtPlot.yRight:
            return

        if not axis:
            self.setScaleDivFromAxis(True)
        else:
            self.setScaleDiv(axis.scaleDiv())

    def setOnlyBackbone(self, flag):
        self.scaleDraw().setOnlyBackbone(flag)
