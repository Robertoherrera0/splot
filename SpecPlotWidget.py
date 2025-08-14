#******************************************************************************
#
#  @(#)SpecPlotWidget.py	3.12  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024
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
import copy
import weakref

from pyspec.graphics.QVariant import (Qt,
                                      QSize,
                                      QAction,
                                      pyqtSignal,
                                      QTimer, 
                                      QSizePolicy,
                                      QPrinter,
                                      QWidget,
                                      QVBoxLayout,
                                      QHBoxLayout,
                                      QComboBox,
                                      QLabel,
                                      QPushButton,
                                      QToolBar,
                                      QApplication,
                                      QMainWindow)

from pyspec.graphics import mpl_imported, qt_variant
from pyspec.css_logger import log

from Constants import *
import icons

from Preferences import Preferences

from NavigateListWidget import NavigateListWidget


from Features import haveFeature, setFeature

from SpecPlot import SpecPlot
from DialogTools import getPrinter, getSaveFile
from PlotHeader import PlotHeader

if mpl_imported():  
    try:
        from SpecPlot2D import SpecPlot2D
    except:
        log.log(3,"Plot2d is not available")
        setFeature("2D", False)
else:
    log.log(3,"matplotlib can not be imported")
    setFeature("2D", False)
 

# Orientation = [QPrinter.Portrait, QPrinter.Landscape]

"""
PaperSize = {
    'A0':	QPrinter.A0,
    'A1':	QPrinter.A1,
    'A2':	QPrinter.A2,
    'A3':	QPrinter.A3,
    'A4':	QPrinter.A4,
    'A5':	QPrinter.A5,
    'A6':	QPrinter.A6,
    'A7':	QPrinter.A7,
    'A8':	QPrinter.A8,
    'A9':	QPrinter.A9,
    'B0':	QPrinter.B0,
    'B1':	QPrinter.B1,
    'B2':	QPrinter.B2,
    'B3':	QPrinter.B3,
    'B4':	QPrinter.B4,
    'B5':	QPrinter.B5,
    'B6':	QPrinter.B6,
    'B7':	QPrinter.B7,
    'B8':	QPrinter.B8,
    'B9':	QPrinter.B9,
    'B10':	QPrinter.B10,
    'C5E':	QPrinter.C5E,
    'Comm10E':	QPrinter.Comm10E,
    'DLE':	QPrinter.DLE,
    'Executive':	QPrinter.Executive,
    'Folio':	QPrinter.Folio,
    'Ledger':	QPrinter.Ledger,
    'Legal':	QPrinter.Legal,
    'Letter':	QPrinter.Letter,
    'Tabloid':	QPrinter.Tabloid,
    'Custom':	QPrinter.Custom,
}
"""

