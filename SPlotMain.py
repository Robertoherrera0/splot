#******************************************************************************
#
#  @(#)SPlotMain.py	3.16  01/09/24 CSS
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
import time
import sys
import re

from PySide6.QtWidgets import QTabWidget
from PySide6.QtCore import Qt

from pyspec.css_logger import log, log_exception
from pyspec.file.spec import FileSpec
from pyspec.graphics.QVariant import *
from pyspec.graphics import qt_variant
from pyspec.utils import is_macos

from Constants import *
from Welcome import Welcome
from Colors import ColorTable
from Preferences import Preferences

from SpecFileSource import SpecFileSource
from SpecDataSource import SpecDataSource, SpecVariableSource
from SpecDataConnection import SpecDataConnection

import DataSource
import DataSource2D
import McaSource

import icons

from AddPlotCurveDialog import getAddPlotCurveDialog
from SpecConnectionDialog import getSpecConnectionParameters, getSpecVariableParameters
from ErrorDialog import popupError
from LogDialog import LogDialog
from LoadImageDialog import getLoadImageFile

try:
    import VERSION
    versionInfo = VERSION.getVersion()
except:
    versionInfo = "unknown"

#
# try json or simplejson
#
jsonok = False
try:
    import json
    jsonok = True
except ImportError:
    pass

if not jsonok:
    try:
        import simplejson as json
        jsonok = True
    except ImportError:
        pass


#
#  declare style sheet file
#
cssname = "app.css"
cssfile = os.path.join(os.path.dirname(__file__), cssname)

class MenuBarSet(object):
    def __init__(self, menubar):
        self.menubar = menubar

class SplotTabBar(QTabBar):

    def __init__(self, parent, *args):
        self.parent = parent
        self.mouseactive = 0
        QTabBar.__init__(self, parent, *args)

    def mousePressEvent(self, ev):

        self.inity = ev.pos().y()

        self.tabnumber = self.tabAt(ev.pos())  # which tabnumber
        self.tabrect = self.tabRect(self.tabnumber)
        self.tab0 = self.tabrect.y()
        self.tab1 = self.tabrect.y() + self.tabrect.height()

        if self.parent.canDetach():
            self.mouseactive = 1
            self.tabwid = self.parent.widgetAtTabNumber(self.tabnumber)
            self.detaching = 0

            self.initPos = ev.pos()

            globalpos = self.mapToGlobal(QPoint(self.x(), self.y()))

            self.minx = globalpos.x()
            self.miny = globalpos.y()
            self.maxx = self.minx + self.width()
            self.maxy = self.miny + self.height()

        QTabBar.mousePressEvent(self, ev)

    def mouseMoveEvent(self, ev):

        cury = ev.pos().y()
        totmoved = cury - self.inity
        tab_topy = self.tab0 + totmoved
        tab_boty = self.tab1 + totmoved

        if self.mouseactive and self.tabwid:

            globalpos = self.mapToGlobal(ev.pos())
            gx = globalpos.x()
            gy = globalpos.y()

            self.out = False

            if (self.minx - gx) > 10:
                self.out = True
            if (self.miny - gy) > 10:
                self.out = True
            if (gx - self.maxx) > 10:
                self.out = True
            if (gy - self.maxy) > 10:
                self.out = True

            if self.out and (not self.detaching):
                # detach
                self.parent.detachTab(self.tabwid)
                self.detaching = 1

            if self.detaching:
                if self.out:
                    self.tabwid.move(self.mapToGlobal(ev.pos()))
                    self.tabwid.raise_()
                    self.tabwid.activateWindow()
                else:
                    # re-attach
                    self.parent.attach(self.tabwid.getName())
                    self.detaching = 0

        # restrict mouse move event to keep tabs on view.
        if (tab_topy > -4) and (tab_boty < (self.rect().height() + 5)):
            QTabBar.mouseMoveEvent(self, ev)

    def mouseReleaseEvent(self, ev):
        self.mouseactive = 0
        self.detaching = 0
        self.tabwid = None
        QTabBar.mouseReleaseEvent(self, ev)


class SplotTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setTabPosition(QTabWidget.North)

        self.tabBar().setMovable(False)
        self.tabCloseRequested.connect(self.removeTab)
        self.tabBar().setDrawBase(False)

        self.setStyleSheet("""
            QTabBar {
                qproperty-drawBase: 0;
            }
            QTabBar::tab {
                font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 500;
                color: #2b2b2b;
                padding: 6px 14px;
                background: transparent;
                border: none;
            }
            QTabBar::tab:selected {
                border-bottom: 2px solid #2b2b2b;
                background-color: transparent;
            }
            QTabBar::tab:hover {
                background-color: #f1f1f1;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f5f5f5;
                border-bottom: 2px solid #bbbbbb;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background: #ffffff;
                margin-top: -1px;
                padding: 4px;
            }
            QTabBar::close-button {
                image: url(/usr/local/lib/spec.d/splot/icons/close.svg);
                subcontrol-position: right;
                margin-left: 6px;
            }
            QTabBar::close-button:hover {
                background: transparent;
            }
        """)


    def tabInserted(self, index):
        self.tabBar().setVisible(self.count() > 1)

    def tabRemoved(self, index):
        self.tabBar().setVisible(self.count() > 1)


