#******************************************************************************
#
#  @(#)SpecPlotQwt.py	3.4  04/28/20 CSS
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

import sys
import time
import os
import math
import copy
import numpy as np

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log
from Constants import *

import Colors

from ScrollZoomer import ScrollZoomer
from CrossHairsQwt import CrossHairs
from RegionZoom import RegionZoom
from SpecPlotAxes import InsideAxis, OutsideScaleDraw, SpecPlotLogScaleEngine

from LegendLabel import LegendLabel
from SpecPlotBaseClass import SpecPlotBaseClass, SpecPlotCurve, SpecPlotMarker
from Preferences import Preferences


class SpecPlotCurveQwt(Qwt.QwtPlotCurve, SpecPlotCurve):

    def __init__(self, mne):

        Qwt.QwtPlotCurve.__init__(self, mne)
        SpecPlotCurve.__init__(self, mne)

        self.setZ(ZLEVEL_CURVE)

    def setColor(self,color):
        if not isinstance(color, QColor): 
            color = QColor(color)

        SpecPlotCurve.setColor(self, color)
        

    def _redraw(self):
        uselines = self.uselines
        usedots = self.usedots
        dotsize = self.dotsize
        linethick = self.linethick
            
        if not usedots and not uselines:
            usedots = True
            dotsize = 3

        if usedots:
            self.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
                                         QBrush(self.color, Qt.SolidPattern),
                                         QPen(self.color),
                                         QSize(dotsize, dotsize)))
        else:
            self.setSymbol(Qwt.QwtSymbol())

        if uselines:
            self.setStyle(Qwt.QwtPlotCurve.Lines)
            self.setPen(QPen(self.color, linethick))
        else:
            self.setStyle(Qwt.QwtPlotCurve.NoCurve)

    def drawFromTo(self, painter, xmap, ymap, frompt, topt):

        if topt < 0:
            topt = self.dataSize() - 1

        if not self.hidden:
            segments = [[frompt, topt]]
        else:
            segments = []

            ptno = frompt
            start = end = None

            while ptno < topt:

                while ptno in self.hidden:
                    ptno += 1
                    continue

                start = ptno

                while (ptno not in self.hidden) and ptno <= topt:
                    ptno += 1
                    continue

                end = ptno - 1

                segments.append([start, end])

        self.drawSegments(painter, xmap, ymap, segments)

    def select(self):
        log.log(3,"Selecting curve %s" % self.mne)
        self.setZ(ZLEVEL_SELECTED)

    def deselect(self):
        log.log(3,"deSelecting curve %s" % self.mne)
        self.setZ(ZLEVEL_CURVE)

    def setData(self, xdata, ydata):
        SpecPlotCurve.setData(self, xdata, ydata)
        Qwt.QwtPlotCurve.setData(self, self._x, self._y)

    def boundingRect(self):
        """Return the bounding rectangle of the data, error bars included.
        """
        # return Qwt.QwtPlotCurve.boundingRect( self )

        if self._x is None or (not self._x.any()):
            return Qwt.QwtPlotCurve.boundingRect(self)
        else:
            xmin = min(self._x)
            xmax = max(self._x)

            if self.showbars and self._dy.any():
                ymin = min(self._y - self._dy)
                ymax = max(self._y + self._dy)
            else:
                ymin = min(self._y)
                ymax = max(self._y)

            return QRectF(xmin, ymin, xmax - xmin, ymax - ymin)

    def drawSegments(self, painter, xmap, ymap, segments):
        lines = []

        for beg, end in segments:
           # prepare lines
            if self.showbars and self._dy.any():
                # draw the bars
                i = beg
                while i < end:
                    xi = xmap.transform(self._x[i])
                    line = QLine(xi, ymap.transform(
                        self._ymin[i]), xi, ymap.transform(self._ymax[i]))
                    lines.append(line)
                    i += 1

            Qwt.QwtPlotCurve.drawFromTo(self, painter, xmap, ymap, beg, end)

        # painter.save()
        painter.setPen(QPen(self.color, self.linethick))
        painter.drawLines(lines)
        # painter.restore()