class SpecPlotWidget(QWidget):

    statsUpdated = pyqtSignal(object,object,object,object,object,object)

    def __init__(self, *args):

        self.status = None
        self.registered = 0

        self.sourcetype = None
        self.server_mode = None
        self.abort_action = None

        self.title = None

        self.datablock = None
        self.scanobj = None

        QWidget.__init__(self, *args)

        self.prefs = Preferences()

        layout = QVBoxLayout()
        toolLayout = QHBoxLayout()
        topLayout = QHBoxLayout()
        topLayout.setAlignment(Qt.AlignBottom)

        bottomLayout = QHBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        toolLayout.setContentsMargins(0, 0, 0, 0)
        topLayout.setContentsMargins(0, 0, 0, 0)
        topLayout.setSpacing(0)
        bottomLayout.setContentsMargins(0, 0, 0, 0)
        bottomLayout.setSpacing(0)

        self.setLayout(layout)
        layout.addLayout(toolLayout)
        layout.addLayout(topLayout)
        layout.addLayout(bottomLayout)

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(18, 18))
        #self.toolbar.setStyleSheet('border-style: solid; border-width: 1px; border-radius: 5px;')

        icondir = os.path.join(os.path.dirname(__file__),'icons')

        self.selectModeAction = QAction(icons.get_icon('pointer'), "Crosshairs", self)
        self.selectModeAction.triggered.connect(self.selectMode)
        self.selectModeAction.setCheckable(True)

        self.regionModeAction = QAction(icons.get_icon('regionin'), "Region", self)
        self.regionModeAction.triggered.connect(self.regionMode)
        self.regionModeAction.setCheckable(True)

        self.regionOutAction = QAction(icons.get_icon('regionout'), "Reset Region", self)
        self.regionOutAction.triggered.connect(self.regionReset)
        self.regionOutAction.setCheckable(False)
        self.regionOutAction.setEnabled(False)

        self.zoomModeAction = QAction(icons.get_icon('zoom'), "Zoom Out", self)
        self.zoomModeAction.triggered.connect(self.zoomMode)
        self.zoomModeAction.setCheckable(True)

        self.zoomoutAction = QAction(icons.get_icon('zoomout'), "Zoom-", self)
        self.zoomoutAction.setStatusTip('Zoom Out Plot')
        self.zoomoutAction.triggered.connect(self.zoomOut)
        self.zoomoutAction.setEnabled(False)

        self.zoominAction = QAction(icons.get_icon('zoomin'), "Zoom+", self)
        self.zoominAction.setStatusTip('Zoom In Plot')
        self.zoominAction.triggered.connect(self.zoomIn)
        self.zoominAction.setEnabled(False)

        self.printAction = QAction(icons.get_icon('printer'), "Print", self)
        self.printAction.setStatusTip('Print Plot')
        self.printAction.triggered.connect(self.printPlot)

        self.toolbar.addAction(self.selectModeAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.regionModeAction)
        self.toolbar.addAction(self.regionOutAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.zoomModeAction)
        self.toolbar.addAction(self.zoomoutAction)
        self.toolbar.addAction(self.zoominAction)
        #self.toolbar.addAction(self.zoomresetAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.printAction)

        self.toolbar.addSeparator()

        self.spacer = QWidget()
        if qt_variant() in ["PyQt6", "PySide6"]:
            from pyspec.graphics.QVariant import QSizePolicy_
            spol = QSizePolicy_()
        else:
            spol = QSizePolicy()
        spol.setHorizontalPolicy(QSizePolicy.Expanding)
        self.spacer.setSizePolicy(spol)
        self.toolbar.addWidget(self.spacer)

        self.sourceNameLabel = QLabel("Source: ")
        self.sourceNameLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.sourceNameValue = QLabel("")
        self.sourceNameValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sourceNameValue.setObjectName("sourcename")

        self.serverStateLabel = QLabel("")
        try:
            self.serverStateLabel.setAlignment(Qt.AlignCenter)
        except AttributeError:
            self.serverStateLabel.setAlignment(Qt.AlignHCenter)
        self.serverStateLabel.setFixedWidth(90)
        self.serverStateLabel.setObjectName("sourcestate")

        icondir = os.path.join(os.path.dirname(__file__),'icons')

        self.abortActiveIcon = icons.get_icon('stop_red')
        self.abortGreyIcon = icons.get_icon('stop_grey')

        self.abortButton = QPushButton(self.abortGreyIcon, "")
        self.abortButton.setEnabled(False)
        self.abortButton.setObjectName("abortbutton")

        self.abortButton.setFixedWidth(60)
        self.abortButton.setFixedHeight(32)

        self.abortButton.clicked.connect(self.abort)

        self.sourceLabelAction = self.toolbar.addWidget(self.sourceNameLabel)
        self.sourceNameAction = self.toolbar.addWidget(self.sourceNameValue)
        self.serverStateAction = self.toolbar.addWidget(self.serverStateLabel)
        self.abortButtonAction = self.toolbar.addWidget(self.abortButton)

        self.sourceLabelAction.setVisible(False)
        self.sourceNameAction.setVisible(False)
        self.serverStateAction.setVisible(False)
        self.abortButtonAction.setVisible(False)

        self.plotHeader = PlotHeader()
        self.mode2d_widget = QWidget()
        self.mode2d_layout = QHBoxLayout()
        self.mode2d_label = QLabel("2D Mode:")
        self.mode2d_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.mode2d_combo = QComboBox()

        if haveFeature("2D_triangles"):
            modes_2d = ['Scatter','Contour', 'Triangles','Image']
        else:
            modes_2d = ['Scatter','Contour', 'Image']

        self.mode2d_combo.addItems(modes_2d)
        mode2d = self.prefs.getValue("style_2d", "scatter").capitalize()

        if mode2d.capitalize() in modes_2d: 
             idx = modes_2d.index(mode2d)
             self.mode2d_combo.setCurrentIndex(idx)

        self.mode2d_combo.currentIndexChanged.connect(self.set2DStyle)

        self.mode2d_widget.setLayout(self.mode2d_layout)
        self.mode2d_layout.addWidget(self.mode2d_label)
        self.mode2d_layout.addWidget(self.mode2d_combo)

        self.slice_widget = NavigateListWidget("Slice:")
        self.slice_widget.valueChanged.connect(self.selectedSliceChanged)

        self.plot = SpecPlot(self)

        if haveFeature("2D"):
            self.plot2d = SpecPlot2D(self)
        else:
            self.plot2d = None

        self.plotmode = None

        titleLabel = QLabel()
        font = titleLabel.font()
        font.setBold(True)
        titleLabel.setFont(font)

        spacer = QWidget()
        spacer.setMinimumWidth(30)
        spacer.setMaximumWidth(30)

        toolLayout.addWidget(self.toolbar)
        topLayout.addWidget(spacer)
        # topLayout.addWidget(self.plotHeader, 2, Qt.AlignLeft)
        topLayout.addWidget(self.plotHeader, 0, Qt.AlignHCenter)


        if haveFeature("2D"):
            topLayout.addWidget(self.mode2d_widget, 1, Qt.AlignRight | Qt.AlignBottom)

        topLayout.addWidget(self.slice_widget, 1, Qt.AlignRight | Qt.AlignBottom)

        if self.plot.legendY1:
            bottomLayout.addWidget(self.plot.legendY1)

        bottomLayout.addWidget(self.plot)

        if haveFeature("2D"):
            bottomLayout.addWidget(self.plot2d)

        if self.plot.legendY2:
            bottomLayout.addWidget(self.plot.legendY2)

        zoommode = self.prefs.getValue("zoommode", ZOOM_MODE)

        if zoommode not in [ZOOM_MODE, REGIONZOOM_MODE, CROSSHAIRS_MODE]:
            zoommode = ZOOM_MODE

        self.setPlotMode(PLOT_1D)
        self.setZoomMode(zoommode)

    def setTitle(self, title=None):
        if title:
            self.sourceNameValue.setText(title)
            self.sourceLabelAction.setVisible(True)
            self.sourceNameAction.setVisible(True)
        else:
            self.sourceNameAction.setVisible(False)
            self.sourceLabelAction.setVisible(False)

    def setSourceType(self, sourcetype): 
        self.sourcetype = sourcetype

    def showSourceStatus(self):
        if self.sourcetype & SOURCE_SPEC:
            self.serverStateAction.setVisible(True)

    def setDataBlock(self, datablock):

        self.plotHeader.setDataBlock(datablock)
        self.plot.setDataBlock(datablock)

        if haveFeature("2D"):
            self.plot2d.setDataBlock(datablock)

        if datablock is None:  return

        if datablock is self.datablock:
            return

        if self.datablock:
            self.datablock.unsubscribe(self)

        # Connect with changes on associated datablock

        self.datablock = datablock
        self.datablock.subscribe(self, DATA_CHANGED, self.dataChanged)
        self.datablock.subscribe(self, STATS_UPDATED, self.statsChanged)
        self.datablock.subscribe(self, ACTIVECOLUMN_CHANGED, self.setActiveCurve)
        self.datablock.subscribe(self, SELECTION_CHANGED, self.columnSelectionChanged)
        self.datablock.subscribe(self, SLICES_CHANGED, self.slicesChanged)
        self.datablock.subscribe(self, NEW_SCAN, self.newScan)

    def dataChanged(self):
        if not haveFeature("2D") or self.plotmode == PLOT_1D:
           self.plot._dataChanged()
        elif self.plotmode == PLOT_2D:
           self.plot2d._dataChanged()

    def statsChanged(self, stats):
        self.plot._statsChanged(stats)

    def setActive(self):
        self.plot.setActive()

    def setInactive(self):
        self.plot.setInactive()

    def setActiveCurve(self, curve):
        self.plot.setActiveCurve(curve)

    def columnSelectionChanged(self, xsel, y1sel, y2sel):

        if len(xsel) > 1: 
            self.setPlotMode(PLOT_2D)
        else:
            self.setPlotMode(PLOT_1D)

        if (haveFeature("2D") is False) or self.plotmode == PLOT_1D:
            self.plot._columnSelectionChanged(xsel,y1sel,y2sel)
        elif self.plotmode == PLOT_2D:
            self.plot2d._columnSelectionChanged(xsel,y1sel,y2sel)

    def newScan(self, scanobj):
        self.scanobj = scanobj
        if self.scanobj.isMesh() and self.plotmode == PLOT_1D:
            self.slice_widget.show()
        else: 
            self.slice_widget.hide()

    def selectedSliceChanged(self, slice_no):
        if not self.changing_slice:
            self.datablock.select_slice(slice_no)

    def slicesChanged(self, nb_slices, slice_selected):
        self.nb_slices = nb_slices 
        self.slice_selected = slice_selected

        if nb_slices < 2:
             self.slice_widget.hide()

        if slice_selected is None:
            self.slice_selected = self.nb_slices-1

        self.changing_slice = True
        self.slice_widget.setNumberOfItems(self.nb_slices)
        self.slice_widget.setCurrentItem(self.slice_selected)
        self.changing_slice = False

    def setPlotMode(self, mode):

        if mode == self.plotmode:
            return

        if haveFeature("2D") is False or mode == PLOT_1D:
            self.plotmode = PLOT_1D
            if haveFeature("2D"):
                self.plot2d.hide()
                self.mode2d_widget.hide()

            if self.scanobj and self.scanobj.isMesh():
                self.slice_widget.show()
            else:
                self.slice_widget.hide()
            self.plot.show()

        else:
            self.plotmode = PLOT_2D
            self.plot.hide()
            self.slice_widget.hide()
            self.plot2d.show()
            self.mode2d_widget.show()

    def set2DStyle(self,idx):
        mode = str(self.mode2d_combo.currentText()).lower()
        self.plot2d.set2DStyle(mode)

    def updatePlotData(self):
        if self.plot.isReduced():
            self.regionOutAction.setEnabled(True)
        else:
            self.regionOutAction.setEnabled(False)

        self.plot.updatePlotData()

    def selectCounter(self, counter):
        self.plotHeader.selectCounter(counter)
        self.plot.selectCounter(counter)

    def setExtraCurves(self, curves):
        self.plot.setExtraCurves(curves)

    def updateZoomInfo(self, zooms, zoomidx):

        if zooms > 1:
            #self.zoomresetAction.setEnabled(True)
            if zoomidx == 0:
                self.zoomoutAction.setEnabled(False)
            else:
                self.zoomoutAction.setEnabled(True)
            if zoomidx == (zooms - 1):
                self.zoominAction.setEnabled(False)
            else:
                self.zoominAction.setEnabled(True)
        else:
            self.zoominAction.setEnabled(False)
            self.zoomoutAction.setEnabled(False)
            #self.zoomresetAction.setEnabled(False)

    def setDataStatus(self, status):

        if status == self.status:
            return

        self.status = status

        self.plot.setDataStatus(status)
        self.plot.updatePlotData()

    def getName(self):
        return self.name

    def getPlot(self):
        return self.plot

    def setServerMode(self,flag=True):
        self.server_mode = flag
        if self.server_mode:
            self.serverStateAction.setVisible(True)
            self.abortButtonAction.setVisible(True)
        else:
            self.serverStateAction.setVisible(False)
            self.abortButtonAction.setVisible(False)

    def setAbortAction(self,action):
        obj = weakref.proxy( action.__self__ )
        fn = weakref.proxy( action.__func__ )
        self.abort_action = [obj,fn]

    def setServerStatus(self, status):
        if status == STATUS_READY:
            self.setReady()
        elif status is STATUS_BUSY:
            self.setBusy()
        elif status is STATUS_OFF:
            self.setDisconnected()

    def setReady(self):
        if not self.server_mode:
            return

        self.serverStateLabel.setText("GANS: Ready")

        self.serverStateLabel.setStyleSheet("""
            font-family: 'Segoe UI', 'IBM Plex Sans', sans-serif;
            font-size: 10pt;
            font-weight: 500;
            color: #2e7d32;  /* green text */
            background-color: transparent;
            border: none;
        """)
        self.abortButton.setIcon(self.abortGreyIcon)
        self.abortButton.setText("")
        self.abortButton.setEnabled(False)

    def setBusy(self):
        if not self.server_mode:
            return

        self.serverStateLabel.setText("GANS: Busy")
        self.serverStateLabel.setStyleSheet("""
            font-family: 'Segoe UI', 'IBM Plex Sans', sans-serif;
            font-size: 10pt;
            font-weight: 500;
            color: #ff9800;  /* amber/orange text */
            background-color: transparent;
            border: none;
        """)
        self.abortButton.setIcon(self.abortActiveIcon)
        self.abortButton.setText("Abort")
        self.abortButton.setEnabled(True)

    def setDisconnected(self):
        if not self.server_mode:
            return

        self.serverStateLabel.setText("GANS: Disconnected")
        self.serverStateLabel.setStyleSheet("""
            font-family: 'Segoe UI', 'IBM Plex Sans', sans-serif;
            font-size: 10pt;
            font-weight: 500;
            color: #9e9e9e;  /* grey text */
            background-color: transparent;
            border: none;
        """)
        self.abortButton.setIcon(self.abortGreyIcon)
        self.abortButton.setText("")
        self.abortButton.setEnabled(False)

    def getTitle(self):
        return  self.plotHeader.getTitle()

    # BEGIN print plot
    def printPlot(self, mute=False, filename=None):
        try:
            printer = getPrinter(self.prefs, mute, self, filename)
        except:
            import traceback
            log.log(2, traceback.format_exc())

        if printer is None:
            return

        title = self.plotHeader.getTitle()

        if self.plotmode == PLOT_2D:
            self.plot2d.printPlot(title, printer, filename)
        else:
            self.plot.printPlot(title, printer, filename)

    def saveAsImage(self, filename=None):
        title = self.plotHeader.getTitle()

        if filename is None:
            filename = getSaveFile(self, "Graphic files (*.jpg *png);;ALL (*)")

        if not filename:
            return

        try:
            if self.plotmode == PLOT_2D:
                self.plot2d.saveAsImage(filename, title)
            else:
                self.plot.saveAsImage(filename, title)
        except:
            import traceback
            log.log(2, traceback.format_exc())

    # END print plot
    def setPrinterName(self, name):
        self.prefs['printer_name'] = name

    def setPortrait(self):
        self.prefs['printer_orientation'] = QPrinter.Portrait

    def setLandscape(self):
        self.prefs['printer_orientation'] = QPrinter.Landscape

    def setPrintGrayScale(self):
        self.prefs['printer_colormode'] = QPrinter.GrayScale

    def setPrintColor(self):
        self.prefs['printer_colormode'] = QPrinter.Color

    def setPaperSize(self, size):
        self.prefs['printer_papersize'] = PaperSize[size]

    def zoomOut(self):
        self.plot.zoomout()

    def zoomIn(self):
        self.plot.zoomin()

    def zoomReset(self):
        self.plot.resetzoom()

    def disableZoomButtons(self):
        self.zoominAction.setDisabled(True)
        self.zoomoutAction.setDisabled(True)

    def enableZoomButtons(self):
        self.zoominAction.setDisabled(False)
        self.zoomoutAction.setDisabled(False)

    def setZoomMode(self, mode):
        if mode == CROSSHAIRS_MODE:
            self.selectMode()
        if mode == ZOOM_MODE:
            self.zoomMode()
        if mode == REGIONZOOM_MODE:
            self.regionMode()

    def selectMode(self):
        self.plot.setZoomMode(CROSSHAIRS_MODE)

        self.regionModeAction.setChecked(False)
        self.zoomModeAction.setChecked(False)
        self.selectModeAction.setChecked(True)

    def zoomMode(self):
        self.plot.setZoomMode(ZOOM_MODE)

        self.regionModeAction.setChecked(False)
        self.zoomModeAction.setChecked(True)
        self.selectModeAction.setChecked(False)

    def regionMode(self):
        self.plot.setZoomMode(REGIONZOOM_MODE)

        self.regionModeAction.setChecked(True)
        self.zoomModeAction.setChecked(False)
        self.selectModeAction.setChecked(False)

        self.plot.resetzoom()

    def regionReset(self):
        self.plot.resetzoom()
        self.plot.resetregion()

    # spec functions
    def abort(self):
        if self.server_mode:
           if self.abort_action:
               obj, fn = self.abort_action
               fn(obj)

def addAPoint():
    dtest.addPoint(1, [7, 49, 14])


def addAnotherPoint():
    dtest.addPoint(2, [9, 49, 24])


def test(testset):

    global dtest
    import DataBlock

    app = QApplication([])
    win = QMainWindow()

    win.setWindowTitle('Spec PLOT')

    plot_w = SpecPlotWidget()
    plot = plot_w.plot

    win.setCentralWidget(plot_w)

    meta = {
        'datastatus': DATA_LIVE,
        'ranges': {'First': [-2, 10]},
    }
    dtest = DataBlock.testData(int(testset))

    plot.setDataBlock(dtest)

    direction = -1

    win.setGeometry(200, 100, 400, 400)
    win.show()

    plot.replot()

    plot.setDataStatus(DATA_STATIC)

    QTimer.singleShot(1000, addAPoint)
    QTimer.singleShot(2000, addAnotherPoint)

    plot.setDataStatus(DATA_STATIC)
    plot.selectColumns()
    plot.updatePlotData()

    sys.exit(app.exec_())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test(sys.argv[1])
    else:
        test(2)