class SPlotMain(QMainWindow):

    def __init__(self, winname, *args):

        self.sources = {}
        self.spec_source = None
        self.spec_c = None

        self.test_cnt = 0
        self.test_nb = 0
        self.test_time = time.time()

        self.active_source = None   # current source
        self.active_srcname = None  # "name" of current source receiving events 
                                    # from main menu

        self.cmd_srcname = None # "name" of source receiving command events

        self.followed_variables = []
        self.spec_actions = {}

        self.winname = winname

        self.cmdsrv = None
        self.servkey = None
        self.serv_fromcmd = False

        try:
            self.logDialog = LogDialog("pyspec")
        except Exception as e:
            import traceback
            log.log(2, traceback.format_exc())

        QMainWindow.__init__(self, *args)
        self.setWindowTitle(self.winname)

        icondir = os.path.join(os.path.dirname(__file__),'icons')
        self.setWindowIcon(icons.get_icon('splot'))

        self.central_widget = QStackedWidget()

        self.prefs = Preferences()

        self.tabs = SplotTabWidget(self)
        self.tabbar = SplotTabBar(self)
        self.tabs.setTabBar(self.tabbar)

        try:
            # if qt_variant() in ["PyQt6", "PySide6"]:
            self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        except AttributeError:
            self.tabs.setTabPosition(QTabWidget.North)

        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)

        self.tabs.currentChanged.connect(self.currentChanged)
        self.tabs.tabCloseRequested.connect(self.closeTab)

        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.startTimer(100)

        self.setStyleSheet(open(cssfile).read())
        if is_macos():
            self.setStyleSheet(open(os.path.join(os.path.dirname(__file__),"macos.css")).read())

        self.welcome = Welcome(self)

        self.central_widget.addWidget(self.welcome)
        self.central_widget.addWidget(self.tabs)

        menubar = self.menuBar()
        self.menubar_set = self.createMenuBarSet(menubar)
        self.setCentralWidget(self.central_widget)
        self.showWelcome()

        self.remote_cmds = {
            #  Command name:  Command, input_desc, output_desc
            "version":      [self.cmd_version,         None,           None],
            "graph":        [self.cmd_selectCreateSource,     "sourcename",   "currentgraph"],
            "graph_list":   [self.cmd_sourceList,       None,          "graphlist"],
            "source":       [self.cmd_showSourceInfo,  None,          None],
            "+source":      [self.cmd_showSourceInfo,  None,          None],
            "-source":      [self.cmd_hideSourceInfo,  None,          None],
            "show":         [self.cmd_showSource,       "sourcename",          None],
            "xlog":         [self.cmd_setXlog,         None,          None],
            "+xlog":        [self.cmd_setXlog,         None,          None],
            "-xlog":        [self.cmd_setXlinear,      None,          None],
            "ylog":         [self.cmd_setY1log,        None,          None],
            "+ylog":        [self.cmd_setY1log,        None,          None],
            "-ylog":        [self.cmd_setY1linear,     None,          None],
            "y1log":        [self.cmd_setY1log,        None,          None],
            "+y1log":       [self.cmd_setY1log,        None,          None],
            "-y1log":       [self.cmd_setY1linear,     None,          None],
            "y2log":        [self.cmd_setY2log,        None,          None],
            "+y2log":       [self.cmd_setY2log,        None,          None],
            "-y2log":       [self.cmd_setY2linear,     None,          None],
            "grid":         [self.cmd_gridOn,          None,          None],
            "+grid":        [self.cmd_gridOn,          None,          None],
            "-grid":        [self.cmd_gridOff,         None,          None],
            "showmotor":    [self.cmd_showMotorOn,     None,          None],
            "+showmotor":   [self.cmd_showMotorOn,     None,          None],
            "-showmotor":   [self.cmd_showMotorOff,    None,          None],
            "showstats":    [self.cmd_showStatsOn,     None,          None],
            "+showstats":   [self.cmd_showStatsOn,     None,          None],
            "-showstats":   [self.cmd_showStatsOff,    None,          None],
            "refresh":      [self.cmd_refresh,         None,          None],
            "ebars":        [self.cmd_barsOn,          None,          None],
            "+ebars":       [self.cmd_barsOn,          None,          None],
            "-ebars":       [self.cmd_barsOff,         None,          None],
            "dots":         [self.cmd_dotsOn,          None,          None],
            "+dots":        [self.cmd_dotsOn,          None,          None],
            "-dots":        [self.cmd_dotsOff,         None,          None],
            "dotsize":      [self.cmd_dotSize,         None,          None],
            "lines":        [self.cmd_linesOn,         None,          None],
            "+lines":       [self.cmd_linesOn,         None,          None],
            "-lines":       [self.cmd_linesOff,        None,          None],
            "linethick":    [self.cmd_lineThickness,  "thickness",          None],
            "marker":       [self.cmd_addMarker,      "[label] position [options] [persistent]]", "name"],
            "marker_list":  [self.cmd_markerList,     None,           "markerlist"],
            "openfile":     [self.cmd_openfile,       "filename [sourcename]",   "currentfile"],
            "openspec":     [self.cmd_openspec,       "specname",   None],
            "follow":       [self.cmd_followVar,      "specname varname",     None],
            "aspect":       [self.cmd_aspect,          "[equal|auto]",     None],
            "scanno":       [self.cmd_selectScanno,   "scanno",     None],
            "next":         [self.cmd_nextScan,       None,     None],
            "prev":         [self.cmd_prevScan,       None,     None],
            "columns":      [self.cmd_setColumnNames, "col1,",       None],
            "range":        [self.cmd_setRange,       "xbeg xend", None],
            "reduce":       [self.cmd_reduce,         "interval", None],
            "plotrange":    [self.cmd_setPlotRange,   "xbeg xend ybeg yend", None],
            "erase":        [self.cmd_erase,          None, None],
            "full":         [self.cmd_full,        None, None],
            "showpts":      [self.cmd_showpts,     "nbpts", None],
            "color":        [self.cmd_color,       "mne [, color]",   None],
            "plot":         [self.cmd_plotSelect,  None,          None],
            "update":       [self.cmd_plotUpdate,  None,          None],
            "setcolumns":   [self.cmd_plotSelectColumns,  None,          None],
            "saveas":      [self.cmd_saveas,      "filename",   None],
            "print":        [self.cmd_print,       "filename",    None],
            "printer":      [self.cmd_printer,     "printername", None],
            "landscape":    [self.cmd_landscape,    None,    None],
            "portrait":     [self.cmd_portrait,     None,    None],
            "papersize":    [self.cmd_papersize,   "papersize",    None],
            "printgray":    [self.cmd_printgray,   None,    None],
            "printcolor":   [self.cmd_printcolor,  None,    None],
            "detach":       [self.cmd_detach,      "sourcename",   None],
            "attach":       [self.cmd_attach,      "sourcename",   None],
            "raise":        [self.cmd_setRaised,   "sourcename",          None],
            "close":        [self.cmd_close,       "sourcename",  None],
            "quit":         [self.cmd_quitApp,     None,          None],
            "showstatus":   [self.cmd_showStatus,     None,          None],
            "show_image":   [self.cmd_showImage,     "image [,follow]",          None],
            "show_var":   [self.cmd_showVariable,     "variable [,follow, [,destination]]",          None],
            "testcnt":   [self.cmd_count,     "number",          None],
        }

        if jsonok:
            self.remote_cmds["setdata"] = [
                self.cmd_setData,     "jsondata",    None]

        self.testch = 10

        self.remote_vars = {
            "addata":       [self.var_setAddData,  None, ],
            "testvar":      [self.var_setTestVar, self.var_getTestVar],
        }

    def savePreferences(self):
        prefs = Preferences()
        geo = self.geometry()

        x = geo.x()
        y = geo.y()
        w = geo.width()
        h = geo.height()

        prefs["geometry"] = "%d,%d,%d,%d" % (x, y, w, h)
        for sourcename in self.sources:
            source = self.sources[sourcename]
            source.saveGeometry()

        prefs.save()