class SpecPlotGrid(Qwt.QwtPlotGrid):

    def __init__(self):

        Qwt.QwtPlotGrid.__init__(self)

        self.setZ(ZLEVEL_GRID)

        gridPenMaj = QPen()
        gridPenMaj.setStyle(Qt.DashLine)
        gridPenMaj.setColor(Qt.black)
        gridPenMaj.setWidth(1)

        gridPenMin = QPen()
        gridPenMin.setStyle(Qt.DashLine)
        gridPenMin.setColor(Qt.gray)
        gridPenMin.setWidth(1)

        self.setMajPen(gridPenMaj)
        self.setMinPen(gridPenMin)

        self.enableXMin(True)
        self.enableYMin(True)


class SpecPlotMarkerQwt(SpecPlotMarker, Qwt.QwtPlotMarker):

    marker_type = "marker"

    def __init__(self, label, persistent=False, showlabel=True, *args):

        SpecPlotMarker.__init__(self, label, persistent, showlabel)
        Qwt.QwtPlotMarker.__init__(self, *args)

    def setShowOptions(self, color, thickness=3):
        SpecPlotMarker.setShowOptions(self, color, thickness)

        self.pen = QPen()
        self.pen.setColor(QColor(self.color))
        self.pen.setWidth(self.linethick)
        self.setLinePen(self.pen)

    def setXValue(self, x):
        if x is not None:
            SpecPlotMarker.setXValue(self, x)
            Qwt.QwtPlotMarker.setXValue(self, x)

    def setYValue(self, y):
        SpecPlotMarker.setYValue(self, y)
        Qwt.QwtPlotMarker.setYValue(self, y)

    def attach(self, plot):
        Qwt.QwtPlotMarker.attach(self, plot)
        self.status = "attached"

    def draw(self, painter, xmap, ymap, brect):

        if self.showlabel:
            cx, cy = self.getLabelPosition()
            tcx = xmap.transform(cx)
            tcy = ymap.transform(cy)

            psize = 10
            painter.setFont(QFont("Courier", psize))
            left = int(len(self.label) / 2.0) * psize

            painter.setPen(self.pen)
            pnt = QPoint(tcx - left, tcy)
            painter.drawText(pnt, self.label)

        Qwt.QwtPlotMarker.draw(self, painter, xmap, ymap, brect)

    def detach(self):
        self.status = "detached"
        Qwt.QwtPlotMarker.detach(self)


class SpecPlotSegmentQwt(SpecPlotMarkerQwt):

    marker_type = MARKER_SEGMENT

    def __init__(self, label, persistent=False, showlabel=True, *args):

        SpecPlotMarkerQwt.__init__(self, label, persistent, showlabel, *args)

    def setCoordinates(self, coords):
        self.x0, self.y0, self.x1, self.y1 = coords

    def getCoordinates(self):
        return self.x0, self.y0, self.x1, self.y1

    def getXValue(self):
        return (self.x0 + self.x1) / 2.0

    def getYValue(self):
        return (self.y0 + self.y1) / 2.0

    def draw(self, painter, xmap, ymap, brect):
        tx0 = xmap.transform(self.x0)
        tx1 = xmap.transform(self.x1)
        ty0 = ymap.transform(self.y0)
        ty1 = ymap.transform(self.y1)

        painter.setPen(self.pen)
        painter.drawLine(tx0, ty0, tx1, ty1)

        SpecPlotMarkerQwt.draw(self, painter, xmap, ymap, brect)


class SpecPlotTextMarkerQwt(SpecPlotMarkerQwt):
    marker_type = MARKER_TEXT

    def __init__(self, label, persistent=False, showlabel=True, *args):
        SpecPlotMarkerQwt.__init__(self, label, persistent, True, *args)

    def setCoordinates(self, posinfo):
        self.x, self.y = posinfo

    def getCoordinates(self):
        return self.x, self.y


