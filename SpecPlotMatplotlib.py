# ******************************************************************************

#  @(#)SpecPlotMatplotlib.py	3.22  01/09/24 CSS

#  "splot" Release 3

#  Copyright (c) 2013,2014,2015,2016,2017,2018,2020,2021,2022,2023,2024
#  by Certified Scientific Software.
#  All rights reserved.

#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software ("splot") and associated documentation files (the
#  "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject to
#  the following conditions:

#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.

#  Neither the name of the copyright holder nor the names of its contributors
#  may be used to endorse or promote products derived from this software
#  without specific prior written permission.

#     * The software is provided "as is", without warranty of any   *
#     * kind, express or implied, including but not limited to the  *
#     * warranties of merchantability, fitness for a particular     *
#     * purpose and noninfringement.  In no event shall the authors *
#     * or copyright holders be liable for any claim, damages or    *
#     * other liability, whether in an action of contract, tort     *
#     * or otherwise, arising from, out of or in connection with    *
#     * the software or the use of other dealings in the software.  *

# ******************************************************************************

import weakref
import time
import numpy as np

from pyspec.graphics.QVariant import (QWidget, pyqtSignal,
                                     QHBoxLayout, QVBoxLayout,
                                     QGridLayout,
                                     Qt, QSizePolicy)
from pyspec.graphics import mpl_version_no, qt_variant
from pyspec.graphics.QVariant import mpl_backend
from pyspec.utils import is_windows
from pyspec.css_logger import log

from Constants import *


mpl_legend_positions = {
   'auto':  0,
   'top_right':  1,
   'top_left':  2,
   'bottom_right':  4,
   'bottom_left':  3,
   'top_center':  9,
   'bottom_center':  8,
}

#if qt_variant() in ["PyQt6", "PySide6"]:
#    import matplotlib
#    import matplotlib.backends.backend_qtagg as mpl_backend
#    matplotlib.use("QtAgg")
#elif qt_variant() in ["PyQt5", "PySide2"]:
#    import matplotlib.backends.backend_qt5agg as mpl_backend
#else:
#    import matplotlib.backends.backend_qt4agg as mpl_backend

FigureCanvas = mpl_backend.FigureCanvasQTAgg

from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, AutoLocator, MaxNLocator, LogLocator
from matplotlib.ticker import FormatStrFormatter, FuncFormatter, ScalarFormatter
from matplotlib.font_manager import FontProperties

from SpecPlotBaseClass import SpecPlotBaseClass, SpecPlotCurve, SpecPlotMarker
from CrossHairsMatplotlib import CrossHairs
from ScrollZoomerMatplotlib import ScrollZoomer
from ScrollBar import ScrollBar
from RegionZoomMatplotlib import RegionZoom
from PlotTicks import calc_ticks

def trace(fn):
    def wrapped(*v, **k):
        name = fn.__name__
        return fn(*v, **k)
    return wrapped

class ScrollBarBox(QWidget):

    def __init__(self,orientation,*args):

        QWidget.__init__(self, *args)
        self.orientation = orientation

        if self.orientation == Qt.Horizontal:
            self._layout = QHBoxLayout()
        else:
            self._layout = QVBoxLayout()

        self._layout.setContentsMargins(0,0,0,0)
        self._layout.setSpacing(0)

        self.setLayout(self._layout)

        self.space1 = QWidget()
        self.scrollbar = ScrollBar(self.orientation, self)
        self.space2 = QWidget()

        self._layout.addWidget(self.space1)
        self._layout.addWidget(self.scrollbar)
        self._layout.addWidget(self.space2)

    def setPosition(self, pos0, pos1):
        if self.orientation == Qt.Horizontal:
            self.space1.setFixedWidth(int(pos0))
            self.space2.setFixedWidth(int(pos1))
        else:
            self.space1.setFixedHeight(int(pos1))
            self.space2.setFixedHeight(int(pos0))

    def scrollBar(self):
        return self.scrollbar

    def setBase(self, beg, end):
        self.scrollbar.setBase(beg,end)

    def moveSlider(self, zmin, zmax):
        self.scrollbar.moveSlider(zmin, zmax)