#------- Handle sources

    def createMenuBarSet(self, menubar):
        menubar_set = MenuBarSet(menubar)
        self.populateMenuBar(menubar_set)
        return menubar_set

    def addSource(self, source, sourcename):

        gno = 1
        gname = sourcename
        while self.sourceExists(gname):
            gno += 1
            gname = "%s_%d" % (sourcename, gno)

        sourcename = gname

        source.sourceActivated.connect(self.sourceActivatedSlot)
        source.configurationChanged.connect(self.updateMenuBar)

        self.sources[sourcename] = source
        source.setSourceName(sourcename)

        self.addSourceTab(source, sourcename)

        self.showSourceTabs()
        self.updateDetached()

        return sourcename

    def getSource(self, sourcename=None):
        if not sourcename:
            if self.cmd_srcname is not None:
                sourcename = self.cmd_srcname
            else:
                sourcename = self.active_srcname

        if sourcename in self.sources:
            source = self.sources[sourcename]
            return source

        return None

    def setActiveSource(self, source):

        if source == self.active_source:
            return

        if self.active_source is not None:
            self.active_source.setInactive()

        if source is None:
            self.active_source = None
            self.active_srcname = None
            return

        self.active_source = source
        self.active_srcname = source.getSourceName()

        # reset source used for command destination
        self.cmd_srcname = None

        source.setActive()
        return self.active_srcname

    def getPlot(self, sourcename=None):
        source = self.getSource(sourcename)

        if source is None:
            return None

        return source.getPlot()

    def getPlotWidget(self, sourcename=None):
        source = self.getSource(sourcename)
        
        if source is None:
            return None

        return source.getPlotWidget()

    def currentChanged(self, index):
        source = self.tabs.currentWidget()
        self.setActiveSource(source)

    def sourceActivatedSlot(self, source):
        idx = self.tabs.indexOf(source)
        self.tabs.setCurrentIndex(idx)
        self.setActiveSource(source)
        self.updateMenuBar(source)

    def addSourceTab(self, source, sourcename=None):
        if not sourcename:
            sourcename = source.getName()
        self.tabs.addTab(source, sourcename)

    def closeCurrentSource(self,flag):
        source = self.getSource(self.active_srcname)
        self.closeSource(source)

    def closeSource(self, source):

        self.hideSourceTab(source)

        if source == self.spec_source:
           self.spec_source = None

        sourcename = source.getSourceName()
        source.close()

        if sourcename not in self.sources:
            return

        self.sources.pop(sourcename)
        self.selectDefaultSource()

        if len(self.sources) == 0:
            self.showNoSource()
        
        self.updateDetached()

    def hideSourceTab(self, source):
        if source.isDetached():
            source.saveGeometry()
            if source.attachWhenClosing():
                self.attach(source.getSourceName())
            else:
                source.deleteLater()

        self.tohide = source
        QTimer.singleShot(0, self._doHide)

    def _doHide(self):
        source = self.tohide

        try:
            sidx = self.tabs.indexOf(source)
        except:
            return

        if sidx != -1:
            self.tabs.removeTab(sidx)
            self.tohide = None
        else:
            log.log(3," source %s not in tabs." % source.getSourceName())

    def closeTab(self, cidx=None):
        source = self.tabs.widget(cidx)
        self.closeSource(source)

    def selectDefaultSource(self, cidx=None):

        if not len(self.sources):
            self.active_srcname = None
            return

        # try first with current_source
        source = None
        if self.active_srcname in self.sources:
            srcname = self.active_srcname
            source = self.sources[srcname]

        # then find the first non detached
        if not source or source.isDetached():
            for srcname in self.sources.keys():
                source = self.sources[srcname]
                if not source.isDetached():   # select this one
                    break

        # if none was found (like when closing the latest tab)
        if source:
            self.tabs.setCurrentWidget(source)
            self.setActiveSource(source)
        else:
            self.setActiveSource(None)

    def sourceExists(self, name):
        return name in self.sources

    def showWelcome(self):
        self.welcome.welcome()
        self._showWelcome()
  
    def showNoSource(self):
        #self.welcome.nosource()
        self._showWelcome()
         
    def _showWelcome(self):
        self.setActiveSource(self.welcome)
        self.central_widget.setCurrentIndex(0)

    def showSourceTabs(self):
        self.central_widget.setCurrentIndex(1)

    def widgetAtTabNumber(self, tabno):
        wid = self.tabs.widget(tabno)
        if wid:
            return wid

    def canDetach(self):
        available = 0

        for srcname in self.sources.keys():
            src = self.sources[srcname]
            if src.isDetached():
                continue
            else:
                available += 1

        if available < 2:
            return False
        else:
            return True

    def detachTab(self, todetach):
        if not self.canDetach():
            return None

        if todetach:
            sourcename = todetach.getSourceName()
            detached = self.detach(sourcename)
        return detached

    def attach(self, sourcename=None):
        source = self.getSource(sourcename)

        log.log(3,"attaching %s" % source.getDisplayName())

        source.saveGeometry()
        source.setDetachMode(False)

    def detach(self, sourcename=None):
        if not self.canDetach():
            return

        source = self.getSource(sourcename)

        self._detach(source)
        return source

    def _detach(self, source):
        self.hideSourceTab(source)
        source.setDetachMode(True)
        self.selectDefaultSource()

    def updateDetached(self):

        attached = []
        detached = []

        for sourcename in self.sources:
            source = self.sources[sourcename]
            if source.isDetached():
                detached.append(source)
            else:
                attached.append(source)

        if len(attached) == 0:
            # no one in main window. reattaching one detached
            if len(detached) > 0:
                detached[0].setDetachMode(False)
        elif len(attached) == 1:
            # telling you are the only attached
            #attached[0].updateDetachMenu(alone=True)
            pass
        elif len(attached) > 0:
            # telling you are not the only attached
            #for src in attached:
            #    src.updateDetachMenu(alone=False)
            pass

    # Create spec source 
    def connectToSpec(self, connpars, varname=None, sourcename=None, check_datafile=False):
        """
           Connecting to spec in one SPlotMain instance:
 
           - a connection to "main" SCAN_D will be opened first

           - if "varname" is provided a second connection to that variable
                will also be opened

           - a connection to spec when a "main" connection is opened will be
             refused

        """
        if varname:
            log.log(3,"  - using array with name: %s" % varname)

        if not varname:
            varname = "SCAN_D"

        if varname == "SCAN_D":
            if self.spec_source:
                log.log(3,"  - already connected to spec" % self.spec_source.getSpecName())
                return

        if not self.spec_source:
            source = SpecDataSource(self, connpars)
            self.spec_source = source
            
        if not self.spec_c:
            if self.cmdsrv is not None:
                srvport = self.cmdsrv.get_port()
            else:
                srvport = None
            self.spec_c  = SpecDataConnection(connpars, ignore_ports=[srvport])
        else:
            log.log(2, "already connected to %s" % self.spec_c.get_specname())
            return

        host = self.spec_c.get_host()
        specname = self.spec_c.get_specname()

        self.prefs['remotehost'] = host
        self.prefs['remotespec'] = specname

        self.spec_source = source
        self.spec_c.set_source(source)  
        source.set_connection(self.spec_c)

        if not sourcename:
            sourcename = source.getSpecName()

        if check_datafile:
            source.filenameChanged.connect(self.openFile)

        sourcename = self.addSource(source, sourcename)

        if self.spec_c is not None:
            # we need a timer to dispatch events
            self.spec_timer = QTimer()
            self.spec_timer.timeout.connect(self.update_spec_events)
            self.spec_timer.start(10)

        if varname != "SCAN_D":
            source = SpecVariableSource(self, self.spec_source, varname)
            if not sourcename:
                sourcename = source.getSpecName()
            sourcename = self.addSource(source, sourcename)

        self.setActiveSource(source)

        return sourcename

    def update_spec_events(self):
        if self.spec_c:
            self.spec_c.update_events()

    # Create file source 
    def openFile(self, filename, fromSpec=True, sourcename=None):

        filename = str(filename)

        if not filename:
            return

        if filename == "/dev/null":
            return

        try:
            file_source = SpecFileSource(self, filename)
            msg = None 
        except IOError as e:
            msg = "Cannot open file %s" % filename
            moremsg = "<b>%s</b>" % str(e.strerror)
        except BaseException as e:
            import traceback
            log.log(3, traceback.format_exc())
            log.log(3,"Problem opening file %s" % str(e))
            msg = "Cannot open file %s" % filename
            moremsg = "<b>%s</b>" % str(e)

        if msg:
            ret = popupError(self, "Open file", msg,
                             severity="warning", moremsg=moremsg)
            return

        if not sourcename:
            sourcename = os.path.basename(filename)

        # Create a Specfile browser

        sourcename = self.addSource(file_source, sourcename)

        if not fromSpec:
            self.setActiveSource(file_source)

        file_source.set_spec_connection(self.spec_c)
        return sourcename

    def closeConnections(self):
        if self.spec_c is not None:
            self.spec_c.close_connection()

    # Select scan in file
    def selectScan(self, scanno):

        source = self.getSource(self.active_srcname)

        if source and source.getType() is SOURCE_FILE:
            filesource.selectScan(scanno)

    # Create empty user source
    def newUserSource(self, sourcename):
        if self.sourceExists(sourcename):
            return None

        source = McaSource.McaSource(self, varname=sourcename)
        sourcename = self.addSource(source, sourcename)

        return source