class SpecPlotVerticalMarkerQwt(SpecPlotMarkerQwt):
    """
     A vertical line with a label and a color
    """

    marker_type = MARKER_VERTICAL

    def __init__(self, label, persistent=False, showlabel=True, *args):
        SpecPlotMarkerQwt.__init__(self, label, persistent, showlabel, *args)
        self.setLineStyle(Qwt.QwtPlotMarker.VLine)

    def setCoordinates(self, posinfo):
        self.setXValue(posinfo[0])

    def getCoordinates(self):
        return [self.x, ]

    def setLabelPosition(self, position):
        self.setYValue(position)


class SpecPlotQwt(Qwt.QwtPlot, SpecPlotBaseClass):

    pointSelected = pyqtSignal(str, float)
    regionSelected = pyqtSignal(str, float, float)

    def __init__(self, parent, *args):
        """
           For now this is a Plot with only one X
           and a set of Ys.

           Columns to use as Y can be selected by name 
        """

        SpecPlotBaseClass.__init__(self)
        Qwt.QwtPlot.__init__(self, parent, *args)

        self.inQtLoop = False
        self.colnames = []
        self.name = None
        self.parent = parent

        self.status = DATA_STATIC

        self.markers = {}
        self.segments = {}

        self.grid = None

        self.y2bot = None
        self.y2top = None

        self.fastmotor = None
        self.slowmotor = None

        self.sliceCurves = []
        self.currentSlice = 0

        self.zoomidx = 0

        self.y1axis_position = 0
        self.y2axis_position = 100
        self.bottomaxis_position = 0
        self.topaxis_position = 100

        self.initPlotCanvas()
        self.loadPreferences()
        self.initColorTable()

    def initPlotCanvas(self):
        self.initMarkers()

        self.scaleengine = Qwt.QwtLinearScaleEngine()

        # Create a legend but do not show it.  Show legend in Y axes
        self.hiddenlegend = Qwt.QwtLegend()
        self.hiddenlegend.setParent(self.canvas())
        self.insertLegend(self.hiddenlegend, Qwt.QwtPlot.ExternalLegend)

        self.setAutoReplot(False)
        self.canvas().setPaintAttribute(Qwt.QwtPlotCanvas.PaintCached, True)
        self.canvas().setPaintAttribute(Qwt.QwtPlotCanvas.PaintPacked, True)

        # Create a legend label to show axis
        self.legendY1 = LegendLabel(1, self)
        self.legendY2 = LegendLabel(-1, self)
        self.legendY2.hide()

        self.legendY1.setFont(self.hiddenlegend.font())
        self.legendY2.setFont(self.hiddenlegend.font())

        self.hiddenlegend.hide()

        # Create a grid item
        self.grid = SpecPlotGrid()

        # Create inside tick axes
        self.bottomAxis = InsideAxis(Qwt.QwtPlot.xBottom,  self)
        self.topAxis = InsideAxis(Qwt.QwtPlot.xTop,     self)
        self.y1Axis = InsideAxis(Qwt.QwtPlot.yLeft,    self)
        self.y2Axis = InsideAxis(Qwt.QwtPlot.yRight,   self)

        self.zoomer = ScrollZoomer(
            Qwt.QwtPlot.xBottom, Qwt.QwtPlot.yLeft, self)
        self.zoomer.setAxes(self.y1Axis, self.y2Axis,
                            self.topAxis, self.bottomAxis)

        self.crosshairs = CrossHairs(self)
        self.regionzoom = RegionZoom(self)

        self.setAxisScaleDraw(Qwt.QwtPlot.xBottom,
                              OutsideScaleDraw(Qwt.QwtPlot.xBottom))
        self.setAxisScaleDraw(Qwt.QwtPlot.yLeft,
                              OutsideScaleDraw(Qwt.QwtPlot.yLeft))
        self.setAxisScaleDraw(
            Qwt.QwtPlot.xTop,    OutsideScaleDraw(Qwt.QwtPlot.xTop))
        self.setAxisScaleDraw(Qwt.QwtPlot.yRight,
                              OutsideScaleDraw(Qwt.QwtPlot.yRight))

        self.topAxis.setOnlyBackbone(True)

        self.plotLayout().setSpacing(0)
        self.plotLayout().setCanvasMargin(0, Qwt.QwtPlot.xBottom)
        self.plotLayout().setCanvasMargin(0, Qwt.QwtPlot.yLeft)
        self.plotLayout().setCanvasMargin(0, Qwt.QwtPlot.xTop)
        self.plotLayout().setCanvasMargin(0, Qwt.QwtPlot.yRight)
        self.plotLayout().setAlignCanvasToScales(True)

        self.setCanvasLineWidth(0)
        self.setAutoFillBackground(True)

        #self.setCanvasBackground(self.theme.status_color[BG_COLOR_STATIC])

    def setName(self, name):
        self.name = name

    def setXAxisAuto(self):
        self.setAxisAutoScale(self.zoomer.xAxis())

    def setY1AxisAuto(self):
        self.setAxisAutoScale(Qwt.QwtPlot.yLeft)

    def setY2AxisAuto(self):
        self.setAxisAutoScale(Qwt.QwtPlot.yRight)

    def _setAxisLimits(self, axis, axmin, axmax):
        if axis == X_AXIS:
            ax = self.zoomer.xAxis()
        elif axis == Y1_AXIS:
            ax = Qwt.QwtPlot.yLeft
        elif axis == Y2_AXIS:
            ax = Qwt.QwtPlot.yRight

        self.setAxisScale(ax, axmin, axmax)

    def setAxisLog(self, axis):

        scaledraw = self.axisScaleDraw(axis)
        scaledraw.setLogMode(True)
        scaleEngine = SpecPlotLogScaleEngine(self, axis)
        scaleEngine.setScaleDraw(scaledraw)

        self.setAxisScaleEngine(axis, scaleEngine)
        self.updatePlotData()
        self.queue_replot()

    def setAxisLinear(self, axis):
        scaledraw = self.axisScaleDraw(axis)
        scaledraw.setLogMode(False)
        self.setAxisScaleEngine(axis,  Qwt.QwtLinearScaleEngine())
        self.updatePlotData()

    def setAxisMinMax(self, axis, amin, amax):
        """ called when scale log calculates min and max for the first time"""
        if axis == Qwt.QwtPlot.yLeft or axis == Qwt.QwtPlot.yRight:
            self.bottomAxis.setPosition(amin)
            self.topAxis.setPosition(amax)
        else:
            self.y1Axis.setPosition(amin)
            self.y2Axis.setPosition(amax)

    def _setXLog(self, flag):
        if flag:
            self.setAxisLog(Qwt.QwtPlot.xBottom)
        else:
            self.setAxisLinear(Qwt.QwtPlot.xBottom)
        self.zoomer.setLog(Qwt.QwtPlot.xBottom, flag)

    def _setY1Log(self, flag=True):
        if flag:
            self.setAxisLog(Qwt.QwtPlot.yLeft)
        else:
            self.setAxisLinear(Qwt.QwtPlot.yLeft)

        self.zoomer.setLog(Qwt.QwtPlot.yLeft, flag)

    def _setY2Log(self, flag):
        if flag:
            self.setAxisLog(Qwt.QwtPlot.yRight)
        else:
            self.setAxisLinear(Qwt.QwtPlot.yRight)

    # specifilc because call to setAlignCanvasToScales
    def setRange(self, xbeg, xend):
        if self.datablock:
            self.datablock.setRange(xbeg, xend)
            self.plotLayout().setAlignCanvasToScales(True)
            self.regionSelection(xbeg, xend)

            if self.parent:
                self.parent.updatePlotData()
            else:
                self.updatePlotData()

    # specifilc because call to setAlignCanvasToScales
    def setInterval(self, ptival):

        self.zoomer.resetZoom()

        if self.datablock:
            self.datablock.setInterval(ptival)
            self.plotLayout().setAlignCanvasToScales(True)

            xbeg, xend = self.datablock.getRange()
            self.regionSelection(xbeg, xend)

            if self.parent:
                self.parent.updatePlotData()
            else:
                self.updatePlotData()

    def resetData(self):
        if self.sliceCurves:
            self.clearMeshScan()
        self.clearCurves()

    def bkpoint(self, msg):
        return
        pyqtRemoveInputHook()
        import pdb
        if self.inQtLoop:
            import pdb
            log.log(3,"  - %s" % msg)
            pdb.set_trace()

    def _showCurve(self, colname, axis=Y1_AXIS):
        if axis == Y2_AXIS:
            yaxis = Qwt.QwtPlot.yRight
        else:
            yaxis = Qwt.QwtPlot.yLeft
        self.curves[colname].setYAxis(yaxis)
        self.curves[colname].setVisible(True)
        self.curves[colname].attach(self)

    def _hideCurve(self, colname):
        if colname in self.curves:
            self.curves[colname].detach()
            self.curves[colname].setVisible(False)

    def _usingY1():
        return self.using_y1 

    def _useY1Axis(self, flag=True):
        if flag:
            self.setY1Log(False)
            self.y1Axis.setOnlyBackbone(False)
            self.enableAxis(Qwt.QwtPlot.yLeft, True)
            self.legendY1.show()
        else:
            self.setY1Log(False)
            self.y1Axis.setOnlyBackbone(True)
            self.enableAxis(Qwt.QwtPlot.yLeft, False)
            self.legendY1.hide()
        self.using_y1 = flag

    def _useY2Axis(self, flag=True):
        if flag:
            self.setY2Log(False)
            self.y2Axis.setOnlyBackbone(False)
            self.enableAxis(Qwt.QwtPlot.yRight, True)
            self.legendY2.show()
            if self.zoommode == ZOOM_MODE:
                self.zoomer.setEnabled(True)
        else:
            self.setY2Log(False)
            self.y2Axis.setOnlyBackbone(True)
            self.enableAxis(Qwt.QwtPlot.yRight, False)
            self.legendY2.hide()
        self.using_y2 = flag

    def _usingY2():
        return self.using_y2 

    def redrawAxes(self):

        if self.x:
            xmin, xmax = self.findMinMax([self.x, ])
        else:
            xmin, xmax = 0, self.datablock.getShape()[0]

        # override if full_xrange
        if self.full_xrange:
            if self.x_range_beg is not None and self.x_range_end is not None:
                xmin = self.x_range_beg
                xmax = self.x_range_end

        ymin, ymax = None, None

        if self.y1s:
            y1min, y1max = self.findMinMax(self.y1s)
            ymin, ymax = y1min, y1max

        if self.y2s:
            y2min, y2max = self.findMinMax(self.y2s)
            if not self.y1s:
                ymin, ymax = y2min, y2max
            else:
                if y2min < ymin:
                    ymin = y2min
                if y2max > ymax:
                    ymax = y2max

        if None in [xmin, xmax, ymin, ymax]:
            return

        xmajor = self.axisMaxMajor(Qwt.QwtPlot.xBottom)
        xminor = self.axisMaxMinor(Qwt.QwtPlot.xBottom)

        ymajor = self.axisMaxMajor(Qwt.QwtPlot.yLeft)
        yminor = self.axisMaxMinor(Qwt.QwtPlot.yLeft)

        if xmax == xmin:
            x0 = 0.9 * xmax
            x1 = 1.1 * xmax
        elif not self.xlog:
            xdiv = self.scaleengine.divideScale(xmin, xmax, xmajor, xminor)
            xticks = xdiv.ticks(Qwt.QwtScaleDiv.MajorTick)
            x0 = xticks[0]
            x1 = xticks[-1]
            xstep = (xticks[-1] - xticks[0]) / (len(xticks) - 1)
            if (x0 - xmin) > 0.00001:
                x0 = x0 - xstep
            if (xmax - x1) > 0.00001:
                x1 = x1 + xstep
        else:
            try:
                x0 = pow(10, int(math.log10(xmin)))
                x1 = pow(10, int(math.log10(xmax)))
            except ValueError:  # . in case of 0 or negative
                return

            if (x0 - xmin) > 0.000001:
                x0 = x0 / 10.0
            if (xmax - x1) > 0.000001:
                x1 = x1 * 10

            xscaleengine = self.axisScaleEngine(Qwt.QwtPlot.xBottom)
            xscaleengine.setMinMax(xmin, xmax)

        if ymax == ymin:
            y0 = 0.9 * ymax
            y1 = 1.1 * ymax
        if not self.y1log:
            ydiv = self.scaleengine.divideScale(ymin, ymax, ymajor, yminor)
            yticks = ydiv.ticks(Qwt.QwtScaleDiv.MajorTick)
            if yticks:
                y0 = yticks[0]
                y1 = yticks[-1]

                ystep = (yticks[-1] - yticks[0]) / (len(yticks) - 1)

                if (y0 - ymin) > 0.00001:
                    y0 = y0 - ystep
                if (ymax - y1) > 0.00001:
                    y1 = y1 + ystep
            else:
                y0 = ymin
                y1 = ymax
        else:
            try:
                y0 = pow(10, int(math.log10(ymin)))
                y1 = pow(10, int(math.log10(ymax)))
            except ValueError:  # in case of 0 or negative
                return

            if (y0 - ymin) > 0.000001:
                y0 = y0 / 10.0
            if (ymax - y1) > 0.000001:
                y1 = y1 * 10

        if self.y1log:
            yscaleengine = self.axisScaleEngine(Qwt.QwtPlot.yLeft)
            yscaleengine.setMinMax(y1min, y1max)

        if self.y2log:
            yscaleengine = self.axisScaleEngine(Qwt.QwtPlot.yRight)
            yscaleengine.setMinMax(y2min, y2max)

        self.axes_ok = True

    def getY1ViewRange(self):
        ival = self.axisScaleDiv(Qwt.QwtPlot.yLeft).interval()
        high = ival.maxValue()
        low = ival.minValue()
        return low, high

    def findMinMax(self, cols):

        colmin = None
        colmax = None

        for colname in cols:

            coldat = self.filterLog(
                colname, self.datablock.getDataColumn(colname))

            if coldat.any():
                min = coldat.min()
                max = coldat.max()
            else:
                min = 0
                max = 0

            if colmin is None or min < colmin:
                colmin = min
            if colmax is None or max > colmax:
                colmax = max
        return colmin, colmax

    def _updateTitles(self):
        self.setAxisTitle(Qwt.QwtPlot.xBottom, self.xlabel)
        self.legendY1.setCounters(self.y1s, self.y1title)
        self.legendY2.setCounters(self.y2s, self.y2title)

    def highlightScanPoint(self, pointno):
        xdata = self.datablock.getDataColumn(self.x)
        if not xdata.any():
            return
        self.showValue(self.x, xdata[pointno], "Point", "")
        self.valueXMarker.detach()
        self.valueXMarker.setLabelAlignment(Qt.AlignRight | Qt.AlignTop)
        self.valueXMarker.setLineStyle(Qwt.QwtPlotMarker.VLine)
        pen = QPen()
        pen.setColor(QColor("#9999ff"))
        pen.setWidth(2.0)
        self.valueXMarker.setLinePen(pen)
        self.valueXMarker.setXValue(xdata[pointno])
        self.valueXMarker.setZ(ZLEVEL_MARKER)
        self.valueXMarker.attach(self)

    def showValue(self, colname, atval, what, isval):
        self.valueXMarker.detach()
        self.valueXMarker.setLabelAlignment(Qt.AlignRight | Qt.AlignTop)
        self.valueXMarker.setLineStyle(Qwt.QwtPlotMarker.VLine)
        self.valueXMarker.setXValue(atval)
        self.valueXMarker.setZ(ZLEVEL_MARKER)
        self.valueXMarker.attach(self)
        self.valueLabelMarker.setXValue(atval)

        self.valueLabelMarker.detach()
        if isval:
            self.valueLabelMarker.setLabel(
                Qwt.QwtText("%s: %s" % (what, isval)))
        else:
            self.valueLabelMarker.setLabel(Qwt.QwtText("%s" % what))

        self.valueLabelMarker.setLabelAlignment(Qt.AlignRight | Qt.AlignTop)
        if isval:
            self.valueXMarker.setYValue(isval)

        self.valueLabelMarker.setZ(ZLEVEL_MARKER)
        self.valueLabelMarker.attach(self)

        self.queue_replot()

    def replot(self):

        self._setDataStatus()
        self._position_markers()

        xival = self.axisScaleDiv(Qwt.QwtPlot.xBottom).interval()
        yival = self.axisScaleDiv(Qwt.QwtPlot.yLeft).interval()
        xmin, xmax = xival.minValue(), xival.maxValue()
        ymin, ymax = yival.minValue(), yival.maxValue()
        self.y1Axis.setPosition(xmin)
        self.y2Axis.setPosition(xmax)
        self.bottomAxis.setPosition(ymin)
        self.topAxis.setPosition(ymax)

        Qwt.QwtPlot.replot(self)

    def _setDataStatus(self):
        if self.theme:
            color = self.theme.status_color[self.status]
            self.setCanvasBackground(QColor(color))

    def _showGrid(self):
        self.grid.attach(self)

    def _hideGrid(self):
        self.grid.detach()

    def pointSelection(self, point):
        xpos = point.x()
        xlabel = self.x
        self.pointSelected.emit(xlabel, xpos)

        #for ctname in self.curves:
        #    curve = self.curves[ctname]
        #    xcoord = self.transform(Qwt.QwtPlot.xBottom, point.x())
        #    ycoord = self.transform(Qwt.QwtPlot.yLeft, point.y())
        #    log.log(3,"calculating closest point for %x / %s " % (xcoord, ycoord))
        #    closest = curve.closestPoint(QPoint(xcoord, ycoord))
        #    log.log(3,str(closest))

    def regionSelection(self, xbeg, xend):
        xlabel = self.x
        self.regionSelected.emit(xlabel, xbeg, xend)

    def setBaseY2(self):
        self.setAxisAutoScale(Qwt.QwtPlot.yRight)
        self.replot()
        y2scale = self.axisScaleDiv(Qwt.QwtPlot.yRight)
        self.y2bot = y2scale.interval().minValue()
        self.y2top = y2scale.interval().maxValue()

    def zoomY2(self):

        if not self.y2s:
            self.y2bot = None
            self.y2top = None
            return

        if self.y2bot is None:
            return

        len2 = self.y2top - self.y2bot

        base = self.zoomer.zoomBase()
        b1 = base.top()
        t1 = base.bottom()

        len1 = t1 - b1

        rect = self.zoomer.zoomRect()

        min1 = rect.top()
        max1 = rect.bottom()

        min2 = self.y2bot + (min1 - b1) * len2 / len1
        max2 = self.y2top + (max1 - t1) * len2 / len1

        self.setAxisScale(Qwt.QwtPlot.yRight, float(min2), float(max2))

    def addCurve(self, cntMne):

        # choose color. same for line and symbol
        curve = SpecPlotCurveQwt(cntMne)
        self.curves[cntMne] = curve
        curve.attach(self)
        curve.setVisible(True)

        # line style
        color = QColor(self.colorTable.getColor(cntMne))

        curve.setColor(color)
        curve.showErrorBars(self.showbars)
        curve.setUseLines(self.uselines)
        curve.setLineThickness(self.linethick)
        curve.setUseDots(self.usedots)
        curve.setDotSize(self.dotsize)

        #curve.redraw()

        self.updatePlotData()
        self.setAxisTitles()
        self.queue_replot()

    def redrawCurves(self):
        for cntMne in self.curves:
            self.curves[cntMne].redraw()

        self.setAxisTitles()
        self.queue_replot()

    def addVerticalMarker(self, label, **kwargs):
        return SpecPlotVerticalMarkerQwt(label, **kwargs)

    def addTextMarker(self, label, **kwargs):
        return SpecPlotTextMarkerQwt(label, **kwargs)

    def addSegmentMarker(self, label, **kwargs):
        return SpecPlotSegmentQwt(label, **kwargs)

    def clearCurves(self):
        for colname in (self.y1s + self.y2s):
            curve = self.curves[colname]
            curve.detach()
            curve.setVisible(False)

        self.zoomer.resetZoom()
        self.queue_replot()

    def showNormalCurves(self):
        for colname in (self.y1s + self.y2s):
            if colname in self.curves:
                curve = self.curves[colname]
                curve.attach(self)
                curve.setVisible(True)
        self.queue_replot()

    def setCurrentSlice(self, sliceno):

        ky0 = self.sliceCurves.keys()[0]
        nb_slices = len(self.sliceCurves[ky0])

        if not self.sliceCurves:
            return

        if sliceno < 0:
            sliceno = nb_slices + sliceno

        if sliceno > nb_slices:
            return

        self.currentSlice = sliceno

        for colname in (self.y1s + self.y2s):
            idx = 0
            for curve in self.sliceCurves[colname]:
                if idx == sliceno:
                    curve.setZ(1000)
                    color = QColor(self.colorTable.getColor(colname))
                    symbol = Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
                                           QBrush(color, Qt.SolidPattern),
                                           QPen(color),
                                           QSize(5, 5))
                else:
                    curve.setZ(30)
                    color = QColor("#c0c0c0")
                    symbol = Qwt.QwtSymbol()

                curve.setPen(QPen(color))
                curve.setSymbol(symbol)

            idx += 1

    def _changeCurveColor(self, mne, color):
        mne = str(mne)

        if mne in self.curves.keys():
            self.curves[mne].setColor(QColor(color))

        self.setAxisTitles()
        self.queue_replot()

    def clearMeshScan(self):
        for colname in self.sliceCurves:
            for curve in self.sliceCurves[colname]:
                curve.detach()
                curve.setVisible(False)
        self.sliceCurves = []

    def alignScales(self):
        self.canvas().setFrameStyle(QFrame.Box | QFrame.Plain)
        self.canvas().setLineWidth(1)

        for i in range(Qwt.QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.setSpacing(24)
                scaleDraw.enableComponent(
                    Qwt.QwtAbstractScaleDraw.Backbone, True)

    def printIt(self, title, dest, mode="printer"):

        pfilter = self.getPrintFilter(mode)

        titlefont = QFont("Arial", 12)
        titlefont.setBold(True)
        qtitle = Qwt.QwtText(title)
        qtitle.setFont(titlefont)
        qtitle.setRenderFlags(Qt.AlignLeft | Qt.AlignVCenter)

        self.setTitle(qtitle)

        yleft_title = self.legendY1.getLabel()
        yright_title = self.legendY2.getLabel()

        if yleft_title:
            self.setAxisTitle(Qwt.QwtPlot.yLeft,  yleft_title)
        if yright_title:
            self.setAxisTitle(Qwt.QwtPlot.yRight, yright_title)

        self.print_(dest, pfilter)

        # restore

        self.setTitle("")
        self.setAxisTitle(Qwt.QwtPlot.yLeft, "")
        self.setAxisTitle(Qwt.QwtPlot.yRight, "")

    def getPrintFilter(self, mode):
        ftr = Qwt.QwtPlotPrintFilter
        pfilter = Qwt.QwtPlotPrintFilter()

        if mode == "image":
            pfilter.setOptions(
                ftr.PrintMargin | ftr.PrintTitle & ~ftr.PrintLegend)
        else:
            pfilter.setOptions(ftr.PrintMargin | ftr.PrintTitle &
                               ~ftr.PrintLegend & ~ftr.PrintBackground)

        return pfilter