class SpecPlotCanvas(FigureCanvas):

    def __init__(self, parent, *args):

        self.parent = parent

        # version 1.1 or later
        if mpl_version_no() > [1,2,0] and not is_windows():
            #self.fig = Figure(tight_layout=True)
            self.fig = Figure()
        else:
            self.fig = Figure()

        self.bkg = None

        super(SpecPlotCanvas, self).__init__(self.fig)
        self.y1axes = self.fig.add_subplot(111)
        self.setParent(parent)

        self.use_y1 = False
        self.use_y2 = False

        self.y2axes = self.y1axes.twinx()

        self.y1_isflat = None
        self.y2_isflat = None

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setDefaultStyle()


        self._xlog = self._y1log = self._y2log = None

        self.xcen = self.ycen = None
        # Artists
        self.showing_grid = False

    def setDefaultStyle(self):

        try:
            def_axiscolor = self.parent.theme.axes_color
        except:
            def_axiscolor = 'red'

        self.xmajorLocator = MaxNLocator()
        self.xminorLocator = AutoMinorLocator()
        self.yminorLocator = AutoMinorLocator()
        self.yflatminorLocator = AutoLocator()


        if mpl_version_no() >= [1,0,0]:
            self.xmajorLocator.set_params(nbins=5)

        self.majorFormatter = FormatStrFormatter("%g")

        self.emptyFormatter = FuncFormatter(self.emptyStr)

        self.y1axes.spines['bottom'].set_color(def_axiscolor)
        self.y1axes.spines['top'].set_color(def_axiscolor)
        self.y1axes.spines['left'].set_color(def_axiscolor)
        self.y1axes.spines['right'].set_color(def_axiscolor)


        if mpl_version_no() >= [1,0,0]:
            self.y1axes.tick_params(axis='x', which='major', direction='in', color=def_axiscolor)
            self.y1axes.tick_params(axis='x', which='minor', direction='in', color=def_axiscolor)
            self.y1axes.tick_params(axis='y', which='major', direction='in', color=def_axiscolor)
            self.y1axes.tick_params(axis='y', which='minor', direction='in', color=def_axiscolor)
            self.y2axes.tick_params(axis='x', direction='in', color=def_axiscolor)
            self.y2axes.tick_params(axis='y', which='minor', direction='in', color=def_axiscolor)
            self.y2axes.tick_params(axis='y', which='major', direction='in', color=def_axiscolor)

        self.y1axes.xaxis.set_major_locator(self.xmajorLocator)
        self.y1axes.xaxis.set_minor_locator(self.xminorLocator)

        if mpl_version_no() >= [1,2,0] and not is_windows():
            self.y1axes.autoscale(enable=True, axis='y', tight=False)
            self.y2axes.autoscale(enable=True, axis='y', tight=False)

        self.y2axes.spines['bottom'].set_color(def_axiscolor)
        self.y2axes.spines['top'].set_color(def_axiscolor)
        self.y2axes.spines['left'].set_color(def_axiscolor)
        self.y2axes.spines['right'].set_color(def_axiscolor)

        self.y1axes.yaxis.set_major_locator(AutoLocator())
        self.y1axes.yaxis.set_minor_locator(self.yminorLocator)

        if mpl_version_no() > [1,2,1]:
            self.fig.set_facecolor("none")
        else:
            self.fig.set_facecolor("white")

        self.y1axes.plot([0], [0])

    def set_flat_y(self, axis, flat):

        if flat:  
            locator = self.yminorLocator
        else:
            locator = self.yflatminorLocator

        if axis == Y1_AXIS:
            ax = self.y1axes.yaxis

            if flat != self.y1_isflat:
                self.y1_isflat = flat
                if mpl_version_no() >= [1,0,0]:
                    ax.set_minor_locator(locator)
        elif axis == Y2_AXIS:
            ax = self.y2axes.yaxis

            if flat != self.y2_isflat:
                self.y2_isflat = flat
                if mpl_version_no() >= [1,0,0]:
                    ax.set_minor_locator(locator)

              
    def set_legend(self, legendflag, legendpos):
        self.set_show_legend(legendflag)
        self.set_legend_position(legendpos)

    def set_show_legend(self, legendflag):
        self.showlegend = legendflag

    def set_legend_position(self, legendpos):
        self.legendpos = legendpos

    def update_axes(self):
        self.y1axes.xaxis.set_major_formatter(self.majorFormatter)

        if not self.use_y1:
            self.y1axes.yaxis.set_major_formatter(self.emptyFormatter)
        else:
            self.y1axes.yaxis.set_major_formatter(self.majorFormatter)

        if not self.use_y2:
            self.y2axes.yaxis.set_major_formatter(self.emptyFormatter)
        else:
            self.y2axes.yaxis.set_major_formatter(self.majorFormatter)

    def show_legend(self):

        if not self.showlegend:
            self.hide_legend()

        h1,l1 = self.y1axes.get_legend_handles_labels()
        h2,l2 = self.y2axes.get_legend_handles_labels()

        hs = h1 + h2
        ls = l1 + l2

        legend_pos = self.legendpos

        try:
            locvalue = mpl_legend_positions[legend_pos]
        except IndexError:
            locvalue = "best"

        if len(hs) > 1:
            fontP = FontProperties()
            fontP.set_size('small') 
            legend = self.y1axes.legend(hs,ls, loc=locvalue, prop=fontP)
            #legend.draggable()
        else:
            self.hide_legend()
 
    def hide_legend(self):

        legend = self.y1axes.get_legend()
        try:
            if legend:
                legend.set_visible(False)
        except:
            pass

    def emptyStr(self,x,pos):
        # percentage example
        # log.log(3,"Formatting x=%s, pos=%s" % (x,pos))
        # return "{0:.0f}%".format(x * 100)
        return ""

    def set_xlog(self, xlog):
        if self._xlog != xlog:
            if xlog:
                self.y1axes.set_xscale("log")
                #self.y1axes.set_xscale("log", nonposx="mask")
                #self.y1axes.set_xscale("symlog")
                self.y1axes.xaxis.set_major_locator(LogLocator())
            else:
                self.y1axes.set_xscale("linear")
                self.y1axes.xaxis.set_major_locator(AutoLocator())
                self.y1axes.xaxis.set_minor_locator(self.yminorLocator)
            self._xlog = xlog

    def set_y1log(self, y1log):
        if self._y1log != y1log:
            if y1log:
                self.y1axes.set_yscale("log")
                #self.y1axes.set_yscale("log", nonposy="mask")
                #self.y1axes.set_yscale("symlog")
            else:
                self.y1axes.set_yscale("linear")
            self._y1log = y1log

    def set_y2log(self, y2log):
        if self._y2log != y2log:
            if y2log:
                self.y2axes.set_yscale("log")
                #self.y2axes.set_yscale("log", nonposy="clip")
                #self.y2axes.set_yscale("symlog")
            else:
                self.y2axes.set_yscale("linear")
            self._y2log = y2log

    def show_grid(self, gridon):
        if gridon == self.showing_grid:
            return

        self.showing_grid = gridon

        if gridon:
            self.y1axes.grid(which='major', color='#666666', linestyle='-.')
            self.y1axes.grid(which='minor', color='#999999', linestyle=':')
        else:
            self.y1axes.grid()
            self.y1axes.grid(which='minor', color='#999999', linestyle=' ')

    def setUseY1(self, flag):
        self.use_y1 = flag

    def setUseY2(self, flag):
        self.use_y2 = flag

    def set_xlabel(self, label):
        self.y1axes.set_xlabel(label)

    def set_xlimits(self, x0, x1, ticks=None):
        self.y1axes.set_xlim((x0, x1))

    def set_y1limits(self, y0, y1, ticks):
        if ticks is None:
            self.y1axes.set_yticks([])
        else:
            self.y1axes.set_ylim((y0, y1))
            self.y1axes.set_yticks(ticks)

    def set_y2limits(self, y0, y1, ticks):
        if ticks is None:
            self.y2axes.set_yticks([])
        else:
            self.y2axes.set_ylim((y0, y1))
            self.y2axes.set_yticks(ticks)

    def plot(self, xdata, ydata, mne, yaxis=Y1_AXIS):
        if yaxis == Y2_AXIS:
            return self.y2axes.plot(xdata, ydata, label=mne)
        else:
            return self.y1axes.plot(xdata, ydata, label=mne)

    def savefig(self, title,filename):
        self.prepare_print(title)
        self.fig.savefig(filename)
        self.restore_after_print()

    def printfig(self, title, printer, filename):
        self.prepare_print(title, bw=True)
        self.render(printer)
        self.restore_after_print()

    def prepare_print(self, title, bw=False):
        from textwrap import wrap

        self.print_bw = bw
        if bw:
            self.canvas_bgcolor = self.y1axes.get_fc()
            self.fig_bgcolor = self.fig.patch.get_facecolor()

        slines = []
        for line in title.split("\n"):
            slines.extend(wrap(line,60))
        
        title = "\n".join(slines)

        title_art = self.y1axes.set_title(title, loc="left")
        title_art.set_y(1.05)
        self.fig.subplots_adjust(top=0.8)
        self.draw()

    def restore_after_print(self):
        try:
            title_art = self.y1axes.set_title(' ', loc="left")
            title_art.set_y(1.00) 

            self.fig.subplots_adjust(top=0.95)
    
            if self.print_bw:
                self.y1axes.set_facecolor(self.canvas_bgcolor)
                self.fig.patch.set_facecolor(self.fig_bgcolor)

            self.draw()
        except:
            import traceback
            log.log(2, traceback.format_exc())

    def getCenter(self):
        xlim = self.y1axes.get_xlim()
        ylim = self.y1axes.get_ylim()

        self.xcen = xlim[0] + (xlim[1] - xlim[0]) / 2.0
        self.ycen = ylim[0] + (ylim[1] - ylim[0]) / 2.0

        return self.xcen, self.ycen

    def getXLimits(self):
        return self.y1axes.get_xlim()

    def getYLimits(self):
        return self.y1axes.get_ylim()

    def pixelsToXY(self, x, y):
        if not self._y1log:
            inv = self.y1axes.transData.inverted()
            return inv.transform((x, y))
        else:
            ax = self.y1axes
            trans = ax.transAxes + ax.transScale + ax.transLimits
            inv = trans.inverted()
            return inv.transform((x, y))