#------- END Handle sources
    
#------- MenuBar -------------------------------------------------------------
    def populateMenuBar(self, menubar_set):

        self.createFileMenu(menubar_set)
        self.createSpecMenu(menubar_set)
        self.createViewMenu(menubar_set)
        self.createPlotMenu(menubar_set)
        self.createDataMenu(menubar_set)
        self.createMathMenu(menubar_set)
        self.createHelpMenu(menubar_set)

        menubar_set.menubar.addMenu(menubar_set.fileMenu)
        menubar_set.menubar.addMenu(menubar_set.specMenu)

        # create it disabled. It will be updated when a spec source becomes available
        menubar_set.specMenu.setEnabled(False) 
        menubar_set.menubar.addMenu(menubar_set.viewMenu)
        menubar_set.menubar.addMenu(menubar_set.plotMenu)
        menubar_set.menubar.addMenu(menubar_set.dataMenu)
        menubar_set.menubar.addMenu(menubar_set.mathMenu)
        menubar_set.menubar.addMenu(menubar_set.helpMenu)

    def updateMenuBar(self, src):

        if self.active_source is None:
            log.log(3,"  - no active source?? weird")
            return

        act_src = self.active_source

        if src != act_src: # got 
            return

        # File Menu
        is_detached = act_src.isDetached()

        if is_detached:
            menubar_set = act_src.getMenuBarSet()
            menubar_set.attachAction.setEnabled(True)
            menubar_set.detachAction.setEnabled(False)
        else:
            menubar_set = self.menubar_set
            menubar_set.attachAction.setEnabled(False)
            menubar_set.detachAction.setEnabled(True)

        # SPEC menu
        if self.spec_source:
            menubar_set.specMenu.setEnabled(True)
            menubar_set.openSpecAction.setEnabled(False)

            if not self.spec_source.isServer():
                try:
                    menubar_set.setFileAction.setDisabled(True)
                except:
                    pass
        else:
            menubar_set.specMenu.setEnabled(False)
            menubar_set.openSpecAction.setEnabled(True)

        # Data Source menu
        if act_src.isSourceInfoVisible():
            menubar_set.toggleViewAction.setText("Hide Source Area")
            menubar_set.toggleViewAction.setStatusTip('Hide source area pane')
        else:
            menubar_set.toggleViewAction.setText("Show Source Area")
            menubar_set.toggleViewAction.setStatusTip('Show source area pane')

        # Plot Menu
        act_src.update_menubar(menubar_set)

    def createFileMenu(self, menubar_set):

        newSourceAction = QAction('&New', self)
        # newSourceAction.setShortcut('Ctrl+N')
        newSourceAction.setStatusTip('Create new empty data source')
        newSourceAction.triggered.connect(self.createNewSource)
        menubar_set.newSourceAction = newSourceAction

        preferencesAction = QAction('&Preferences', self)
        # preferencesAction.setShortcut('Ctrl+P')
        preferencesAction.setStatusTip('Preferences')
        preferencesAction.triggered.connect(self.openPreferencesDialog)
        menubar_set.preferencesAction = preferencesAction

        openSpecAction = QAction('Connect to &SPEC', self)
        openSpecAction.setStatusTip('Connect to SPEC')
        openSpecAction.triggered.connect(self.selectSpec)
        menubar_set.openSpecAction = openSpecAction

        openFileAction = QAction('&Open SPEC File', self)
        openFileAction.setStatusTip('Open File')
        openFileAction.triggered.connect(self.openFileChoose)
        menubar_set.openFileAction = openFileAction

        loadImageAction = QAction('&Load Image data', self)
        loadImageAction.setStatusTip('Load Image datafile')
        loadImageAction.triggered.connect(self.load_image_data)
        menubar_set.loadImageAction = loadImageAction

        closeAction = QAction('&Close', self)
        #closeAction.setShortcut('Ctrl+C')
        closeAction.setStatusTip('Close')
        closeAction.triggered.connect(self.closeCurrentSource)
        menubar_set.closeAction = closeAction

        attachAction = QAction('A&ttach', self)
        #attachAction.setShortcut('Ctrl+t')
        attachAction.setStatusTip('Attach source back to main window')
        attachAction.triggered.connect(self.attach)
        menubar_set.attachAction = attachAction

        detachAction = QAction('&Detach', self)
        #detachAction.setShortcut('Ctrl+D')
        detachAction.setStatusTip('Detach source from main window')
        detachAction.triggered.connect(self.detach)
        menubar_set.detachAction = detachAction

        saveAsImageAction = QAction('Save as &Image', self)
        saveAsImageAction.setStatusTip('Save as image')
        # saveAsImageAction.setShortcut('Ctrl+I')
        saveAsImageAction.triggered.connect(self.saveAsImage)
        menubar_set.saveAsImageAction = saveAsImageAction

        printPlotAction = QAction('&Print Plot', self)
        printPlotAction.setShortcut('Ctrl+P')
        printPlotAction.setStatusTip('Print Plot')
        printPlotAction.triggered.connect(self.printPlot)
        menubar_set.printPlotAction = printPlotAction

        exitAction = QAction('&Exit', self)
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.appQuit)
        menubar_set.exitAction = exitAction

        fileMenu = QMenu("&File")

        fileMenu.addActions([newSourceAction, preferencesAction])
        fileMenu.addSeparator()
        fileMenu.addActions([openSpecAction, openFileAction, loadImageAction, closeAction, attachAction, detachAction])
        fileMenu.addSeparator()
        fileMenu.addActions([saveAsImageAction, printPlotAction])
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        menubar_set.fileMenu = fileMenu

    def createSpecMenu(self, menubar_set):
        setFileAction = QAction('&Set Data File', self)
        setFileAction.setStatusTip('Select File to save scan data')
        setFileAction.triggered.connect(self.setSpecDataFile)

        specVariableAction = QAction("&Display Variable", self)
        specVariableAction.setStatusTip('Select a variable to be displayed')
        specVariableAction.triggered.connect(self.selectSpecVariable)

        roiAction = QAction('Define ROI', self)
        roiAction.setStatusTip("Define Region of Interest in SPEC")
        roiAction.triggered.connect(self.define_roi) 
        roiAction.setEnabled(True)

        specMenu = QMenu("&Spec")

        specMenu.addAction(setFileAction)
        specMenu.addAction(specVariableAction)
        specMenu.addAction(roiAction)

        menubar_set.setFileAction = setFileAction
        menubar_set.specVariableAction = specVariableAction
        menubar_set.roiAction = roiAction
        menubar_set.specMenu = specMenu

    def createViewMenu(self, menubar_set):
        toggleViewAction = QAction('Show Source Area', self)
        toggleViewAction.setStatusTip('Show source area pane')
        toggleViewAction.triggered.connect(self.toggleSourceView)

        viewMenu = QMenu("&View")
        viewMenu.addAction(toggleViewAction)

        menubar_set.toggleViewAction = toggleViewAction
        menubar_set.viewMenu = viewMenu

    def createPlotMenu(self, menubar_set):
        setlogxAction = QAction('&X Axis Log Scale', self)
        setlogxAction.triggered.connect(self.toggleXLog)

        setlogy1Action = QAction('Y &Left Axis Log Scale', self)
        setlogy1Action.triggered.connect(self.toggleY1Log)

        setlogy2Action = QAction('Y &Right Axis Log Scale', self)
        setlogy2Action.triggered.connect(self.toggleY2Log)

        gridAction = QAction('Show &Grid', self)
        gridAction.triggered.connect(self.togglePlotGrid)

        optionsAction = QAction('Plot &Options', self)
        optionsAction.triggered.connect(self.showPlotOptionDialog)

        showMotorAction = QAction('Show &Motor on Plot', self)
        showMotorAction.triggered.connect(self.toggleShowMotor)

        showStatsAction = QAction('Show &Stats on Plot', self)
        showStatsAction.triggered.connect(self.toggleShowStats)

        plotMenu = QMenu("&Plot")
        plotMenu.addActions([setlogxAction, setlogy1Action, setlogy2Action])
        plotMenu.addSeparator()
        plotMenu.addAction(gridAction)
        plotMenu.addSeparator()
        plotMenu.addActions([showMotorAction, showStatsAction])
        plotMenu.addSeparator()
        plotMenu.addAction(optionsAction)

        menubar_set.setlogxAction = setlogxAction
        menubar_set.setlogy1Action = setlogy1Action
        menubar_set.setlogy2Action = setlogy2Action
        menubar_set.gridAction = gridAction
        menubar_set.showMotorAction = showMotorAction
        menubar_set.showStatsAction = showStatsAction
        menubar_set.optionsAction = optionsAction

        menubar_set.plotMenu = plotMenu

    def createDataMenu(self, menubar_set):
        dataMenu = QMenu("&Data")
        menubar_set.dataMenu = dataMenu

        colormapAction = QAction('Edit colormap', self)
        colormapAction.setStatusTip("Edit color uses for data display")
        colormapAction.triggered.connect(self.edit_colormap) 

        defineAxesAction = QAction('Define Axes', self)
        defineAxesAction.setStatusTip("Define titles and ranges for X and Y Axes")
        defineAxesAction.triggered.connect(self.define_axes) 
        defineAxesAction.setEnabled(True)

        export2DAction = QAction('Export selected data', self)
        export2DAction.setStatusTip("Export selected data to image file")
        export2DAction.triggered.connect(self.export2d) 
        export2DAction.setEnabled(False)

        dataMenu.addAction(colormapAction)
        #dataMenu.addAction(roiAction)
        dataMenu.addAction(defineAxesAction)
        dataMenu.addAction(export2DAction)

        menubar_set.dataMenu = dataMenu

    def createMathMenu(self, menubar_set):
        gaussianAction = QAction('Fit active plot (Gaussian)', self)
        gaussianAction.setStatusTip('Estimate fit for active counter (Gaussian)')
        gaussianAction.triggered.connect(self.gaussianFit)

        lorentzAction = QAction('Fit active plot (Lorentzian)', self)
        lorentzAction.setStatusTip('Estimate fit for active counter (Lorentzian)')
        lorentzAction.triggered.connect(self.lorentzFit)

        lineAction = QAction('Fit active plot to Line', self)
        lineAction.setStatusTip('Estimate fit for active counter (Line)')
        lineAction.triggered.connect(self.lineFit)

        mathMenu = QMenu("&Math")
        mathMenu.addActions([gaussianAction, lorentzAction, lineAction])

        menubar_set.gaussianAction = gaussianAction
        menubar_set.lorentzAction = lorentzAction
        menubar_set.lineAction = lineAction

        menubar_set.mathMenu = mathMenu

    def createHelpMenu(self,menubar_set):
        helpAction = QAction('&About splot', self)
        helpAction.setShortcut('Ctrl+H')
        helpAction.setStatusTip('About')
        if self.parent:
            helpAction.triggered.connect(self.helpAbout)

        logConsoleAction = QAction('&Debug console', self)
        # logConsoleAction.setShortcut('Ctrl+L')
        logConsoleAction.setStatusTip('Debug')
        if self.parent:
            logConsoleAction.triggered.connect(self.showLogConsole)

        helpMenu = QMenu("&Help")
        helpMenu.addActions([helpAction, logConsoleAction])

        menubar_set.helpAction = helpAction
        menubar_set.logConsoleAction = logConsoleAction
        menubar_set.helpMenu = helpMenu

