#******************************************************************************
#
#  @(#)ScrollZoomer.py	3.3  04/28/20 CSS
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

from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt

from pyspec.css_logger import log
from Constants import *

from ScrollBar import ScrollBar

ATTACHEDTOSCALE, OPPOSITETOSCALE = 0, 1

class ScrollData:

    def __init__(self):
        self.scrollBar = None
        self.position = OPPOSITETOSCALE
        self.mode = Qt.Qt.ScrollBarAsNeeded


class ScrollZoomer(Qwt.QwtPlotZoomer):

    def __init__(self, xaxis, yaxis, plot):

        if not plot:
            return

        self.isEnabled = False
        # We create a zoomer attached only to yLeft

        Qwt.QwtPlotZoomer.__init__(self, Qwt.QwtPlot.xBottom, Qwt.QwtPlot.yLeft,
                                   Qwt.QwtPicker.DragSelection,
                                   Qwt.QwtPicker.ActiveOnly,
                                   plot.canvas())

        self.rubberband_color = Qt.QColor(ZOOM_RUBBERBAND_COLOR)
        self.setRubberBandPen(Qt.QPen(self.rubberband_color))

        self.d_cornerWidget = None
        self.d_hScrollData = ScrollData()
        self.d_vScrollData = ScrollData()
        self.d_inZoom = False
        self.d_alignCanvasToScales = False

    def zoom(self, direction):

        Qwt.QwtPlotZoomer.zoom(self, direction)

        self.y1axes.setPosition(self.zoomRect().left())
        self.y2axes.setPosition(self.zoomRect().right())
        self.x1axes.setPosition(self.zoomRect().bottom())
        self.x2axes.setPosition(self.zoomRect().top())

        self.plot().update()
        self.plot().updateZoomInfo(len(self.zoomStack()), self.zoomRectIndex())

    def setEnabled(self, flag):
        self.isEnabled = flag
        Qwt.QwtPlotZoomer.setEnabled(self, flag)
        self.plot().update()

    def resetZoom(self):
        self.zoom(0)
        Qwt.QwtPlotZoomer.setZoomBase(self, self.zoomBase())
        self.zoom(0)
        self.plot().setAxisLimits()

    def widgetKeyPressEvent(self, e):

        resetzoom = 0

        #Qwt.QwtPlotZoomer.widgetKeyPressEvent(self, e)

        if e.key() == Qt.Qt.Key_Minus:
            self.zoomout()

        if e.key() == Qt.Qt.Key_Plus:
            self.zoomin()

        if e.key() == Qt.Qt.Key_Escape:
            self.resetZoom()

    def zoomin(self):
        self.zoom(1)

    def zoomout(self):
        self.zoom(-1)

    def setZoomBase(self):
        self.plot().setBaseY2()
        Qwt.QwtPlotZoomer.setZoomBase(self)

    def horizontalScrollBar(self):
        return self.d_hScrollData.scrollBar

    def verticalScrollBar(self):
        return self.d_vScrollData.scrollBar

    def setHScrollBarMode(self, mode):
        if self.hScrollBarMode() != mode:
            self.d_hScrollData.mode = mode
            self.updateScrollBars()

    def setVScrollBarMode(self, mode):
        if self.vScrollBarMode() != mode:
            self.d_vScrollData.mode = mode
            self.updateScrollBars()

    def hScrollBarMode(self):
        return self.d_hScrollData.mode

    def vScrollBarMode(self):
        return self.d_vScrollData.mode

    def setHScrollBarPosition(self, position):
        if self.d_hScrollData.position != position:
            self.d_hScrollData.position = position

    def setVScrollBarPosition(self, position):
        if self.d_vScrollData.position != position:
            self.d_vScrollData.position = position
            self.updateScrollBars()

    def hScrollBarPosition(self):
        return self.d_hScrollData.position

    def vScrollBarPosition(self):
        return self.d_vScrollData.position

    def cornerWidget(self):
        return self.d_cornerWidget

    def setCornerWidget(self, widget):
        if widget != self.d_cornerWidget:
            if self.canvas():
                delete(self.d_cornerWidget)
                self.d_cornerWidget = widget
                if self.d_cornerWidget.parent() != canvas():
                    self.d_cornerWidget.setParent(canvas())

                self.updateScrollBars()

    def eventFilter(self, obj, event):

        if obj == self.canvas():
            etype = event.type()

            if etype == Qt.QEvent.Resize:
                fw = self.canvas().frameWidth()

                rect = Qt.QRect()

                rect.setSize(event.size())
                rect.setRect(rect.x() + fw,         rect.y() + fw,
                             rect.width() - 2 * fw, rect.height() - 2 * fw)

                self.layoutScrollBars(rect)

            elif etype == Qt.QEvent.ChildRemoved:
                child = event.child()
                if child == self.d_cornerWidget:
                    self.d_cornerWidget = None
                elif child == self.d_hScrollData.scrollBar:
                    self.d_hScrollData.scrollBar = None
                elif child == self.d_vScrollData.scrollBar:
                    self.d_vScrollData.scrollBar = None

        return Qwt.QwtPlotZoomer.eventFilter(self, obj, event)

    def getZoomLimits(self, axis):
        if axis == Qwt.QwtPlot.yLeft:
            return self.zoomRect().top(), self.zoomRect().bottom()
        elif axis == Qwt.QwtPlot.yRight:
            log.log(3," y2 axis not returning limits yet")
        elif axis == Qwt.QwtPlot.xBottom:
            return self.zoomRect().left(), self.zoomRect().right()

    def setLog(self, axis, flag):
        if axis == Qwt.QwtPlot.yLeft:
            sb = self.d_vScrollData.scrollBar
            if sb:
                sb.setLog(flag)
        elif axis == Qwt.QwtPlot.xBottom:
            sb = self.d_hScrollData.scrollBar
            if sb:
                sb.setLog(flag)

    def rescale(self):

        zoomidx = self.zoomRectIndex()

        if self.isEnabled and zoomidx > 0:
            self.plot().zoomY2()

        xScale = self.plot().axisWidget(self.xAxis())
        yScale = self.plot().axisWidget(self.yAxis())

        if zoomidx <= 0:
            if self.d_inZoom:
                xScale.setMinBorderDist(0, 0)
                yScale.setMinBorderDist(0, 0)

                layout = self.plot().plotLayout()
                layout.setAlignCanvasToScales(self.d_alignCanvasToScales)

                self.d_inZoom = False
        else:
            if not self.d_inZoom:

                # We set a minimum border distance.
                # Otherwise the canvas size changes when scrolling,
                # between situations where the major ticks are at
                # the canvas borders (requiring extra space for the label)
                # and situations where all labels can be painted below/top
                # or left/right of the canvas.

                start, end = xScale.getBorderDistHint()
                xScale.setMinBorderDist(start, end)

                start, end = yScale.getBorderDistHint()
                yScale.setMinBorderDist(start, end)

                layout = self.plot().plotLayout()
                self.d_alignCanvasToScales = layout.alignCanvasToScales()
                layout.setAlignCanvasToScales(False)

                self.d_inZoom = True

        # if not self.plot().axes_ok:

        if zoomidx > 0:
            self.y1axes.setPosition(self.zoomRect().left())
            self.y2axes.setPosition(self.zoomRect().right())
            self.x1axes.setPosition(self.zoomRect().bottom())
            self.x2axes.setPosition(self.zoomRect().top())

        Qwt.QwtPlotZoomer.rescale(self)
        self.updateScrollBars()
        self.plot().queue_replot()

    def scrollBar(self, orientation):

        if orientation == Qt.Qt.Vertical:
            sb = self.d_vScrollData.scrollBar
        else:
            sb = self.d_hScrollData.scrollBar

        if sb == None:
            sb = ScrollBar(orientation, self.canvas())
            sb.hide()
            if orientation == Qt.Qt.Vertical:
                self.d_vScrollData.scrollBar = sb
            else:
                self.d_hScrollData.scrollBar = sb
            sb.sliderMoved.connect(self.scrollIt)

        return sb

    def updateScrollBars(self):

        if not self.canvas():
            return

        xAxis = Qwt.QwtPlotZoomer.xAxis(self)
        yAxis = Qwt.QwtPlotZoomer.yAxis(self)

        xScrollBarAxis = xAxis

        if self.hScrollBarPosition() == OPPOSITETOSCALE:
            xScrollBarAxis = self.oppositeAxis(xScrollBarAxis)

        yScrollBarAxis = yAxis
        if self.vScrollBarPosition() == OPPOSITETOSCALE:
            yScrollBarAxis = self.oppositeAxis(yScrollBarAxis)

        layout = self.plot().plotLayout()

        showHScrollBar = self.needScrollBar(Qt.Qt.Horizontal)

        if showHScrollBar:
            sb = self.scrollBar(Qt.Qt.Horizontal)

            sb.setPalette(self.plot().palette())

            sd = self.plot().axisScaleDiv(xAxis)
            interval = sd.interval()
            lowerBound = interval.minValue()
            upperBound = interval.maxValue()

            sb.setInverted(lowerBound > upperBound)

            sb.setBase(self.zoomBase().left(), self.zoomBase().right())
            sb.moveSlider(self.zoomRect().left(), self.zoomRect().right())

            if not sb.isVisibleTo(self.canvas()):
                sb.show()
                layout.setCanvasMargin(layout.canvasMargin(xScrollBarAxis)
                                       + sb.extent(), xScrollBarAxis)
        else:
            if self.horizontalScrollBar():
                self.horizontalScrollBar().hide()
                layout.setCanvasMargin(layout.canvasMargin(xScrollBarAxis)
                                       - self.horizontalScrollBar().extent(), xScrollBarAxis)

        showVScrollBar = self.needScrollBar(Qt.Qt.Vertical)

        if showVScrollBar:
            sb = self.scrollBar(Qt.Qt.Vertical)

            sb.setPalette(self.plot().palette())

            sd = self.plot().axisScaleDiv(yAxis)

            interval = sd.interval()
            lowerBound = interval.minValue()
            upperBound = interval.maxValue()

            sb.setInverted(lowerBound < upperBound)

            sb.setBase(self.zoomBase().top(), self.zoomBase().bottom())
            sb.moveSlider(self.zoomRect().top(), self.zoomRect().bottom())

            if not sb.isVisibleTo(self.canvas()):
                sb.show()
                layout.setCanvasMargin(layout.canvasMargin(yScrollBarAxis)
                                       + sb.extent(), yScrollBarAxis)
        else:
            if self.verticalScrollBar():
                self.verticalScrollBar().hide()
                layout.setCanvasMargin(layout.canvasMargin(yScrollBarAxis)
                                       - self.verticalScrollBar().extent(), yScrollBarAxis)

        if showHScrollBar and showVScrollBar:
            if self.d_cornerWidget == None:
                self.d_cornerWidget = Qt.QWidget(self.canvas())
                self.d_cornerWidget.setAutoFillBackground(True)
                self.d_cornerWidget.setPalette(self.plot().palette())
            self.d_cornerWidget.show()
        else:
            if self.d_cornerWidget:
                self.d_cornerWidget.hide()

        self.layoutScrollBars(self.canvas().contentsRect())
        self.plot().updateLayout()

    def setAxes(self, y1axes, y2axes, x1axes, x2axes):
        self.y1axes = y1axes
        self.y2axes = y2axes
        self.x1axes = x1axes
        self.x2axes = x2axes

    def scrollbarSizes(self):

        hScrollBar = self.horizontalScrollBar()
        vScrollBar = self.verticalScrollBar()

        hsize = 0
        vsize = 0

        if hScrollBar and hScrollBar.isVisible():
            hsize = hScrollBar.extent()
        if vScrollBar and vScrollBar.isVisible():
            vsize = hScrollBar.extent()

        return (hsize, vsize)

    def layoutScrollBars(self, rect):

        hPos = self.xAxis()

        if self.hScrollBarPosition() == OPPOSITETOSCALE:
            hPos = self.oppositeAxis(hPos)

        vPos = self.yAxis()
        if self.vScrollBarPosition() == OPPOSITETOSCALE:
            vPos = self.oppositeAxis(vPos)

        hScrollBar = self.horizontalScrollBar()
        vScrollBar = self.verticalScrollBar()

        hdim = vdim = 0

        if hScrollBar:
            hext = hScrollBar.extent()
            if hext:
                hdim = hext

        if vScrollBar:
            vext = vScrollBar.extent()
            if vext:
                vdim = vext

        if hScrollBar and hScrollBar.isVisible():

            x = rect.x()
            if hPos == Qwt.QwtPlot.xTop:
                y = rect.top()
            else:
                y = rect.bottom() - hdim + 1

            w = rect.width()

            if vScrollBar and vScrollBar.isVisible():
                if vPos == Qwt.QwtPlot.yLeft:
                    x += vdim
                w -= vdim

            hScrollBar.setGeometry(x, y, w, hdim)

        if vScrollBar and vScrollBar.isVisible():

            pos = self.yAxis()
            if self.vScrollBarPosition() == OPPOSITETOSCALE:
                pos = self.oppositeAxis(pos)

            if vPos == Qwt.QwtPlot.yLeft:
                x = rect.left()
            else:
                x = rect.right() - vdim + 1
            y = rect.y()

            h = rect.height()

            if hScrollBar and hScrollBar.isVisible():
                if hPos == Qwt.QwtPlot.xTop:
                    y += hdim

                h -= hdim

            vScrollBar.setGeometry(x, y, vdim, h)

        if hScrollBar and hScrollBar.isVisible() and vScrollBar and vScrollBar.isVisible():
            if self.d_cornerWidget:
                cornerRect = Qt.QRect(
                    vScrollBar.pos().x(), hScrollBar.pos().y(), vdim, hdim)
                self.d_cornerWidget.setGeometry(cornerRect)

    def scrollIt(self, orientation, min, max):

        if orientation == Qt.Qt.Horizontal:
            x = min
            y = self.zoomRect().top()
        else:
            x = self.zoomRect().left()
            y = min

        ymin = self.zoomRect().bottom()
        ymax = self.zoomRect().top()

        Qwt.QwtPlotZoomer.move(self, x, y)
        self.plot().update()
        self.move(x, y)

    def needScrollBar(self, o):
        if o == Qt.Qt.Horizontal:
            mode = self.d_hScrollData.mode
            baseMin = self.zoomBase().left()
            baseMax = self.zoomBase().right()
            zoomMin = self.zoomRect().left()
            zoomMax = self.zoomRect().right()
        else:
            mode = self.d_vScrollData.mode
            baseMin = self.zoomBase().top()
            baseMax = self.zoomBase().bottom()
            zoomMin = self.zoomRect().top()
            zoomMax = self.zoomRect().bottom()

        needed = False

        if mode == Qt.Qt.ScrollBarAlwaysOn:
            needed = True
        elif mode == Qt.Qt.ScrollBarAlwaysOff:
            needed = False
        else:
            if (baseMin < zoomMin) or (baseMax > zoomMax):
                needed = True

        return needed

    def oppositeAxis(self, axis):
        if axis == Qwt.QwtPlot.xBottom:
            return Qwt.QwtPlot.xTop
        elif axis == Qwt.QwtPlot.xTop:
            return Qwt.QwtPlot.xBottom
        elif axis == Qwt.QwtPlot.yLeft:
            return Qwt.QwtPlot.yRight
        elif axis == Qwt.QwtPlot.yRight:
            return Qwt.QwtPlot.yLeft
        else:
            return axis