class SpecPlotMarkerMatplotlib(SpecPlotMarker):

    def __init__(self, label, **kwargs):
        SpecPlotMarker.__init__(self, label, **kwargs)
        self.attached = False
        self.line = self.txt = self.box = None

    def draw(self):
        pass

    def isAttached(self):
        return self.attached

    def attach(self, plot):
        self.canvas = weakref.ref(plot.canvas)
        if not self.isAttached():
            self.draw_pending = True
            self.attached = True

        self.attached = True

    def detach(self):
        if self.line: 
             self.line.remove()
             self.line = None

        if self.txt: 
             self.txt.remove()
             self.txt = None

        if self.box: 
             self.box.remove()
             self.box = None

        self.attached = False

class SpecPlotVerticalMarkerMatplotlib(SpecPlotMarkerMatplotlib):

    marker_type = MARKER_VERTICAL

    def __init__(self, label, **kwargs):
        SpecPlotMarkerMatplotlib.__init__(self, label, **kwargs)

    def setLabelPosition(self, position):
        self.setYValue(position)

    def setCoordinates(self, posinfo):
        self.setXValue(posinfo[0])

    def draw(self):

        # I should remove only if visibitily changes
        if not self.attached:
            return

        x = self.getXValue()
        label = self.getLabel()
        labelx, labely = self.getLabelPosition()

        xcen, ycen = self.canvas().getCenter()
        xmin, xmax = self.canvas().getXLimits()

        if x < ( xmin + (xcen-xmin)/3.0):
            horalign = 'left'
        elif x > (xcen + 2.0*(xmax-xcen)/3.0):
            horalign = 'right'
        else:
            horalign = 'center'


        if x > xmax or x < xmin:

            if self.line:
                self.line.remove()
                self.line = None
                self.txt.remove()
                self.txt = None

            bbox_props = dict(boxstyle="round", fc="#ececdd", ec="b", lw=1)

            if not self.box:
                axes = self.canvas().y1axes
                self.box = axes.text(labelx, labely, label,
                     color=self.color, horizontalalignment=horalign, bbox=bbox_props)
            
            bb = self.box.get_bbox_patch()

            if x > xmax:
                boxx = xmax
                horalign = 'right'
                arrow = 'rarrow'
                self.box.set_x(xmax)
                self.box.set_y(labely)
                self.box.set_ha(horalign)
                bb.set_boxstyle("rarrow")
            elif x < xmin:
                boxx = xmin
                horalign = 'left'
                arrow = 'larrow'
                bb.set_boxstyle("larrow")
            self.box.set_x(boxx)
            self.box.set_y(labely)
            self.box.set_text(label)
            bb.set_boxstyle(arrow)
            self.box.set_ha(horalign)

        elif not self.line: 
            if self.box:
                self.box.remove()
                self.box = None
            axes = self.canvas().y1axes
            self.line = axes.axvline(x, color=self.color)
            self.txt = axes.text(labelx, labely, label,
                     color=self.color, horizontalalignment=horalign)
        else:
            self.line.set_xdata(x)
            self.txt.set_x(labelx)
            self.txt.set_y(labely)
            self.txt.set_text(label)
            self.txt.set_ha(horalign)