#------- END MenuBar -------------------------------------------------------------

#------- Menu Actions -------------------------------------------------------------

    def saveAsImage(self, sourcename=None, filename=None):
        plot_w = self.getPlotWidget(sourcename)
        if plot_w:
            plot_w.saveAsImage(filename)

    def printPlot(self, sourcename=None, mute=False, filename=None):
        plot_w = self.getPlotWidget(sourcename)
        log.log(2, "Printing source: %s" % self.getSource(sourcename))

        if plot_w:
            plot_w.printPlot(mute=mute, filename=filename)

    def createNewSource(self, sourcename=None):
        for i in range(300):
            sourcename = "source_%d" % i
            if sourcename not in self.sources:
                 source = self.newUserSource(sourcename)
                 break

        return self.setActiveSource(source)

    def appQuit(self, code=0):
        log.log(3,"in window appquit")

        #if self.cmdsrv:
        #    self.cmdsrv.stop()

        self.closeConnections()
        self.savePreferences()
        getQApp().exit(0)

    def setSpecDataFile(self):
        filename = QFileDialog.getSaveFileName(
            self, "Choose file to save scan data", ".")

        if type(filename) in [list, tuple]:
           filename = filename[0]

        if filename:
            self.active_source.setDataFile(filename)

    def displaySpecVariable(self, varname, vartype=DATA_1D, follow=False, destination=None):

        if not self.spec_source:
            log.log(3,"trying to display a spec variable while spec is not yet connected")
            return

        specname = self.spec_source.getSpecName()

        if destination is not None:
            src = self.getSource(destination)
            if src is not None: 
                newsrc = False
            else:
                newsrc = True
        else:
            newsrc = True
            destination = varname

        try:
            if newsrc:
                if vartype == DATA_2D:
                    src = DataSource2D.DataSource2D(self, specname=specname, varname=varname)
                    src.set_connection(self.spec_c)
                else:
                    src = McaSource.McaSource(self, specname=specname, varname=varname)
                    src.set_connection(self.spec_c)
                    #src = SpecVariableSource(self, self.spec_source, varname)

                self.addSource(src, destination)
            else:
                if vartype == DATA_1D and src.isMCA():
                    src.add_variable(specname, varname)

            if follow:
               src.follow()
            else:
                if vartype == DATA_2D and src.is2D():
                    data = self.spec_c.getVariableData(varname)
                    src.setData(data)

        except BaseException as e:
           import traceback
           log.log(2, traceback.format_exc())

        self.setActiveSource(src)
        return destination

    def show_mcas(self, mcas, parent=None, name=None):
        if parent is not None:
            srcname = parent.getSourceName()

        if not name and srcname is not None:
            srcname = "MCA-"+srcname
        elif name:
            srcname = srcname
        else:
            srcname = "MCA"

        src = self.getSource(srcname)
        if src is None:
            src = McaSource.McaSource(self, specname=None, varname=srcname)
            self.addSource(src,srcname)

        src.setData(mcas)

    def toggleSourceView(self):
        self.active_source.toggleSourceInfoView()

    def toggleXLog(self):
        self.active_source.toggleXLog()

    def toggleY1Log(self):
        self.active_source.toggleY1Log()

    def toggleY2Log(self):
        self.active_source.toggleY2Log()

    def togglePlotGrid(self):
        self.active_source.togglePlotGrid()

    def showPlotOptionDialog(self):
        self.active_source.showPlotOptionDialog()

    def toggleShowMotor(self):
        self.active_source.toggleShowMotor()

    def toggleShowStats(self):
        self.active_source.toggleStatsOnPlot()

    def gaussianFit(self):
        self.active_source.gaussianFit()

    def lorentzFit(self):
        self.active_source.lorentzFit()

    def lineFit(self):
        self.active_source.lineFit()

    def edit_colormap(self):
        try:
            self.active_source.edit_colormap()
        except AttributeError:
            import traceback
            log.log(1, traceback.format_exc())
            log.log(1, " source %s has no edit_colormap feature" % self.active_srcname)

    def define_roi(self):
        try:
            self.active_source.define_roi()
        except AttributeError:
            import traceback
            log.log(2,traceback.format_exc())
            log.log(1, " source %s has no exporting 2D feature" % self.active_srcname)

    def define_axes(self):
        try:
            self.active_source.define_axes()
        except AttributeError:
            log.log(1, " source %s has no exporting 2D feature" % self.active_srcname)

    def export2d(self):
        try:
            self.active_source.export2d()
        except AttributeError:
            log.log(1, " source %s has no exporting 2D feature" % self.active_srcname)


