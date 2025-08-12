#******************************************************************************
#
#  @(#)ScrollZoomerMatplotlib.py	3.4  10/30/20 CSS
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

from pyspec.graphics.QVariant import *
from Constants import *
from pyspec.css_logger import log
from ScrollBar import ScrollBar

import matplotlib.patches as patches

class ScrollZoomer(object):

    def __init__(self, plot):
        self.plot_ref = plot

        self.initialized = False

        self.enabled = False
        self.selecting = False
        self.last_rect = None

        self.levels = []
        self.current_level = 0

        self.x_beg0 = self.x_end0 = None
        self.y1_beg0 = self.y1_end0 = None
        self.y2_beg0 = self.y2_end0 = None

    def setEnabled(self, flag):
        self.enabled = flag

    def begin(self,event):
        if event.inaxes: 
            self.selecting = True
            canvas = self.plot_ref().canvas
            self.x_beg, self.y1_beg = canvas.pixelsToXY(event.x, event.y)
            if self.last_rect:
                self.last_rect.remove()
                self.last_rect = None

    def mouse_move(self,event):
        if self.selecting:
            canvas = self.plot_ref().canvas
            self.x_end, self.y1_end = canvas.pixelsToXY(event.x, event.y)

            width = self.x_end - self.x_beg
            height = self.y1_end - self.y1_beg

            if self.last_rect:
                self.last_rect.remove()
            self.last_rect = canvas.y1axes.add_patch(patches.Rectangle( (self.x_beg, self.y1_beg), width, height, color=ZOOM_RUBBERBAND_COLOR, fill=False) )

    def end(self,event):
        if self.selecting:
            if self.last_rect:
                self.last_rect.remove()
                self.last_rect = None
            self.add_zoomlevel()
            self.selecting = False

    def isInitialized(self):
        return self.initialized

    def isSelecting(self):
        return self.selecting

    def add_zoomlevel(self):
        if self.x_beg > self.x_end:
            self.x_beg,self.x_end = self.x_end,self.x_beg

        if self.y1_beg > self.y1_end:
            self.y1_beg,self.y1_end = self.y1_end,self.y1_beg

        self.y2_beg = self.convertY2(self.y1_beg)
        self.y2_end = self.convertY2(self.y1_end)

        self.levels = self.levels[:self.current_level+1] + \
                  [[(self.x_beg, self.x_end), (self.y1_beg, self.y1_end), (self.y2_beg, self.y2_end)],]
        
        self.zoomin()

    def convertY2(self, y):

        spread1 = self.y1_end0-self.y1_beg0  
        spread2 = self.y2_end0-self.y2_beg0

        offset1 = y - self.y1_beg0
        offset2 = offset1 * spread2 / spread1

        y2 = self.y2_beg0 + offset2
        return y2
       
    def setZoomBase(self):

        canvas = self.plot_ref().canvas

        self.x_beg0, self.x_end0 = canvas.y1axes.get_xlim()
        self.y1_beg0, self.y1_end0 = canvas.y1axes.get_ylim()
        self.y2_beg0, self.y2_end0 = canvas.y2axes.get_ylim()

        self.initZoom()

    def initZoom(self):

        levels = [[(self.x_beg0, self.x_end0),(self.y1_beg0, self.y1_end0), (self.y2_beg0, self.y2_end0)]]

        self.current_level = 0

        if levels != self.levels:
            self.levels = levels
            self.resetZoom()

    def resetZoom(self):
        self.initZoom()
        self.rescale()
        self.plot_ref().updateZoomInfo(len(self.levels), self.current_level)

    def isZoomed(self):
        return len(self.levels) > 1 

    def zoomin(self):
        self.zoom(1)

    def zoomout(self):
        self.zoom(-1)

    def zoom(self,direction):
        if direction > 0 and self.current_level < (len(self.levels)):
            self.current_level += 1
        elif direction < 0 and self.current_level > 0: 
            self.current_level -= 1

        self.rescale()
        self.plot_ref().updateZoomInfo(len(self.levels), self.current_level)

    def scrollIt(self,orientation, minval, maxval):

        canvas = self.plot_ref().canvas
        self.rect = self.levels[self.current_level]

        if orientation == Qt.Horizontal:
            self.rect[0] = (minval,maxval)
        else:
            self.rect[1] = (minval,maxval)
            self.rect[2] = (self.convertY2(minval),self.convertY2(maxval))
        self.plot_ref().replot()

    def rescale(self):

        self.rect = self.levels[self.current_level]
        
        canvas = self.plot_ref().canvas

        canvas.y1axes.set_xlim(self.rect[0])
        canvas.y1axes.set_ylim(self.rect[1])
        canvas.y2axes.set_ylim(self.rect[2])

        self.updateScrollBars()

    def updateScrollBars(self):

        showHScrollBar = self.needScrollBar(Qt.Horizontal)
        showVScrollBar = self.needScrollBar(Qt.Vertical)

        horiz_sb = self.plot_ref().horizontalScrollBar()
        vert_sb = self.plot_ref().verticalScrollBar()

        rect = self.levels[self.current_level]

        canvas = self.plot_ref().canvas

        if showHScrollBar or showVScrollBar:

            dpi = canvas.fig.dpi

            canvas_bbox = canvas.fig.get_window_extent().transformed(
                                  canvas.fig.dpi_scale_trans.inverted())
            y1axes_bbox = canvas.y1axes.get_window_extent().transformed(
                                  canvas.fig.dpi_scale_trans.inverted())

            cxwid, cxhei = canvas_bbox.width*dpi, canvas_bbox.height*dpi
            x0pos, x1pos, y0pos,y1pos = y1axes_bbox.x0*dpi, y1axes_bbox.x1*dpi, \
                                  y1axes_bbox.y0*dpi, y1axes_bbox.y1*dpi

            horiz_pos0 = x0pos - 5
            horiz_pos1 = cxwid - x1pos - 5

            vert_pos0 = y0pos 
            vert_pos1 = cxhei - y1pos 

        if showHScrollBar:

            zoomMin, zoomMax = rect[0]

            horiz_sb.setBase(self.x_beg0, self.x_end0)
            horiz_sb.moveSlider(zoomMin, zoomMax)

            horiz_sb.setPosition(horiz_pos0, horiz_pos1)

            canvas.fig.subplots_adjust(top=1.0)

            if not horiz_sb.isVisibleTo(self.plot_ref()):
                horiz_sb.show()
        else:
            canvas.fig.subplots_adjust(top=0.9)
            horiz_sb.hide()
 
        if showVScrollBar:
            zoomMin, zoomMax = rect[1]

            vert_sb.setBase(self.y1_beg0, self.y1_end0)
            vert_sb.moveSlider(zoomMin, zoomMax)

            vert_sb.setPosition(vert_pos0, vert_pos1)

            if not vert_sb.isVisibleTo(self.plot_ref()):
                vert_sb.show()
        else:
            vert_sb.hide()

    def needScrollBar(self, o):

        rect = self.levels[self.current_level]

        if o == Qt.Horizontal:
            baseMin = self.x_beg0
            baseMax = self.x_end0
            zoomMin, zoomMax = rect[0]
        else:
            baseMin = self.y1_beg0
            baseMax = self.y1_end0
            zoomMin, zoomMax = rect[1]

        needed = False

        if (baseMin < zoomMin) or (baseMax > zoomMax):
            needed = True

        return needed