class SpecPlotTextMarkerMatplotlib(SpecPlotMarkerMatplotlib):
    marker_type = MARKER_TEXT

    def __init__(self, label, **kwargs):
        SpecPlotMarkerMatplotlib.__init__(self, label, **kwargs)

    def setCoordinates(self, posinfo):
        self.x, self.y = posinfo

    def getCoordinates(self):
        return self.x, self.y

    def draw(self):
        # I should remove only if visibitily changes
        if not self.attached:
            return

        label = self.getLabel()
        labelx, labely = self.getLabelPosition()

        if not self.txt:
            axes = self.canvas().y1axes
            self.txt = axes.text(labelx, labely, label,
                     color=self.color)
        else:
            self.txt.set_x(labelx)
            self.txt.set_y(labely)
            self.txt.set_text(label)


class SpecPlotSegmentMatplotlib(SpecPlotMarkerMatplotlib):
    marker_type = MARKER_SEGMENT

    def __init__(self, label, **kwargs):
        SpecPlotMarkerMatplotlib.__init__(self, label, **kwargs)

    def setCoordinates(self, coords):
        self.x0, self.y0, self.x1, self.y1 = coords

    def getCoordinates(self):
        return self.x0, self.y0, self.x1, self.y1

    def getXValue(self):
        return (self.x0 + self.x1) / 2.0

    def getYValue(self):
        return (self.y0 + self.y1) / 2.0

    def draw(self):
        # I should remove only if visibitily changes
        if not self.attached:
            return

        x0, y0, x1, y1 = self.getCoordinates()

        label = self.getLabel()

        labelx = self.getXValue()
        labely = self.getYValue()

        xcen, ycen = self.canvas().getCenter()
        xmin, xmax = self.canvas().getXLimits()

        if labelx < ( xmin + (xcen-xmin)/3.0):
            horalign = 'left'
        elif labelx > (xcen + 2.0*(xmax-xcen)/3.0):
            horalign = 'right'
        else:
            horalign = 'center'

        if not self.line:
            axes = self.canvas().y1axes
            self.line = axes.plot([x0,x1],[y0,y1], color=self.color)[0]
            self.txt = axes.text(labelx, labely, label,
                     color=self.color, horizontalalignment=horalign)
        else:
            self.line.set_xdata([x0,x1])
            self.line.set_ydata([y0,y1])
            self.txt.set_x(labelx)
            self.txt.set_y(labely)
            self.txt.set_text(label)
            self.txt.set_ha(horalign)


