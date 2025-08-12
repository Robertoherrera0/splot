#******************************************************************************
#
#  @(#)DataSource1D.py	3.5  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2019,2020,2021,2023,2024
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

import os
import sys
import copy
import weakref

from pyspec.graphics.QVariant import *
from Constants import *
from pyspec.css_logger import log
from pyspec.utils import is_windows, is_unity, is_macos

import icons

from ScanMetadataWidget import ScanMetadataWidget
from ColumnSelectionWidget import ColumnSelectionWidget
from SpecPlotWidget import SpecPlotWidget

import numpy as np
from FunctionModels import GaussianModel, LorentzianModel, LinearModel

cssname = "app.css"
cssfile = os.path.join(os.path.dirname(__file__), cssname)

from DataSource import DataSource
import DataBlock

class DataSource1D(DataSource):

    sourceActivated = pyqtSignal(object)
    configurationChanged = pyqtSignal(object)

    def __init__(self, app, sourcetype, name):


        self.columns_widget = None
        self.meta_widget = None
        self.datastatus = DATA_STATIC
        self.extra_curves = {}
        self.active_cnt = None

        sourcetype |= SOURCE_1D

        DataSource.__init__(self, app, sourcetype, name)

    def init(self):
        self.metadata = {}
        self.errorflag = None
        self.datastatus = DATA_STATIC

    def init_data(self):
        self.datablock = DataBlock.DataBlock()

    def init_graphics_area(self):
        self.plot_w = SpecPlotWidget()

        self.plot_w.setSourceType(self.getType())
        self.plot_w.setDataBlock(self.datablock)
        self.plot_w.setDataStatus(self.getStatus())

        self.plot = self.plot_w.getPlot()
        self.plot.configurationChanged.connect(self.emit_configuration_changed)

        return self.plot_w

    def init_source_area(self):
        self.show_column_selection_widget()

    def show_column_selection_widget(self, flag=True):
        self.columns_widget = ColumnSelectionWidget(self)
        self.columns_widget.setDataBlock(self.datablock)
        self.columns_widget.setColumnDataHandler(self._columnDataHandler)

        self.add_source_tab(1, self.columns_widget,  "Columns")

    def show_metadata_widget(self, flag=True):
        try:
            self.meta_widget = ScanMetadataWidget()
            self.add_source_tab(2, self.meta_widget,  "Scan Info")
        except BaseException as e:
            import traceback
            log.log(2, "error creating metadata widget " + traceback.format_exc())

    def isServer(self):
        # stubs. Always returns False. Implement in class
        return False

    def isSHM(self):
        # stubs. Always returns False. Implement in class
        return False

    def getPlot(self):
        return self.plot

    def getMeta(self):
        return self.metadata

    def getStatus(self):
        return self.datastatus

    def update_menubar(self, menubar_set):
        menubar_set.dataMenu.menuAction().setEnabled(False)
        menubar_set.plotMenu.menuAction().setEnabled(True)
        menubar_set.mathMenu.menuAction().setEnabled(True)

        plot = self.plot

        if plot.getXLog():
            actlab = "X axis. Linear scale"
            tiplab = "Set linear scale for X"
        else:
            actlab = "X axis. Log scale"
            tiplab = "Set log scale for X"
        menubar_set.setlogxAction.setText(actlab)
        menubar_set.setlogxAction.setStatusTip(tiplab)

        # y1 action
        if plot.usingY1():
            menubar_set.setlogy1Action.setEnabled(True)
        else:
            menubar_set.setlogy1Action.setEnabled(False)

        if plot.getY1Log():
            actlab = "Y &Left Axis Linear scale"
            tiplab = "Set linear scale for Y Left"
        else:
            actlab = "Y &Left Axis Log scale"
            tiplab = "Set log scale for Y Left"
        menubar_set.setlogy1Action.setText(actlab)
        menubar_set.setlogy1Action.setStatusTip(tiplab)

        if plot.usingY2():
            menubar_set.setlogy2Action.setEnabled(True)
        else:
            menubar_set.setlogy2Action.setEnabled(False)

        if plot.getY2Log():
            actlab = "Y &Right Axis Linear scale"
            tiplab = "Set linear scale for Y Right"
        else:
            actlab = "Y &Right Axis Log scale"
            tiplab = "Set log scale for Y Right"
        menubar_set.setlogy2Action.setText(actlab)
        menubar_set.setlogy2Action.setStatusTip(tiplab)

        if plot.getShowGrid():
            actlab = "Hide &Grid"
            tiplab = "Hide Grid from plot"
        else:
            actlab = "Show &Grid"
            tiplab = "Show Grid on plot"

        menubar_set.gridAction.setText(actlab)
        menubar_set.gridAction.setStatusTip(tiplab)

        if plot.getShowStats():
            menubar_set.showStatsAction.setText("Hide &Stats on Plot")
            menubar_set.showStatsAction.setStatusTip("Hide Stats on Plot")
        else:
            menubar_set.showStatsAction.setText("Show &Stats on Plot")
            menubar_set.showStatsAction.setStatusTip("Show Stats on Plot")

        if self.isServer():
            menubar_set.showMotorAction.setEnabled(True)

            if plot.isShowingMotor():
                actlab = "Hide &Motor on plot"
                tiplab = "Hide Motor on plot"
            else:
                actlab = "Show &Motor on plot"
                tiplab = "Show Motor on plot"

            menubar_set.showMotorAction.setText(actlab)
            menubar_set.showMotorAction.setStatusTip(tiplab)
        else:
            menubar_set.showMotorAction.setEnabled(False)


    # Plot commands
    def setPlotXLog(self,flag=True):
        self.plot.setXLog(flag)
        self.emit_configuration_changed()

    def setPlotY1Log(self,flag=True):
        self.plot.setY1Log(flag)
        self.emit_configuration_changed()

    def setPlotY2Log(self,flag=True):
        self.plot.setY2Log(flag)
        self.emit_configuration_changed()
    
    def setShowMotorOnPlot(self, flag=True):
        self.plot.setMotorMarkerActive(flag)
        self.emit_configuration_changed()

    def togglePlotGrid(self):
        mode = not self.plot.getShowGrid()
        self.showPlotGrid(mode)

    def showPlotGrid(self, mode):
        self.plot.showGrid(mode)
        self._updateShowPlotGrid()
        self.emit_configuration_changed()

    def toggleXLog(self):
        self.setPlotXLog(not self.plot.getXLog() )

    def toggleY1Log(self):
        self.setPlotY1Log(not self.plot.getY1Log() )
        self.emit_configuration_changed()

    def toggleY2Log(self):
        self.setPlotY2Log(not self.plot.getY2Log() )
        self.emit_configuration_changed()

    def toggleShowMotor(self):
        self.setShowMotorOnPlot(not self.plot.isShowingMotor())
        self.emit_configuration_changed()

    def showPlotOptionDialog(self):
        self.plot.showPlotOptionDialog()

    def _updateShowPlotGrid(self):
        showing = self.plot.getShowGrid()
        self.prefs.setValue("gridmode", "On" if showing else "Off")

    # End Plot commands

    def check_preferences(self):

        if self.prefs.getValue("trackstats","Off") == 'On':
            self.showStatsOnPlot(True)
        else:
            self.showStatsOnPlot(False)

        if self.prefs.getValue("gridmode","Off") == "On":
            self.showPlotGrid(True)
        else:
            self.showPlotGrid(False)


    # Math commands
    def toggleStatsOnPlot(self):
        doshow = not self.plot.getShowStats()
        self.showStatsOnPlot(doshow)

    def showStatsOnPlot(self, doshow=None):
        if doshow:
            self.plot.showStats()
        else:
            self.plot.hideStats()
        self._updatePlotStatsMenu()
        self.emit_configuration_changed()

    def _updatePlotStatsMenu(self):
        showing = self.plot.getShowStats()
        self.prefs.setValue("trackstats", "On" if showing else "Off")

    # End Math commands

    def _columnDataHandler(self, data):
        data['isfit'] = False
        data['source'] = self.getDescription()
        data['description'] = self.getDescription() +  ":" + data['colname']
        self.app.requestAddCurve(data)
       
    def addExtraCurve(self, curve, options):
        self.datablock.addExtraData(curve,options)

    def setXSelection(self, xcols, override_default=False):
        self.datablock.setXSelection(xcols, override_default)

    def setYSelection(self, y1s, y2s, override_default=False):
        self.datablock.setY1Selection(y1s, override_default)
        self.datablock.setY2Selection(y2s, override_default)
        
    def setY1Selection(self, y1s, override_default=False):
        self.datablock.setY1Selection(y1s, override_default)
        
    def setY2Selection(self, y2s, override_default=False):
        self.datablock.setY2Selection(y1s, override_default)
 
    def setScanObject(self, scanobj):
        self.scanobj = scanobj
        self.datablock.setScanObject(scanobj)
        self.datablock.setSourceDescription(self.getDescription())

    def emit_configuration_changed(self):
        self.configurationChanged.emit(self)

    def setData(self, data, columnnames=None, metadata=None):
        self.datablock.update(data, columnnames, metadata)
        self.updateDataInfo()
        self.emit_configuration_changed()

    def setColumnNames(self, columnnames):
        self.datablock.setColumnNames(columnnames)

    def getColumnNames(self):
        return self.datablock.getColumnNames()

    def updateDataInfo(self):
        if not self.meta_widget:
            return

        self.meta_widget.setMetadata(self.metadata)

        if "errors" in self.metadata and self.metadata["errors"]:
            self.setErrorFlag(True)
        else:
            self.setErrorFlag(False)

    def setErrorFlag(self, flag):
        # return
        idx = self.tabs.indexOf(self.meta_widget)
        curidx = self.tabs.currentIndex()

        if flag != self.errorflag:
            self.tabs.removeTab(idx)
            if flag and not self.errorflag:
                self.tabs.insertTab(idx, self.meta_widget, icons.get_icon('attention'), "Scan Info")
            else:
                self.tabs.insertTab(idx, self.meta_widget, "Scan Info")

            if curidx == idx:
                self.tabs.setCurrentIndex(idx)

        self.errorflag = flag

    def resetAll(self):
        log.debug("RESET")

    def resetData(self):
        self.datablock.resetData()
        #self.updatePlot()

    def setTrendPoints(self, nbpts):
        self.prefs.setValue('showpts', nbpts)

    def pointSelection(self, xlabel, xpos):
        pass

    def regionSelection(self, xlabel, x1, x2):
        pass

    def gaussianFit(self):
        self.datablock.doFit(model=GaussianModel())

    def lorentzFit(self):
        self.datablock.doFit(model=LorentzianModel())

    def lineFit(self):
        self.datablock.doFit(model=LinearModel())

    def selectCounter(self, counter):
        self.active_cnt = counter
        self.plot_w.selectCounter(counter)

    def selectScan(self, scanno):
        pass

    def next(self):
        pass

    def prev(self):
        pass

def main_test():
    app = QApplication([])
    win = QMainWindow()
    wid = DataSource1D(None, SOURCE_ANY, "Test")
    win.setWindowTitle('Data Source dumb test')

    win.setCentralWidget(wid)
    win.setGeometry(200, 100, 400, 400)
    win.show()

    try:
        sys.exit(app.exec_())
    except AttributeError:
        exec_ = getattr(app, "exec")
        sys.exit(exec_())

if __name__ == '__main__':
    main_test()

