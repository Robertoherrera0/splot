#******************************************************************************
#
#  @(#)SpecPlotBaseClass.py	3.12  01/07/22 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2020,2021,2022
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

import numpy as np
import time
import copy
import math
import weakref

import themes

from pyspec.graphics.QVariant import QTimer
from pyspec.graphics import qt_variant
from Constants import *
from pyspec.css_logger import log

from Preferences import Preferences
from PlotOptions import PlotOptionsDialog, PlotDefaults, LegendPositions
import Colors

class SpecPlotCurve(object):

    def __init__(self, mne):
        self.mne = mne

        self.hidden = []
        self._x = np.asarray([])
        self._y = np.asarray([])
        self._dy = np.asarray([])   # for errorbars

        self.uselines = PlotDefaults['uselines']
        self.linethick = PlotDefaults['linethick']
        self.usedots = PlotDefaults['usedots']
        self.dotsize = PlotDefaults['dotsize']
        self.showbars = PlotDefaults['showbars']

        self.color = Colors.ColorTable().getDefaultColor()

    def setData(self, xdata, ydata):
        self._x = xdata
        self._y = ydata

        if self.showbars:
            self._dy = np.asarray([math.sqrt(abs(yval)) for yval in ydata])
            self._ymin = (self._y - self._dy)  # min values for bars
            self._ymax = (self._y + self._dy)  # max values for bars

    def setConfig(self,config):
        if 'usedots' in config: 
            self.setUseDots(config['usedots'])
        if 'color' in config: 
            self.setColor(config['color'])

    def getXData(self):
        return self._x

    def getXMin(self):
        return self._x.min()
    def getXMax(self):
        return self._x.max()

    def getYData(self):
        return self._y

    def getYMin(self):
        return self._y.min()
    def getYMax(self):
        return self._y.max()

    def setColor(self, color):
        self.color = color
        self._redraw()

    def setUseLines(self, flag):
        self.uselines = flag

    def setLineThickness(self, linethick):
        self.linethick = linethick

    def setUseDots(self, flag):
        self.usedots = flag

    def setDotSize(self, dotsize):
        self.dotsize = dotsize

    def showErrorBars(self, flag):
        self.showbars = flag
        if self.showbars and self._y.any():
            self._dy = np.asarray([math.sqrt(abs(yval)) for yval in self._y])
            self._ymin = (self._y - self._dy)  # array of min values for bars
            self._ymax = (self._y + self._dy)  # array of max values for bars

    def setHiddenPoints(self, hiddenpoints):
        self.hidden = hiddenpoints

    def clearCurve(self):
        self._x = np.empty(0)
        self._y = np.empty(0)
        self.redraw()

    def select(self):
        log.log(3,"%s curve selected" % self.mne)

    def deselect(self):
        log.log(3,"%s curve deselected" % self.mne)

    def redraw(self):
        self._redraw()

    def _redraw(self):
        pass


class SpecPlotMarker(object):

    marker_type = "marker"

    def __init__(self, label, persistent=False, showlabel=True, *args):

        self.showlabel = showlabel
        self.x = 0
        self.y = 0

        self.status = "detached"
        self.persistent = persistent

        self.label = ""
        if self.showlabel:
            if label.startswith("##"):
                self.label = label[2:]
            else:
                self.label = label

        self.setColor("black")

    def setColor(self, color):
        self.color = color

    def setShowOptions(self, color, thickness=3):
        self.setColor(color)
        self.linethick = thickness

    def getXValue(self):
        return self.x

    def getYValue(self):
        return self.y

    def setXValue(self, x):
        self.x = x

    def setYValue(self, y):
        self.y = y

    def setLabel(self, label):
        """ change label after creation """
        self.label = label

    def getLabel(self):
        return self.label

    def getLabelPosition(self):
        return self.getXValue(), self.getYValue()

    def isPersistent(self):
        return self.persistent

    def getMarkerType(self):
        return self.marker_type


class SpecPlotVerticalMarker(SpecPlotMarker):
    """
     A vertical line with a label and a color
    """

    marker_type = MARKER_VERTICAL

    def __init__(self, label, persistent=False, showlabel=True, *args):
        SpecPlotMarker.__init__(self, label, persistent, showlabel, *args)

    def setCoordinates(self, posinfo):
        self.setXValue(posinfo[0])

    def getCoordinates(self):
        return [self.x, ]

    def setLabelPosition(self, position):
        self.setYValue(position)