class SpecPlotCurveMatplotlib(SpecPlotCurve):

    def __init__(self, colname, canvas):
        SpecPlotCurve.__init__(self, colname)
        self.canvas = weakref.ref(canvas)
        self.line = None
        self.yaxis = Y1_AXIS

        self.plot_pending = False
        self.attached = False
        self.selected = False

    def isAttached(self):
        return self.attached

    def attach(self):
        if not self.isAttached():
            self.plot_pending = True
            self.attached = True

        self.plot()

    def detach(self):
        # I should remove if visibility or axes change only. otherwise just set data
        if self.line: 
             self.line.remove()
             self.line = None
        self.attached = False

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def show(self, axis):
        self.setYAxis(axis)
        self.attach()

    def setYAxis(self, axis):
        if axis != self.yaxis:
            self.yaxis = axis

            if self.isAttached():
                self.detach()
                self.attach()

    def getLimits(self):
        if self._x.any() and len(self._y.tolist()):
            xdata = self._x
            ydata = self._y
            minx, maxx = xdata.min(), xdata.max()
            miny, maxy = ydata.min(), ydata.max()
            minposy = np.where(ydata > 0, ydata, np.inf).min()
            return (minx, maxx, miny, maxy), minposy, self.yaxis
        else:
            return (None,) * 4, None, self.yaxis

    def plot(self):
        if self._x.any():
            self._redraw()

    def _redraw(self):
        if not self.isAttached():
            return

        if self.plot_pending:
            self.line = self.canvas().plot(self._x, self._y, self.mne, self.yaxis)[0]
            self.plot_pending = False
        else:
            self.line.set_xdata(self._x)
            self.line.set_ydata(self._y)

        self.configure()

    def configure(self):

        self.line.set_color(str(self.color))

        if not self.usedots:
            if not self.linethick:
                marker = "."
            else:
                marker = ""
        else:
            marker = "o"

        self.line.set_marker(marker)
        self.line.set_markersize(self.dotsize)
        self.line.set_linewidth(self.linethick)

        if not self.uselines:
            self.line.set_linestyle('None')
        else:
            self.line.set_linestyle('-')

        if self.selected:
            self.line.set_zorder(ZLEVEL_SELECTED)
        else:
            self.line.set_zorder(ZLEVEL_CURVE)