#------- END Menu Actions -------------------------------------------------------------

#------- Command Server and commands -------------------------------------------------------------
    def set_command_server(self, server):
        self.cmdsrv = server
        self.cmdsrv.set_commands(self.remote_cmds)
        self.cmdsrv.set_channels(self.remote_vars)

    def apply_command_server_prefs(self, runit, name):

        log.log(2, "cmd server prefs: %s - %s" % (runit,name))
        if runit:
            self.cmdsrv.set_name(name)
            if not self.cmdsrv.is_running():
                log.log(2, "starting command server")
                self.cmdsrv.run()
            else:
                log.log(2, "command server already running. name changed")
            self.prefs.setValue('cmd_server', name)
        else:
            self.prefs.removeValue('cmd_server')

        self.prefs.save()

    def getCommandServerInfo(self):
        if self.cmdsrv is None:
            running = False
        else:
            running = True
        return [running, self.servkey, self.serv_fromcmd]

    def cmd_version(self, long=False):
        if long:
            return VERSION.getFullVersion()
        else:
            return VERSION.getVersion()

    def cmd_setRaised(self, sourcename=None):

        source = self.getSource(sourcename)

        if source:
            source.xraise()
            self.setActiveSource(source)

        return True

    def cmd_quitApp(self):
        self.appQuit(0)
        return True

    def cmd_showStatus(self):
        return True

    def cmd_selectCreateSource(self, sourcename=None):
        # it does not activate it
        if sourcename  and sourcename not in self.sources:
            sourcename = self.newUserSource(sourcename)

        self.cmd_srcname = sourcename
        return sourcename

    def cmd_plotUpdate(self, sourcename=None):
        source = self.getSource(sourcename)
        source.newScan(update=True)
        return True

    def cmd_plotSelectColumns(self, xselection, yselection, sourcename=None):

        xcolnames = []
        y1colnames = []
        y2colnames = []

        xselection = None
        y1selection = None
        y2selection = None

        source = self.getSource(sourcename)

        xparts = xselection.split(":")
        if xparts:
            xcolnames = xparts.split(",")

        yparts = yselection.split(":")

        y1selection = yparts[0]

        if len(yparts) > 1:
            y2selection = yparts[1]

        if y1selection:
            y1colnames = y1selection.split(",")

        if y2selection:
            y2colnames = y2selection.split(",")

        if xcolnames:
            source.setXSelection(xcolnames, override_default=True)

        source.setYSelection(y1colnames, y2colnames, override_default=True)

        return True

    def cmd_plotSelect(self, par1, par2=None, par3=None):
        """ 
          Parameters to plotSelect are given a string composed of colom separated list of values.
          More than one column can be given for y1selection and y2selection by using comma to 
          separate the columns.

          if nb_pars = 1
               par = y1selection
          if nb_pars = 2
               par1 = xselection
               par2 = yselection
          if nb_pars = 3
               par1 = xselection
               par2 = yselection
               par3 = nb_points

          Example:
              pars = "roi1,roi2"     -  Selects roi1 and roi2 to be plotted as y1
              pars = "th roi1,roi2:det"  -  As before, but selects also th for x axis. det is plotted following the y2 axis
              pars = "th det 10"    -  xselection is x, y selection is det and only the first 10 points will be shown on graph
        """

        xcolnames = []
        y1colnames = []
        y2colnames = []

        xselection = None
        y1selection = None
        y2selection = None
        pt_interval = None

        source = self.getSource()
        plot = self.getPlot()

        if par2 == None:
            yselection = par1
        else:
            xselection = par1
            yselection = par2
            pt_interval = par3

        if xselection:
            xcolnames = xselection.split(",")

        yparts = yselection.split(":")

        y1selection = yparts[0]

        if len(yparts) > 1:
            y2selection = yparts[1]

        if y1selection:
            y1colnames = y1selection.split(",")

        if y2selection:
            y2colnames = y2selection.split(",")

        if xcolnames:
            source.setXSelection(xcolnames, override_default=False)

        if pt_interval:
            plot.setInterval(pt_interval)
        else:
            plot.resetRange()

        source.setYSelection(y1colnames, y2colnames, override_default=False)

        # to force an update of saved configuration if needed
        source.setPlotConfigModified(True)

        return True

    def cmd_saveas(self, filename=None, sourcename=None):
        self.saveAsImage(sourcename=sourcename, filename=filename)
        return True

    def cmd_print(self, filename=None, sourcename=None):
        self.printPlot(sourcename=sourcename, mute=True, filename=filename)
        return True

    def cmd_printer(self, printername, sourcename=None):
        plot_w = self.getPlotWidget(sourcename)
        if plot_w:
            plot_w.setPrinterName(printername)
        return True

    def cmd_landscape(self, sourcename=None):
        plot_w = self.getPlotWidget(sourcename)
        if plot_w:
            plot_w.setLandscape()
        return True

    def cmd_portrait(self, sourcename=None):
        plot_w = self.getPlotWidget(sourcename)
        if plot_w:
            plot_w.setPortrait()
        return True

    def cmd_papersize(self, papersize, sourcename=None):
        plot_w = self.getPlotWidget(sourcename)
        if plot_w:
            plot_w.setPaperSize(papersize)
        return True

    def cmd_printgray(self, sourcename=None):
        plot_w = self.getPlotWidget(sourcename)
        if plot_w:
            plot_w.setPrintGrayScale()
        return True

    def cmd_printcolor(self, sourcename=None):
        plot_w = self.getPlotWidget(sourcename)
        if plot_w:
            plot_w.setPrintColor()
        return True

    def cmd_close(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            self.closeSource(source)
        return True

    def cmd_detach(self, sourcename=None):
        if not sourcename:
            sourcename = self.active_srcname

        self.detach(sourcename)
        return True

    def cmd_attach(self, sourcename=None):
        if not sourcename:
            sourcename = self.active_srcname
        self.attach(sourcename)
        return True

    def cmd_sourceList(self):
        andch = " "
        retstr = ""
        for fname in self.sources:
            retstr += fname
            if fname == self.active_srcname:
                retstr += "*"
            retstr += andch
            andch = " "
        return retstr

    def cmd_showSource(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            self.setActiveSource(source)
        return True

    def cmd_showSourceInfo(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.openSplitter()
        return True

    def cmd_hideSourceInfo(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.closeSplitter()
        return True

    def cmd_setXlog(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.setPlotXLog(True)
        return True

    def cmd_setXlinear(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.setPlotXLog(False)
        return True

    def cmd_setY1log(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.setPlotY1Log(True)
        return True

    def cmd_setY1linear(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.setPlotY1Log(False)
        return True

    def cmd_setY2log(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.setPlotY2Log(True)
        return True

    def cmd_setY2linear(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.setPlotY2Log(False)
        return True

    def cmd_gridOn(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.showPlotGrid(True)
        return True

    def cmd_gridOff(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.showPlotGrid(False)
        return True

    def cmd_showMotorOn(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.setShowMotorOnPlot(True)
        return True

    def cmd_showMotorOff(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.setShowMotorOnPlot(False)
        return True

    def cmd_showStatsOn(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.showStatsOnPlot(True)
        return True

    def cmd_showStatsOff(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.showStatsOnPlot(False)
        return True

    def cmd_refresh(self, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.redrawCurves()
        return True

    def cmd_dotsOn(self, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.setUseDots(True)
            plot.redrawCurves()
        return True

    def cmd_barsOn(self, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.showErrorBars(True)
            plot.redrawCurves()
        return True

    def cmd_barsOff(self, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.showErrorBars(False)
            plot.redrawCurves()
        return True

    def cmd_dotsOff(self, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.setUseDots(False)
            plot.redrawCurves()
        return True

    def cmd_dotSize(self, dotsize, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.setDotSize(int(dotsize))
            plot.redrawCurves()
        return True

    def cmd_linesOn(self, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.setUseLines(True)
            plot.redrawCurves()
        return True

    def cmd_linesOff(self, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.setUseLines(False)
            plot.redrawCurves()
        return True

    def cmd_lineThickness(self, thickness, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.setLineThickness(thickness)
            plot.redrawCurves()
        return True

    def cmd_markerList(self, sourcename=None):
        plot = self.getPlot(sourcename)
        markerlist = plot.getMarkers()

        retstr = ""
        for label, mtype, pos in markerlist:
            retstr += "%s (%s) at %s\n" % (label, mtype, str(pos))
        return retstr

    def cmd_addMarker(self, *pars):
        """
            pars combination could be:
               position 

               label remove

               position options
               position persistent
               position options persistent

               label position options
               label position persistent
               label position options persistent

            markers without a label will be assigned a hidden one (to be able to remove them) but not displayed
            Use list markers to get list of markers.  This function will return the name of the marker created.

            options support for now
               color
                  or
               color, linethick

        """
        plot = self.getPlot(self.active_srcname)

        if not plot:
            return True

        xpos = None
        label = None
        options = None
        persistent = False
        marker_name = ""

        params = list(pars)

        if len(params) == 0:
            return marker_name

        # find position in either first or second parameter. It has to be there in any case
        # if found in first position label is then hidden but an automatic label name is created
        #    if label needs to be a float number, add a hash ## in front

        # first parameter
        log.log(3,"adding marker. Parameters %d / are %s " %
               (len(params), " - ".join(params)))
        par1 = params.pop(0)

        posinfo = self.parsePosition(par1)

        if posinfo is None:
            # to set a float number as label for marker. put a double hash in
            # front ##
            label = par1

        # second parameter if posinfo not found yet
        if posinfo is None and len(params):
            par2 = params.pop(0)
            if par2 == "remove":
                plot.removeMarker(label)
                return marker_name
            else:
                posinfo = self.parsePosition(par2)

        if posinfo is None:
            log.log(3,"Could not find position for marker in command")
            return marker_name

        # At this point only color and persistent are left in params
        if len(params) and params[-1] == "persistent":
            persistent = True
            params.pop(-1)

        if len(params):
            options = params.pop(0)

        if len(params):
            log.log(3,"Wrong number of parameters for marker definition")
            return marker_name

        try:
            marker_name = plot.addMarker(
                label, posinfo, persistent=persistent, options=options)
        except:
            import traceback
            log.log(2, traceback.format_exc())

        return marker_name

    def parsePosition(self, pos_str):
        # Posinfo could be
        #    a float number --->  xpos por vertical line
        # four float numbers separated by comma --->  x0, x1, y0, y1 to draw a
        # segment
        try:
            xpos = float(pos_str)
            return [xpos, ]
        except:
            pass

        try:
            lpos = map(float, pos_str.split(","))
            if len(lpos) != 4 and len(lpos) != 2:
                msg = "marker position. Wrong number of arguments"
                log.log(3,msg)
                return None
            else:
                return lpos
        except:
            pass

        return None

    def cmd_openfile(self, filename, sourcename=None):

        if filename and os.path.exists(filename):
            sourcename = self.openFile(filename, sourcename=sourcename)
            return sourcename

        return "file not found"

    def cmd_openspec(self, specname, sourcename=None):
        sourcename = self.connectToSpec(specname, sourcename=sourcename)
        return sourcename

    def cmd_color(self, mne, color=None):
        if not color:
            return str(ColorTable().getColor(mne))
        else:
            ColorTable().setColor(mne, color)
        return True

    def cmd_followVar(self, specname, varname, sourcename=None):
        if not sourcename:
            sourcename = varname

        sourcename = self.displaySpecVariable(varname)
        return sourcename

    def cmd_aspect(self, aspect,sourcename=None):
        source = self.getSource(sourcename)

        if source:
            source.set_aspect_ratio(aspect)
        
        return True

    def cmd_selectScanno(self, scanno, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.selectScan(int(scanno))
        return True

    def cmd_nextScan(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.next()
        return True

    def cmd_prevScan(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.prev()
        return True

    def cmd_setRange(self, xbeg, xend, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.setRange(int(xbeg), int(xend))
        return True

    def cmd_setPlotRange(self, par1, par2, par3, par4, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.setPlotRange(par1, par2, par3, par4)
        return True

    def cmd_reduce(self, interval, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.setInterval(interval)
        return True

    def cmd_erase(self, sourcename=None):
        source = self.getSource(sourcename)
        if source:
            source.resetData()
        return True

    def cmd_full(self, sourcename=None):
        plot = self.getPlot(sourcename)
        if plot:
            plot.resetRange()
        return True

    def cmd_showpts(self, nbpts, sourcename=None):
        try:
            nbpts = int(nbpts)
        except:
            return False

        plot = self.getPlot(sourcename)
        if plot:
            plot.setShowPoints(nbpts)
        return True

    def cmd_setData(self, jdata, colnames=None):

        data = json.loads(jdata)

        if len(data) == 2:
            data = data[0]
        else:
            log.log(3,"No column names")

        source = self.getSource()
        if not source:
            return True

        if colnames:
            source.setColumnNames(colnames.split(","))

        source.setData(data)

        return True

    def var_setAddData(self, data_array):

        source = self.getSource()
        if not source:
            return True

        source.setData(data_array)

        return True

    def cmd_setColumnNames(self, columnnames, sourcename=None):
        cols = columnnames.split(",")
        source = self.getSource(sourcename)
        if source:
            source.setColumnNames(cols)
        return True

    def cmd_showImage(self, varname, *args):

        args = list(args)

        if "follow" in args:
            follow = True
            args.pop(args.index("follow"))        
        else:
            follow = False

        if len(args):
            destination = args[0]
        else:
            destination = varname

        log.log(2, "showing image with name %s, follow=%s, destination=%s" % (varname, follow, destination))
        self.displaySpecVariable(varname, DATA_2D, follow, destination)
        return True

    def cmd_count(self, cntno):
        self.test_cnt = cntno
        self.test_nb += 1 
        log.log(2, "test count - cntno is %s / nb of times: %s (time elapsed since last time= %3.3f secs)" % \
              (self.test_cnt, self.test_nb, time.time()-self.test_time))
        self.test_time = time.time()
        return True

    def cmd_showVariable(self, varname, follow=False, destination=None):
        try:
            self.displaySpecVariable(varname, DATA_1D, follow, destination)
        except:
            import traceback
            log.log(2, traceback.format_exc())

    def var_setTestVar(self, value):
        self.testch = value
        return True

    def var_getTestVar(self):
        return self.testch

#------- END Command Server and commands --------------------------------------

#------- Moving data around sources


    def requestAddCurve(self, curve):
        addpars = { 'sources': self.getSourceList(current_first=True) }
        options = getAddPlotCurveDialog(self, curve, addpars)

        if options:
            sourcename = options['source']
            self.addCurveToSource(curve,sourcename,options)

    def addCurveToSource(self, curve, sourcename, options):
        # Only valid option now is 'keep'
        if sourcename in self.sources:
            source = self.sources[sourcename]
            source.addExtraCurve(curve, options) 

    def getSourceList(self, current_first=False): 

        srclist = []
        if current_first and self.active_srcname:
            srclist.append(self.active_srcname)

        for srcname in self.sources:
            if current_first and srcname==self.active_srcname:
                continue
            srclist.append(srcname) 

        return srclist

  
#------- END Moving data around sources

    def keyPressEvent(self, event):
        log.debug("key pressed")

        key = event.key()
        if key == Qt.Key_Escape:
            log.debug("ESCAPE")
            source = self.getSource(sourcename)
            #plot = self.getPlot(sourcename)
            #plot.resetZoom()
        elif key == Qt.Key_Up:
            source = self.getSource(sourcename)
            source.next()
        elif key == Qt.Key_Down:
            source = self.getSource(sourcename)
            source.prev()

        return QMainWindow.keyPressEvent(self,event)
  
            
    def helpAbout(self):
        from HelpDialog import AboutDialog
        diag = AboutDialog(self)
        diag.show()

    def openPreferencesDialog(self):
        from PreferencesDialog import PreferencesDialog
        try:
            diag = PreferencesDialog(self)
            diag.set_info(self.cmdsrv.get_info())
        except:
            import traceback
            log.log(2, traceback.format_exc())
        diag.show()
       
    def showLogConsole(self):
        try:
            self.logDialog.show()
        except Exception as e:
            import traceback
            log.log(2, traceback.format_exc())

    def selectSpec(self):
        try:
            connpars = getSpecConnectionParameters(self)
            if connpars:
                self.connectToSpec(connpars)
        except:
            import traceback
            log.log(2, traceback.format_exc())

    def selectSpecVariable(self):
        specname = self.spec_source.getSpecName()
        varpars = getSpecVariableParameters(specname, parent=self)
        if varpars:
            varname, vartype, follow = varpars
            self.displaySpecVariable(varname, vartype, follow)

    def openFileChoose(self):
        lastopenfile = self.prefs['lastopenfile']

        if lastopenfile is None:
            lastopenfile = os.path.join(".", "dummy.txt")

        filename = QFileDialog.getOpenFileName(self, "Open File", lastopenfile)

        log.log(3,"filename selected is: %s " % str(filename))

        if qt_variant() != "PyQt4":
            # in PySide getOpenFileNamNamee returns a tuple
            filename = filename[0]

        if filename:
            self.prefs['lastopenfile'] = filename
            try:
                self.openFile(filename, fromSpec=False)
            except BaseException as e:
                import traceback
                popupError(self, "open file", "problem opening file %s - %s" % (filename, str(e)),
                           moremsg="hint: check that the file has <b>specfile</b> format")
                log.log(3,traceback.format_exc())

    def load_image_file(self, filename, imgformat=None, sourcename=None):
        log.log(2,"image file selected is: %s " % str(filename))
        log.log(2," suggested file format is %s" % imgformat)
        log.log(2," destination source is %s" % sourcename)

        if sourcename is None and filename is not None: 
            self.open_file_source2d(filename, imgformat)
        else:
            source = self.getSource(sourcename) 
            if source: 
                source.open_file(filename, imgformat)

    def open_file_source2d(self, filename,imgformat):
        # Create a new DataSourc2D source
        try:
            msg = None
            source = DataSource2D.DataSource2D(self, \
                    filename=filename,imgformat=imgformat)
        except IOError as e:
            msg = "Cannot open file %s" % filename
            moremsg = "<b>%s</b>" % str(e.strerror)
        except BaseException as e:
            import traceback
            log.log(3, traceback.format_exc())
            log.log(3,"Problem opening file %s" % str(e))
            msg = "Cannot open file %s" % filename
            moremsg = "<b>%s</b>" % str(e)

        if msg:
            ret = popupError(self, "Open file", msg,
                  severity="warning", moremsg=moremsg)
            return

        sourcename = os.path.basename(filename)
        sourcename = self.addSource(source, sourcename)

        self.setActiveSource(source)
        if self.spec_c:
            source.set_connection(self.spec_c)
        return sourcename

    def load_image_data(self):
        try:
            lastimgfile = self.prefs['lastimgfile']

            if lastimgfile is None:
                lastimgfile = self.prefs['lastopenfile']

            sources = []
            for sourcename in self.sources:
                source = self.sources[sourcename]
                if source.is2D():
                    sources.append(sourcename)

            log.log(2, "opening dialog for images file: sources are: %s" % str(sources))
            info = getLoadImageFile(self, lastimgfile, sources)
            if not info:
                return

            log.log(2, "dialog for images file returns: %s" % str(info))
            filename, imgformat, destination = info
    
            if not filename:
                return
    
            self.prefs['lastimgfile'] = filename
        except BaseException as e:
            import traceback
            log.log(2,traceback.format_exc())

        try:
            self.load_image_file(filename, imgformat, destination)
        except BaseException as e:
            import traceback
            popupError(self, "load image", "problem opening image file %s - %s" % (filename, str(e)),
                           moremsg="hint: check that the file has <b>specfile</b> format")
            log.log(3,traceback.format_exc())