class SpecPlotBaseClass(object):

    def __init__(self, theme=None):
        self.datablock = None

        self.scanObj = None
        self.status = None
        self.theme = None

        self.plotMode = PlotNormalMode

        self.plotconfig = {}

        self.prefs = Preferences()

        if not self.theme:
            if theme is None:
                self.theme = themes.get_theme(self.prefs['theme'])
            else:
                self.theme = themes.get_theme(theme)

        self.active = True

        self.xlog = None
        self.y1log = None
        self.y2log = None
        self.showing_grid = None

        self.using_y1 = False
        self.using_y2 = False

        self.x = []
        self.first_x = None
        self.y1s = []
        self.y2s = []

        self.xtitle = None
        self.y1title = None
        self.y2title = None

        self.xlabel = None
        self.y1label = None
        self.y2label = None

        self.curves = {}
        self.markers = {}

        self.curve_selected = None

        self.showing_stats = True
        self.showing_motor = False
        self.stats_hidden = False
        self.motor_marker_active = False

        self.full_xrange = False

        self.x_range_beg = None
        self.x_range_end = None
        self.y_range_beg = None
        self.y_range_end = None

        self.x_range_auto = True
        self.y_range_auto = True

        self.x_range_set = False
        self.y_range_set = False

        self.zoomer = self.crosshairs = self.regionzoom = None
        self.zoommode = None

        self.pending_actions = set()

        self.actiontimer = QTimer()
        self.actiontimer.timeout.connect(self._do_pending)
        self.initPendingActions()

        self.options_dialog = None

    def loadPreferences(self):

        gridmode = self.prefs.getValue('gridmode', "Off")
        showmotor = self.prefs.getValue('showmotor')

        self.showbars = self.prefs.getValue('showbars')
        self.usedots = self.prefs.getValue('usedots', PlotDefaults['usedots'])
        self.dotsize = self.prefs.getValue('dotsize')
        self.uselines = self.prefs.getValue('uselines')
        self.linethick = self.prefs.getValue('linethick')

        self.showlegend = self.prefs.getValue('showlegend')
        self.legend_position = self.prefs.getValue('legendpos')

        self.showpts = self.prefs.getValue('showpts')

        if self.showbars is None:
            self.showbars = PlotDefaults['showbars']
        else:
            # can be a string with 1 or True
            self.showbars = eval(str(self.showbars))

        if self.usedots is None:
            self.usedots = PlotDefaults['usedots']
        else:
            # can be a string with 1 or True
            self.usedots = eval(str(self.usedots))

        if self.uselines is None:
            self.uselines = PlotDefaults['uselines']
        else:
            self.uselines = eval(str(self.uselines))

        if self.dotsize is None:
            self.dotsize = PlotDefaults['dotsize']
        else:
            self.dotsize = int(self.dotsize)

        if self.linethick is None:
            self.linethick =  PlotDefaults['linethick']
        else:
            self.linethick = int(self.linethick)

        if self.showlegend is None:
            self.showlegend = PlotDefaults['showlegend']
        else:
            self.showlegend = eval(str(self.showlegend))

        legendpos = self.legend_position
        if legendpos is None or str(legendpos) not in LegendPositions:
            self.legend_position = PlotDefaults['legendpos']
        else:
            self.legend_position = str(legendpos)

        if self.showpts is None:
            self.showpts = 2048
        else:
            self.showpts = int(self.showpts)


        if gridmode == "On":
            self.showing_grid = True
        else:
            self.showing_grid = False
        self.showGrid(self.showing_grid)

        if showmotor == "On":
            self.setMotorMarkerActive(True)
        else:
            self.setMotorMarkerActive(False)

    def initColorTable(self):
        self.colorTable = Colors.ColorTable()
        self.colorTable.colorChanged.connect(self._changeCurveColor)

    def initPendingActions(self):
        self.actiontimer.start(100)

    def _do_pending(self):

        #if not self.active:
        #    return

        do_replot = False

        while len(self.pending_actions):
            reason, action = self.pending_actions.pop()
            if reason == "replot":
                do_replot = action
                continue
            action()

        if do_replot:  # do a replot as last action if programmed
            do_replot()

    def setActive(self):
        self.active = True
        self.actiontimer.setInterval(PENDING_INTERVAL)

    def setInactive(self):
        self.active = False
        self.actiontimer.setInterval(PENDING_INTERVAL_INACTIVE)

    def setPlotConfig(self, plotconfig, filtername=None):
        if plotconfig is None:
            return

        mode = int(plotconfig.get("mode", 0))
        oldmode = int(self.plotconfig.get("mode", 0))

        flag = mode & PL_FULL_RANGE
        self.setFullXRange(flag)

        flag = mode & PL_GRID
        oldflag = oldmode & PL_GRID

        if flag != oldflag:
            if flag:
                self.showGrid(True)
            else:
                self.showGrid(False)

        flag = mode & PL_YLOG
        oldflag = oldmode & PL_YLOG

        if flag != oldflag:
            self.setY1Log(flag and True or False)

        flag = mode & PL_NO_DOTS
        oldflag = oldmode & PL_NO_DOTS

        if flag != oldflag:
            if flag:
                self.setUseDots(False)
            else:
                self.setUseDots(True)

        flag = mode & PL_NO_LINES
        oldflag = oldmode & PL_NO_LINES

        if flag != oldflag:
            if flag:
                self.setUseLines(False)
            else:
                self.setUseLines(True)

        linewid = plotconfig.get("linewid", None)
        oldlinewid = self.plotconfig.get("linewid", None)

        if linewid is not None and linewid != oldlinewid:
            self.setLineThickness(linewid)

        if filtername is not None:
            dotsize = plotconfig.get("%s-dotsize" % filtername, None)
        if dotsize is None:
            dotsize = plotconfig.get("dotsize", None)

        olddotsize = self.plotconfig.get("dotsize", None)

        if dotsize is not None and dotsize != olddotsize:
            self.setDotSize(dotsize)

        self.redrawCurves()
        self.plotconfig = plotconfig

    def setActiveCurve(self, curve):
        self.curve_selected = curve

    def selectCounter(self, cnt):
        curve = None
        if cnt in self.curves.keys():
            curve = self.curves[cnt]

        if curve is self.curve_selected:
            return

        if curve is not None:
            if self.curve_selected is not None:
                self.curve_selected.deselect()
            curve.select()
            self.curve_selected = curve

    def setFullXRange(self, flag):
        if flag:
            self.full_xrange = True
        else:
            self.full_xrange = False
        self._doSetAxisLimits()
        self.queue_replot()

    def setPlotRange(self, p1, p2, p3, p4):
        if p1 == "auto" and p2 == "auto":
            self.x_range_set = False
            self.x_range_beg = None
            self.x_range_end = None
        else:
            if p1 != "auto":
                self.x_range_beg = float(p1)
            else:
                self.x_range_beg = None

            if p2 != "auto":
                self.x_range_end = float(p2)
            else:
                self.x_range_end = None

            self.x_range_set = True

        if p3 == "auto" and p4 == "auto":
            self.y_range_set = False
        else:
            if p3 != "auto":
                self.y_range_beg = float(p3)
            else:
                self.y_range_beg = None

            if p4 != "auto":
                self.y_range_end = float(p4)
            else:
                self.y_range_end = None

            self.y_range_set = True

        self._doSetAxisLimits()
        self.queue_replot()

    def setDots(self, flag, size):
        self.setUseDots(flag)
        if flag:
            self.setDotSize(size)

    def setUseDots(self, flag):
        self.usedots = eval(str(flag))
        self.prefs.setValue('usedots', self.usedots)

        for curve in self.curves.values():
            curve.setUseDots(flag)

    def setDotSize(self, dotsize):
        minsize = PlotDefaults['mindotsize']
        maxsize = PlotDefaults['maxdotsize']
        dotsize = int(dotsize)

        if dotsize >= minsize and dotsize <= maxsize:
            self.dotsize = dotsize
        self.prefs.setValue('dotsize', self.dotsize)

        for curve in self.curves.values():
            curve.setDotSize(self.dotsize)

    def setLines(self, flag, thickness):
        self.setUseLines(flag)
        if flag:
            self.setLineThickness(thickness)

    def setUseLines(self, flag):
        self.uselines = eval(str(flag))
        self.prefs.setValue('uselines', self.uselines)
        for curve in self.curves.values():
            curve.setUseLines(flag)

    def setLineThickness(self, linethick):
        minthick = PlotDefaults['minlinethick']
        maxthick = PlotDefaults['maxlinethick']

        linethick = int(linethick)
        if linethick >= minthick and linethick <= maxthick:
            self.linethick = linethick

        self.prefs.setValue('linethick', self.linethick)

        for curve in self.curves.values():
            curve.setLineThickness(self.linethick)

    def showErrorBars(self, flag):
        self.showbars = eval(str(flag))
        self.prefs.setValue('showbars', self.showbars)
        for curve in self.curves.values():
            curve.showErrorBars(flag)

    def setLegend(self, show, position):
        self.setShowLegend(show)
        if show:
            self.setLegendPosition(position)

    def setShowLegend(self, flag):
        self.showlegend = eval(str(flag))
        self.prefs.setValue('showlegend',self.showlegend)
        self._setShowLegend()

    def setLegendPosition(self, legendpos):
        legendpos = str(legendpos)

        if legendpos in LegendPositions:
            self.legend_position = legendpos

        self.prefs.setValue('legendpos',self.legend_position)
        self._setLegendPosition()

    def _setShowLegend(self):
        pass

    def _setLegendPosition(self):
        pass

    def setShowPoints(self, nbpts):
        self.prefs['showpts'] = nbpts
        self.showpts = nbpts

    def queue_replot(self):
        self.queue_action("replot", self.replot)

    def queue_action(self, name, action):
        self.pending_actions.add((name, action))

    def replot(self):
        pass

    # BEGIN - Actions and Menu
    def setPlotDefaults(self):
        self.setDots(PlotDefaults['usedots'], PlotDefaults['dotsize'])
        self.setLines(PlotDefaults['uselines'], PlotDefaults['linethick'])
        self.showErrorBars(PlotDefaults['showbars'])
        self.setLegend(PlotDefaults['showlegend'], PlotDefaults['legendpos'])
        self.redrawCurves()

    def showPlotOptionDialog(self):
        if self.options_dialog is None:
            diag = PlotOptionsDialog(self)
        else:
            diag = self.options_dialog
        diag.show()

    # END - Actions and Menu

    def setDataBlock(self, datablock):
        self.datablock = datablock
        self.datablock.subscribe(self,NEW_SCAN, self.newScan)

    def _dataChanged(self):
        self.fillData()
        self.queue_replot()

    def setDataStatus(self, status):
        if status != self.status:
            self.status = status
            self._doSetAxisLimits()
            self.queue_replot()

    def setAxisTitles(self, xtitle=None, y1title=None, y2title=None, resetdefault=False):

        if xtitle is None and y1title is None and y2title is None:
            resetdefault = True

        if resetdefault:
            self.xtitle = None
            self.y1title = None
            self.y2title = None
        else:
            if xtitle is not None:
                self.xtitle = xtitle
            if y1title is not None:
                self.y1title = y1title
            if y2title is not None:
                self.y2title = y2title

        self._updateAxisTitles()

    def _updateAxisTitles(self):
        self._updateXTitle()
        self._updateY1Title()
        self._updateY2Title()
        self._updateTitles()

    def _updateXTitle(self):
        if self.xtitle is not None:
            self.xlabel = self.xtitle
        else:
            self.xlabel = self.first_x or "Point no."

    def _updateY1Title(self):
        if self.y1title is not None:
            self.y1label = self.y1title
        else:
            self.y1label = " ".join(self.y1s)

    def _updateY2Title(self):
        if self.y2title is not None:
            self.y2label = self.y2title
        else:
            self.y2label = " ".join(self.y2s)

    def _updateTitles(self):
        # STUB. to be filled by each toolkit plot implementation
        pass

    def updatePlotData(self):
        self.queue_action("updatePlotData", self._updatePlotData)

    def _updatePlotData(self):

        if not self.datablock:
            return

        dstat = self.status
        self.fillData()

        #if self.plotMode is PlotMeshMode:
            #self.fillData()
            ## self.fillMeshData()
        #elif self.plotMode is PlotTimeMode:
            #if self.status == DATA_LIVE:
                #self.fillTimeData()
            #else:
                #self.fillData()
        #else:
            #self.fillData()

        self._doSetAxisLimits()
        self.queue_replot()

    def fillData(self):
        for colname in (self.y1s + self.y2s):
            curve = self.curves[colname]
            curve.setHiddenPoints([])

            if self.plotMode is PlotMeshMode:
                xcolname, xdata, ycolname, ydata = self.datablock.getXYDataSliceForColumn(colname)
            else:
                xcolname, xdata, ycolname, ydata = self.datablock.getXYDataForColumn(colname)

            if xdata is None or not xdata.any():
                curve.clearCurve()
                continue

            config = self.datablock.getDataConfig(colname)
            if config: 
                curve.setConfig(config)

            ydata = self.filterLog(colname, ydata, curve)
            self.fillCurveData(curve,xdata,ydata)

    def fillCurveData(self, curve, xdata, ydata):
        if self.plotMode is PlotTimeMode:
            nbpts = len(xdata)
            if nbpts > self.showpts:
                xdata = xdata[-self.showpts:]
            ydata = ydata[-self.showpts:]
        #elif self.plotMode is PlotMeshMode:
            #self.slice_info = self.datablock.getSliceInfo()
            #self.nb_slices = len(self.slice_info)
            #fidx, lidx = self.slice_info[self.slice_selected]
            #xdata = xdata[fidx:]
            #ydata = ydata[fidx:]

        curve.setData(xdata,ydata)

    def fillData0(self):
        # fill data for curves for every y
        for colname in (self.y1s + self.y2s):
            curve = self.curves[colname]
            curve.setHiddenPoints([])

            
            try:
                xcolname, xdata, ycolname, ydata = self.datablock.getXYDataForColumn(colname)

                if not xdata.any():
                    curve.clearCurve()
                else:
                    ydata = self.filterLog(colname, ydata, curve)
                    curve.setData(xdata, ydata)

                config = self.datablock.getDataConfig(colname)
                if config: 
                    curve.setConfig(config)
            except:
                log.log(3,"cannot feed data to curve")
                pass

    def fillTimeData(self):
        showpts = self.showpts

        # fill data for curves for every y
        for colname in (self.y1s + self.y2s):
            curve = self.curves[colname]
            curve.setHiddenPoints([])
            xcolname, xdata, ycolname, ydata = self.datablock.getXYDataForColumn(colname)
            ydata = self.filterLog(colname, ydata)

            nbpts = len(xdata)
            if nbpts > showpts:
                xdata = xdata[-showpts:]
            ydata = ydata[-showpts:]

            curve.setData(xdata, ydata)

    def fillMeshData(self):
        log.log(3,"TODO.  fillMeshData")

    def filterLog(self, colname, data, curve=None):
        # if in log mode. make sure ydata has no negs or 0 values
        # set all 0 or nega values equal to the minimum positive

        if self.y1log and (colname in self.y1s):
            dofilter = True
        elif self.y2log and (colname in self.y2s):
            dofilter = True
        else:
            dofilter = False

        if len(data) == 0:
            dofilter = False

        #if dofilter:
        if False:
            if curve:
                dataidx = np.array(range(len(data)))
                hidden_indexes = dataidx[data <= 0].tolist()
                curve.setHiddenPoints(hidden_indexes)
            logdata = copy.copy(data[:])
            logdata[logdata <= 0] = np.amin(logdata[logdata > 0])
            return logdata
        else:
            return data

    def redrawAxes(self):
        #log.log(3,"TODO.  redrawAxes")
        pass

    def updateColumnSelection(self):
        self.x = self.datablock.getXSelection()
        self.y1s = self.datablock.getY1Selection()
        self.y2s = self.datablock.getY2Selection()
        self._columnSelectionChanged(self.x, self.y1s, self.y2s)

    def _columnSelectionChanged(self, xsel, y1sel, y2sel):
        self.x = xsel
        if len(self.x) > 0:
            self.first_x = self.x[0]
        else:
            self.first_x = None
        self.y1s = y1sel
        self.y2s = y2sel

        self._updateColumnSelection()
        self._updateAxisTitles()
        self._doSetAxisLimits()

        self.fillData()
        self.queue_replot()

    def _updateColumnSelection(self):
        
        configuration = [self.usingY1(), self.usingY2()]

        for ycolname in self.curves:
            if ycolname not in self.y1s and ycolname not in self.y2s:
                self._hideCurve(ycolname)

        for ycolname in self.y1s:
            if ycolname not in self.curves:
                self.addCurve(ycolname)
            self._showCurve(ycolname, axis=Y1_AXIS)

        if self.y1s:
            self._useY1Axis(True)
        else:
            self._useY1Axis(False)

        if not self.y2s:
            self._useY2Axis(False)
        else:
            self._useY2Axis(True)
            for ycolname in self.y2s:
                if ycolname not in self.curves:
                    self.addCurve(ycolname)
                self._showCurve(ycolname, axis=Y2_AXIS)

        new_configuration = [self.usingY1(), self.usingY2()]
        if configuration != new_configuration:
            self.emit_configuration_changed()

        self.zoomer.setZoomBase()

    def emit_configuration_changed(self):
        pass

    #  BEGIN.  Prepare scan modes
    def newScan(self, scanobj):
        self.scanObj = scanobj
        self.choosePlotMode()

    def choosePlotMode(self):

        if not self.scanObj:
            return

        if self.scanObj.isTimeScan():
            self.setTimeMode()
        elif self.scanObj.isMesh():
            motors = self.scanObj.getMotors()
            if len(motors) < 2:
                log.log(3," not enough motors")
                self.setNormalMode()
            else:
                self.setMeshMode()
        else:
            self.setNormalMode()

    def setNormalMode(self):
        self.plotMode = PlotNormalMode
        self.x_range_set = False
        self.y_range_set = False
        self._doSetAxisLimits()
 
    def _updateFullRange(self):
        # decide if full range is valid
        if not self.full_xrange:
            return

        if self.first_x and self.scanObj:
            colrange = self.scanObj.getMotorRange(self.first_x)
            if colrange is not None:
                self.x_range_beg, self.x_range_end = map(float, colrange)
                self.x_range_auto = False

    def setTimeMode(self):
        self.plotMode = PlotTimeMode
        self.x_range_set = False

    def setMeshMode(self):
        self.plotMode = PlotMeshMode
        self.nb_slices = 0
        self.slice_selected = -1
 
    #  END.  Prepare scan modes

    #  BEGIN.  Canvas operations
    def showGrid(self, flag=True):
        if flag:
            self._showGrid()
            self.showing_grid = True
            self.prefs.setValue("gridmode", "On")
        else:
            self._hideGrid()
            self.showing_grid = False
            self.prefs.setValue("gridmode", "Off")

        self.queue_replot()

    def getShowGrid(self):
        return self.showing_grid

    def getXLog(self):
        return self.xlog 

    def getY1Log(self):
        return self.y1log 

    def getY2Log(self):
        return self.y2log 

    def setXLog(self, flag=True):
        self._setXLog(flag)
        self.xlog = flag
        self.queue_replot()

    def setY1Log(self, flag=True):
        self.y1log = flag
        self._setY1Log(flag)
        self.queue_replot()

    def setY2Log(self, flag=True):
        self.y2log = flag
        self._setY2Log(flag)
        self.queue_replot()

    #  END.  Canvas operations

    def usingY1(self):
        return self.using_y1

    def usingY2(self):
        return self.using_y2

    # STUBS. To be coded in specific toolkit class
    def _showCurve(self, colname, axis=Y1_AXIS):
        log.log(3,"STUB. _showCurve(). ")

    def _hideCurve(self, colname):
        log.log(3,"STUB. _hideCurve(). ")

    def _changeCurveColor(self, mne, color):
        log.log(3,"STUB. _changeCurveColor(). ")

    def _useY1Axis(self, flag=True):
        log.log(3,"STUB. _useY1Axis(). ")

    def _useY2Axis(self, flag=True):
        log.log(3,"STUB. _useY2Axis(). ")

    def _showGrid(self):
        log.log(3,"STUB. _showGrid(). ")

    def _hideGrid(self):
        log.log(3,"STUB. _hideGrid(). ")

    def _setXLog(self, flag):
        log.log(3,"STUB. _setXLog(). ")

    def _setY1Log(self, flag):
        log.log(3,"STUB. _setY1Log(). ")

    def _setY2Log(self, flag):
        log.log(3,"STUB. _setY2Log(). ")

    def _setAxisLimits(self, axis, axmin, axmax):
        log.log(3,"STUB. _setAxisLimits(). ")

    def setXAxisAuto(self):
        log.log(3,"STUB. _setXAxisAuto(). ")

    def setY1AxisAuto(self):
        log.log(3,"STUB. _setY1AxisAuto(). ")

    def setY2AxisAuto(self):
        log.log(3,"STUB. _setY2AxisAuto(). ")

    # END STUBS.

    def setAxisLimits(self):
        self._doSetAxisLimits()
        self.queue_replot()

    def isScanRunning(self):
        dstat = self.status
        return dstat == DATA_LIVE

    def _doSetAxisLimits(self):

        if not self.datablock:
            return

        dstat = self.status

        if dstat == DATA_TREND:
            xdata = self.datablock.getDataColumn(self.first_x)
            min_x = xdata.min()
            max_x = xdata.max()
            self._setAxisLimits(X_AXIS, float(min_x), float(max_x))
        else:
            self.x_range_auto = True
            if dstat == DATA_LIVE and self.full_xrange:
                self._updateFullRange()
            elif dstat == DATA_STATIC:
                if self.x_range_set:  # set by setPlotRange(). reset on new scan
                    self.x_range_auto = False

            # X
            if self.x_range_auto:
                self.setXAxisAuto()
            else:
                xbeg = self.x_range_beg
                xend = self.x_range_end
                    
                if xbeg > xend:
                    xbeg, xend = xend, xbeg
    
                if xbeg is not None and xend is not None:
                    self._setAxisLimits(X_AXIS, xbeg, xend)
    
            # Y
            if dstat == DATA_STATIC and self.y_range_set:
                self.y_range_auto = False
            else:
                self.y_range_auto = True

            if self.y_range_auto:
                self.setY1AxisAuto()
                self.setY2AxisAuto()
            else:
                ybeg = self.y_range_beg
                yend = self.y_range_end

                if ybeg is None or yend is None:
                    y1s = self.datablock.getY1Selection()
                    ymin = None
                    ymax = None
                    span = None
                    for y1 in y1s:
                        ydata = self.datablock.getDataColumn(y1)
                        if ydata.any():
                            y1min = ydata.min()
                            y1max = ydata.max()
                            if ymin is None or y1min < ymin:
                                ymin = y1min
                            if ymax is None or y1max < ymax:
                                ymax = y1max

                    if ymin is not None and ymax is not None:
                        span = ymax - ymin

                    if ybeg is None:
                        if span is not None:
                            ybeg = 0.95 * ymin

                    if yend is None:
                        if span is not None:
                            yend = 1.05 * ymax

                if ybeg is not None and yend is not None:
                    self._setAxisLimits(Y1_AXIS, ybeg, yend)
                    self._setAxisLimits(Y2_AXIS, ybeg, yend)

        self.setZoomBase()
        self.redrawAxes()
        
        self.queue_replot()

    def initMarkers(self):
        # Declare markers
        self.linePeak = self.addVerticalMarker("PEAK", persistent=True)
        self.lineCOM = self.addVerticalMarker("COM", persistent=True)
        self.lineCFWHM = self.addVerticalMarker("CFWHM", persistent=True)
        self.lineMotPos = self.addVerticalMarker("Current", persistent=True)

        self.linePeak.setShowOptions(color=self.theme.marker_color_peak, thickness=1)
        self.lineCOM.setShowOptions(color=self.theme.marker_color_com, thickness=1)
        self.lineCFWHM.setShowOptions(color=self.theme.marker_color_fwhm, thickness=1)
        self.lineMotPos.setShowOptions(color=self.theme.marker_color_motor_position, thickness=1)

        self.app_markers = ['PEAK', 'COM', 'CFWHM', 'MotPos']

        self.markers['PEAK'] = self.linePeak
        self.markers['COM'] = self.lineCOM
        self.markers['CFWHM'] = self.lineCFWHM
        self.markers['MotPos'] = self.lineMotPos

        self.marker_nb = 0    # to be used to create hidden marker labels


    def addVerticalMarker(self, label, **kwargs):
        # STUB. to be implemented in child class
        return None

    def addMarker(self, label, posinfo, persistent=False, options=None):

        if label is None:
            self.marker_nb += 1
            label_idx = "_marker_%d" % self.marker_nb
        else:
            label_idx = label

        if label_idx.startswith("_"):
            showlabel = False
        else:
            showlabel = True

        if len(posinfo) == 1:
            marker_type = MARKER_VERTICAL
        elif len(posinfo) == 2:
            marker_type = MARKER_TEXT
        else:
            marker_type = MARKER_SEGMENT

        size = 1
        if options is None:
            color = self.colorTable.getColor(label_idx)
        else:
            opts = options.split(",")
            color = opts[0]
            if len(opts) > 1:
                size = float(opts[1])

        marker = None

        if label in self.markers:
            marker = self.markers[label_idx]
            if marker.getMarkerType() != marker_type:
                self.removeMarker(label)
                marker = None

        if marker is None:
            if marker_type == MARKER_VERTICAL:
                marker = self.addVerticalMarker(
                    label_idx, persistent=persistent, showlabel=showlabel)
                marker.position = len(self.markers) - 4
            elif marker_type == MARKER_TEXT:
                marker = self.addTextMarker(label_idx, persistent=persistent, showlabel=showlabel)
            else:
                marker = self.addSegmentMarker(label_idx, persistent=persistent, showlabel=showlabel)

            self.markers[label_idx] = marker

        marker.setCoordinates(posinfo)
        marker.setShowOptions(color, size)
        marker.attach(self)

        self.queue_replot()
        return label_idx

    def removeMarker(self, label):
        if label in self.markers:
            marker = self.markers[label]
            marker.detach()
            self.queue_replot()
            self.markers.pop(label)


    def getMarkers(self):
        marker_list = []
        for label in self.markers:
            marker = self.markers[label]
            position = marker.getXValue()
            if position is not None:
                marker_list.append(
                    [label, marker.getMarkerType(), marker.getCoordinates()])
        return marker_list

    def _position_markers(self):
        # calculate where to put the labels for markers
        low, high = self.getY1ViewRange()

        if high is None or low is None:
            return

        # stats markers
        if self.showing_stats:
            onethird_up = (high - low) * 2 / 3.0 + low
            inthe_middle = (high - low) / 2.0 + low
            onethird_down = (high - low) / 3.0 + low

            self.linePeak.setLabelPosition(onethird_up)
            self.lineCFWHM.setLabelPosition(inthe_middle)
            self.lineCOM.setLabelPosition(onethird_down)

        # Motor position marker
        if self.showing_motor:
            threeway_up = (high - low) * 3 / 4.0 + low
            self.lineMotPos.setLabelPosition(threeway_up)

        # User markers
        if len(self.markers) > len(self.app_markers):
            pos1 = (high - low) / 5.0 + low
            pos2 = (high - low) * 2 / 5.0 + low
            pos3 = (high - low) * 3 / 5.0 + low
            pos4 = (high - low) * 4 / 5.0 + low
            poss = [pos1, pos2, pos3, pos4]

            markernb = 0
            for name, marker in self.markers.items():
                if name not in self.app_markers:
                    if marker.getMarkerType() == MARKER_VERTICAL:
                        mpos = poss[markernb % 4]
                        marker.setLabelPosition(mpos)
                        markernb += 1

    def newPlot(self):
        self.purgeTemporary()

    def purgeTemporary(self):
        for name in self.markers.keys():
            marker = self.markers[name]
            if not marker.isPersistent():
                marker.detach()
                self.markers.pop(name)
        self.queue_replot()

    # BEGIN stats
    def showStats(self):
        self.linePeak.attach(self)
        self.lineCOM.attach(self)
        self.lineCFWHM.attach(self)

        self.showing_stats = True
        self.stats_hidden = False
        self.queue_replot()

    def hideStats(self, temporary=False):


        self.linePeak.detach()
        self.lineCOM.detach()
        self.lineCFWHM.detach()

        if not temporary:
            self.showing_stats = False
        self.stats_hidden = True

        self.queue_replot()

    def getShowStats(self):
        return self.showing_stats

    def _statsChanged(self, newstats):

        if not self.curve_selected:
            self.hideStats()
            return

        if not newstats or not isinstance(newstats, dict):
            self.hideStats(temporary=True)
            return

        if self.showing_stats and self.stats_hidden:
            self.showStats()

        column = newstats.get('column',None)
        stats_2d = newstats.get('2d', False)

        if column == self.curve_selected and not stats_2d:
            peak_pos = newstats['peak'][0]  # pos, peakval
            fwhm_pos = newstats['fwhm'][1]  # fwhm, center
            com_pos = newstats['com']
        
            self.lineCOM.setXValue(com_pos)
            self.lineCFWHM.setXValue(fwhm_pos)
            self.linePeak.setXValue(peak_pos)
            self.queue_replot()

    # END stats

    # BEGIN motor
    def setMotorMarkerActive(self, flag=None):
        prefname = "showmotor"

        if flag is not None:
            self.motor_marker_active = flag

        if self.motor_marker_active:
            self.prefs[prefname] = "On"
            if self.showing_motor:
                self.lineMotPos.attach(self)
        else:
            self.prefs[prefname] = "Off"
            self.lineMotPos.detach()

        self.queue_replot()

    def isShowingMotor(self): 
        return self.showing_motor and self.motor_marker_active

    def showMotorMarker(self):
        self.showing_motor = True
        if self.motor_marker_active:
            self.lineMotPos.attach(self)

    def hideMotorMarker(self):
        self.showing_motor = False
        self.lineMotPos.detach()

    def motorPositionChanged(self, motor, position):
        self.lineMotPos.setLabel("%s (%g)" % (motor, position))
        self.lineMotPos.setXValue(position)

        if self.isShowingMotor():
            self.queue_replot()

    # END motor

    # BEGIN zoom functions
    def setZoomMode(self, mode):
        if None in [self.zoomer, self.crosshairs, self.regionzoom]:
            log.log(3,"Not all zoom objects defined for this class")
            self.zoommode = None
            return

        if mode == CROSSHAIRS_MODE:
            self.crosshairs.setEnabled(True)
            self.zoomer.setEnabled(False)
            self.regionzoom.setEnabled(False)
            self.zoommode = CROSSHAIRS_MODE
        elif mode == ZOOM_MODE:
            self.zoomer.setEnabled(True)
            self.crosshairs.setEnabled(False)
            self.regionzoom.setEnabled(False)
            self.zoommode = ZOOM_MODE
            self.zoomer.setZoomBase()
        elif mode == REGIONZOOM_MODE:
            self.regionzoom.setEnabled(True)
            self.crosshairs.setEnabled(False)
            self.zoomer.setEnabled(False)
            self.zoomer.setZoomBase()
            self.zoommode = REGIONZOOM_MODE
        else:
            pass

        self.prefs["zoommode"] = mode

    def setZoomBase(self):
        if self.zoomer is None:
            return
        self.zoomer.setZoomBase()

    def getZoomLimits(self, axis):
        if self.zoomer is None:
            return
        return self.zoomer.getZoomLimits(axis)

    def isZoomed(self):
        if self.zoomer is None:
            return
        return (self.zoomer.zoomRectIndex() > 0)

    def setRange(self, xbeg, xend):

        if self.datablock:
            self.datablock.setRange(xbeg, xend)
            self.regionSelection(xbeg, xend)

            if self.parent:
                self.parent.updatePlotData()
            else:
                self.updatePlotData()

    def setInterval(self, ptival):

        if self.zoomer is not None:
            self.zoomer.resetZoom()

        if self.datablock:
            self.datablock.setInterval(ptival)

            xbeg, xend = self.datablock.getRange()
            self.regionSelection(xbeg, xend)

            if self.parent:
                self.parent.updatePlotData()
            else:
                self.updatePlotData()

    def isReduced(self):
        return self.datablock.isReduced()

    def getRange(self):
        if self.datablock:
            return self.datablock.getRange()
        else:
            return []

    def getFullRange(self):
        return self.datablock.getFullRange()

    def resetRange(self):
        if self.datablock:
            self.datablock.resetRange()
            xbeg, xend = self.datablock.getRange()
            self.regionSelection(xbeg, xend)
            if self.parent:
                self.parent.updatePlotData()
            else:
                self.updatePlotData()

    def zoomin(self):
        if self.zoommode == REGIONZOOM_MODE :
            if self.regionzoom is not None:
                self.regionzoom.zoomin()
        elif self.zoomer is not None:
            self.zoomer.zoomin()

    def zoomout(self):
        if self.zoommode == REGIONZOOM_MODE:
            self.regionzoom.zoomout()
        else:
            self.zoomer.zoomout()

    def resetzoom(self):
        if self.zoomer is not None:
            self.zoomer.resetZoom()

        self.updatePlotData()

    def resetregion(self):
        self.resetRange()

    def updateZoomInfo(self, nb_zooms, zoomidx):
        self.zoomidx = zoomidx
        if self.parent is not None:
            self.parent.updateZoomInfo(nb_zooms, zoomidx)
        self.queue_replot()

    # END zoom modes