class SpecPlotMatplotlib(QWidget, SpecPlotBaseClass):

    # Signals

    pointSelected = pyqtSignal(str, float)
    regionSelected = pyqtSignal(str, float, float)
    configurationChanged = pyqtSignal()

    _vertical_marker_class = SpecPlotVerticalMarkerMatplotlib
    _text_marker_class = SpecPlotTextMarkerMatplotlib
    _segment_marker_class = SpecPlotSegmentMatplotlib

    def __init__(self, parent=None, *args, **kwargs):

        self.parent = parent
        self.xlabel = "Point no."

        # data limits
        self.x_min = None
        self.x_max = None
        self.y1_min = None
        self.y1_max = None
        self.y2_min = None
        self.y2_max = None

        # axes limits
        self.axes_auto = {}
        self.axes_limits = {}

        SpecPlotBaseClass.__init__(self,**kwargs)
        QWidget.__init__(self, parent, *args)

        self.prev_status = None

        self.legendY1 = self.legendY2 = None
        self._initWidget()
        self.initMarkers()
        self.loadPreferences()
        self.initColorTable()

        self.setDataStatus(DATA_STATIC)

        self._setShowLegend()
        self._setLegendPosition()

        self.crosshairs = CrossHairs(weakref.ref(self.canvas))
        self.zoomer = ScrollZoomer(weakref.ref(self))
        self.regionzoom = RegionZoom(weakref.ref(self))

        hscrollbar = self.hbox.scrollBar()
        hscrollbar.sliderMoved.connect(self.zoomer.scrollIt)

        vscrollbar = self.vbox.scrollBar()
        vscrollbar.sliderMoved.connect(self.zoomer.scrollIt)

        self.replot()


    def _initWidget(self):

        self._layout = QGridLayout()

        # Public members

        # create a figure, add an axes area and make space for a colorbar

        # create a qt widget that contains the figure
        self.canvas = SpecPlotCanvas(self)

        # Prepare scrollbars
        self.hbox = ScrollBarBox(Qt.Horizontal)
        self.vbox = ScrollBarBox(Qt.Vertical)

        self.setLayout(self._layout)

        # self._layout.addWidget(self.legendY1)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setRowStretch(1,1)
        self._layout.setColumnStretch(0,1)

        self._layout.addWidget(self.hbox,0,0)
        self._layout.addWidget(self.canvas,1,0)
        self._layout.addWidget(self.vbox,1,1)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # connect events
        self.canvas.mpl_connect("button_press_event", self.start_selection)
        self.canvas.mpl_connect("button_release_event", self.end_selection)
        self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        self.canvas.mpl_connect("key_press_event", self.key_pressed)

        #self.canvas.mpl_connect('resize_event', self.resized)

    def horizontalScrollBar(self):
        return self.hbox

    def verticalScrollBar(self):
        return self.vbox

    def horizontalScrollBar(self):
        return self.hbox

    def verticalScrollBar(self):
        return self.vbox

    def resetData(self):
        log.log(3,"TODO reset data")
        pass

    def _setDataStatus(self):
        if self.prev_status != self.status:
            try:
                bgcolor = self.theme.status_color[self.status]
            except:
                bgcolor = 'white'
            #self.canvas.y1axes.set_axis_bgcolor(bgcolor)
            self.canvas.y1axes.patch.set_facecolor(bgcolor)
        self.prev_status = self.status

    def _setShowLegend(self):
        self.canvas.set_show_legend(self.showlegend)
        self.queue_replot()

    def _setLegendPosition(self):
        self.canvas.set_legend_position(self.legend_position)
        self.queue_replot()

    def addCurve(self, colname):

        curve = SpecPlotCurveMatplotlib(colname, self.canvas)
        self.curves[colname] = curve

        # line style
        color = self.colorTable.getColor(colname)
        curve.setColor(color)
        curve.showErrorBars(self.showbars)
        curve.setUseLines(self.uselines)
        curve.setLineThickness(self.linethick)
        curve.setUseDots(self.usedots)
        curve.setDotSize(self.dotsize)
        curve.attach() 

        self.setAxisTitles()
        self.queue_replot()

    def addVerticalMarker(self, label, **kwargs):
        return SpecPlotVerticalMarkerMatplotlib(label, **kwargs)

    def addTextMarker(self, label, **kwargs):
        return SpecPlotTextMarkerMatplotlib(label, **kwargs)

    def addSegmentMarker(self, label, **kwargs):
        return SpecPlotSegmentMatplotlib(label, **kwargs)

    def _updateTitles(self):
        self.canvas.set_xlabel(self.xlabel)
        self.canvas.y1axes.set_ylabel(self.y1label)
        self.canvas.y2axes.set_ylabel(self.y2label)

    def setXAxisAuto(self):
        self._setAxisAuto(X_AXIS, True)

    def setY1AxisAuto(self):
        self._setAxisAuto(Y1_AXIS, True)

    def setY2AxisAuto(self):
        self._setAxisAuto(Y2_AXIS, True)

    def _setAxisAuto(self, axis, flag):
        if (axis not in self.axes_auto) or (flag != self.axes_auto[axis]):
            self.axes_auto[axis] = flag

    def _setAxisLimits(self, axis, axmin, axmax):

        self._setAxisAuto(axis, False)

        if (axis not in self.axes_limits) or (axmin, axmax) != self.axes_limits[axis]:
            self.axes_limits[axis] = (axmin, axmax)

    def _showCurve(self, colname, axis=Y1_AXIS):
        self.curves[colname].show(axis)

    def _hideCurve(self, colname):
        if colname in self.curves:
            self.curves[colname].detach()
            self.queue_replot()

    def _useY1Axis(self, flag=True):
        self.using_y1 = flag
        self.canvas.setUseY1(flag)

    def _useY2Axis(self, flag=True):
        self.using_y2 = flag
        self.canvas.setUseY2(flag)

    def _changeCurveColor(self, mne, color):

        mne = str(mne)
        if mne in self.curves.keys():
            self.curves[mne].setColor(color)

        self.setAxisTitles()  # should change colors in legend
        self.queue_replot()

    def _showGrid(self):
        """ nothing to do. show grid if flag is set """
        pass

    def _hideGrid(self):
        """ nothing to do. show grid if flag is set """
        pass

    def _setXLog(self, flag):
        pass

    def _setY1Log(self, flag):
        pass

    def _setY2Log(self, flag):
        pass

    # end plot options methods


    # update plot
    def getY1ViewRange(self):
        return  self.canvas.y1axes.get_ylim()
     
    def emit_configuration_changed(self):
        self.configurationChanged.emit()

    # handling of axes limits
    def set_limits_and_ticks(self):

        # calculate data limits
        xchanged, y1changed, y2changed = self.check_limits()

        if None not in [self.x_min, self.x_max]:
            self.set_xlimits()
            self.set_y1limits()
            self.set_y2limits()

    def set_xlimits(self, ivals=5):

        if not self.axes_auto[X_AXIS] and X_AXIS in self.axes_limits: 
            xmin, xmax = self.axes_limits[X_AXIS]
        else:
            xmin, xmax = self.x_min, self.x_max
        
        if self.xlog:
            xmin, xmax, ticks = calc_ticks(xmin, xmax, ivals, self.xlog)
            self.canvas.set_xlimits(xmin, xmax, ticks)
        else:
            self.canvas.set_xlimits(xmin, xmax)


    def set_y1limits(self, ivals=5):
        if self.using_y1:
            if Y1_AXIS in self.axes_limits and not self.axes_auto[Y1_AXIS]:
                ymin, ymax = self.axes_limits[Y1_AXIS]
            else: 
                ymin, ymax = self.y1_min, self.y1_max
                if self.y1log:
                     ymin = self.y1min_pos 

            #if ymin > 0:
            ymin, ymax, ticks = calc_ticks(ymin,ymax,ivals,self.y1log)
            #else:
                #ymin, ymax, ticks = calc_ticks(ymin,ymax,ivals,False)
        else:
            ymin, ymax = (None,None)
            ticks = None

        log.log(2, " setting y1 limits and ticks to: {} {} {}".format(ymin,ymax, ticks))

        self.canvas.set_y1limits(ymin,ymax,ticks)

    def set_y2limits(self, ivals=5):
        if self.using_y2:
            if Y2_AXIS in self.axes_limits and not self.axes_auto[Y2_AXIS]:
                ymin, ymax = self.axes_limits[Y2_AXIS]
            else: 
                ymin, ymax = self.y2_min, self.y2_max
                if self.y2log:
                     ymin = self.y2min_pos

            #if ymin > 0:
            ymin, ymax, ticks = calc_ticks(ymin,ymax,ivals,self.y2log)
            #else:
            #    ymin, ymax, ticks = calc_ticks(ymin,ymax,ivals,False)
        else:
            ymin, ymax = (None,None)
            ticks = None

        self.canvas.set_y2limits(ymin,ymax,ticks)

    def check_limits(self):

        x_min, x_max = None, None
        y1_min, y1_max = None, None
        y2_min, y2_max = None, None

        xlimchanged = False
        y1limchanged = False
        y2limchanged = False

        minpos_y1 = minpos_y2 = None

        # Find currrent limits

        x_fixed = False

        if self.isScanRunning(): 
            if not self.x_range_auto:
                x_min = self.x_range_beg
                x_max = self.x_range_end
                if None not in [x_min, x_max]:
                    x_fixed = True

        for curve_name in self.curves:
            curve = self.curves[curve_name] 

            if not curve.isAttached():
                continue

            lims, minposy, yaxis = curve.getLimits()

            if None in lims:
                continue

            minx, maxx, miny, maxy = lims

            if not x_fixed:
                if x_min is None or minx < x_min:
                    x_min = minx

                if x_max is None or maxx > x_max:
                    x_max = maxx


            if yaxis is Y2_AXIS:
                if y2_min is None or miny < y2_min:
                    y2_min = miny
                if y2_max is None or maxy > y2_max:
                    y2_max = maxy

                if minpos_y2 is None or minposy < minpos_y2:
                    minpos_y2 =  minposy
            else:
                if y1_min is None or miny < y1_min:
                    y1_min = miny
                if y1_max is None or maxy > y1_max:
                    y1_max = maxy

                if minpos_y1 is None or  minposy < minpos_y1:
                    minpos_y1 =  minposy

        # check if they have changed
        if x_min != self.x_min:
            self.x_min = x_min
            xlimchanged = True

        if x_max != self.x_max:
            self.x_max = x_max
            xlimchanged = True

        if y1_min != self.y1_min:
            self.y1_min = y1_min
            y1limchanged = True

        if y1_max != self.y1_max:
            self.y1_max = y1_max
            y1limchanged = True

        if y2_min != self.y2_min:
            self.y2_min = y2_min
            y2limchanged = True

        if y2_max != self.y2_max:
            self.y2_max = y2_max
            y2limchanged = True

        self.y1min_pos = (minpos_y1 is not None) and minpos_y1 or 0
        self.y2min_pos = (minpos_y2 is not None) and minpos_y2 or 0

        return xlimchanged, y1limchanged, y2limchanged

    # end handling of axes limits
    def start_selection(self, event):

        if self.zoommode == REGIONZOOM_MODE:
            self.regionzoom.begin(event)
            self.queue_replot()
        elif self.zoommode == ZOOM_MODE:
            self.zoomer.begin(event)
            self.queue_replot()

    def end_selection(self, event):
        
        if self.zoommode == CROSSHAIRS_MODE:
             xlabel = self.first_x
             xpos,ypos = self.canvas.pixelsToXY(event.x, event.y)
             self.pointSelected.emit(xlabel, xpos)
        elif self.zoommode == REGIONZOOM_MODE:
            self.regionzoom.end(event)
            self.queue_replot()
        elif self.zoommode == ZOOM_MODE:
            self.zoomer.end(event)
            self.queue_replot()

    def mouse_move(self, event):
        if self.zoommode == CROSSHAIRS_MODE:
            self.crosshairs.mouse_move(event)
            self.queue_replot()
        elif self.zoommode == REGIONZOOM_MODE:
            if event.inaxes and self.regionzoom.isSelecting():
                self.regionzoom.mouse_move(event)
                self.queue_replot()
        elif self.zoommode == ZOOM_MODE:
            if event.inaxes and self.zoomer.isSelecting():
                self.zoomer.mouse_move(event)
                self.queue_replot()

    def key_pressed(self, ev):
        if ev.key == 'escape':
            self.zoomer.resetZoom()

    def resized(self, event):
        self.queue_replot()

    def regionSelection(self, xbeg, xend):
        xlabel = self.first_x
        self.regionSelected.emit(xlabel, xbeg, xend)

    def replot(self):

        try:
            self.check_curves_are_flat()
        except:
            import traceback
            log.log(2, traceback.format_exc())

        

        self._setDataStatus()
        self.setAxisTitles()

        for name, curve in self.curves.items():
            curve.plot()

        # if self.showing_grid:
        #     self.canvas.show_grid(True)
        # else:
        #     self.canvas.show_grid(False)

        self.canvas.show_grid(True)

        self.canvas.set_xlog(self.xlog)
        self.canvas.set_y1log(self.y1log)
        self.canvas.set_y2log(self.y2log)
            
        self.canvas.show_legend()
        self.canvas.update_axes()

        if self.zoommode == ZOOM_MODE and self.zoomer.isZoomed():
            self.zoomer.rescale()
        else:
            self.set_limits_and_ticks()

        self._replot_markers()

        try:
            if mpl_version_no() > [1,2,0] and not is_windows():
                self.canvas.fig.tight_layout()
        except BaseException as e:
            import traceback
            log.log(2, traceback.format_exc())

        self.canvas.draw()

        if self.zoommode == ZOOM_MODE and not self.zoomer.isZoomed():
            self.zoomer.setZoomBase()

    def check_curves_are_flat(self):

        y1flat, y2flat = (True, True)

        for curve in self.curves.values():
            lims, minposy, ax = curve.getLimits() 

            if (lims[2] == lims[3]):
                 if ax == Y1_AXIS:
                     y1flat = False
                 else: 
                     y2flat = False

        self.canvas.set_flat_y(Y1_AXIS, y1flat)
        self.canvas.set_flat_y(Y2_AXIS, y2flat)

    def redrawCurves(self):
        self.queue_replot()

    def _replot_markers(self):
        self._position_markers()

        for marker_name, marker in self.markers.items():
            marker.draw()

    # end update plot

    # begin print
    def saveAsImage(self, filename,title):
        self.canvas.savefig(title, filename)

    def printPlot(self, title, printer, filename):
        self.canvas.printfig(title, printer, filename)

    # end print

def test():
    import sys
    from pyspec.graphics.QVariant import (QApplication, QMainWindow)
    app = QApplication([])
    win = QMainWindow()
    wid = SpecPlotMatplotlib(theme="classic")
    win.setCentralWidget(wid)

    from DataBlock import DataBlock

    data = np.array([[1, 2, 4, 3], [3, 5, 4, 2], [4, 6, 1, 7], [
                         5, 3, 3, 1], [0, 4, 3, 2], [6, 19, 18, 13]])

    colnames = ["x", "sec", "mon", "det"]

    dblock = DataBlock()
    wid.setDataBlock(dblock)
    dblock.setData(data) 
    dblock.setColumnNames(colnames)
    dblock.setXSelection("x")
    dblock.setY1Selection(["mon", ])
    wid.updateColumnSelection()

    win.show()

    try:
        exec_ = getattr(app, "exec_")
    except AttributeError:
        exec_ = getattr(app, "exec")
    sys.exit(exec_())

if __name__ == '__main__':
    test()

