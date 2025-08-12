#******************************************************************************
#
#  @(#)DataSource.py	3.18  01/09/24 CSS
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

import numpy as np

from pyspec.graphics.QVariant import *
from pyspec.graphics import qt_variant
from Constants import *
from pyspec.css_logger import log
from pyspec.utils import is_windows, is_unity, is_macos

import icons
import themes
from Preferences import Preferences


try:
   from xraise import xraise_id
except ImportError:
   log.log(1,"Cannot import xraise. Using dummy")
   def xraise_id(*args):
       pass


cssname = "app.css"
cssfile = os.path.join(os.path.dirname(__file__), cssname)

from Preferences import Preferences

class DataSource(QWidget):

    sourceActivated = pyqtSignal(object)
    configurationChanged = pyqtSignal(object)

    def __init__(self, app, sourcetype, name):
        QWidget.__init__(self)

        self.app = app
        self.setName(name)
        self.sourcetype = sourcetype

        self.detachmode = False
        self.sourcename = None

        self.showing_info = True

        self.menubar = None
        self.menubar_set = None

        self.plot_w = None

        self.prefs = Preferences()

        self._init_data()
        self._init()
        self._init_widget()

    def _init(self):
        self.active = False
        self.errorflag = None
        self.init()

    def init(self):
        """ 
        STUB. To be filled up by implementing class
        Description:
           Allow sources to initialize private data
           before graphics are created.
        """
        pass

    def _init_data(self):
        self.init_data()

    def _init_widget(self):
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.main_splitter = QSplitter()
        self.main_splitter.setOrientation(Qt.Vertical)

        self.splitter = QSplitter()
        self.splitter.setObjectName("sourcesplitter")

        self.splitter_pos = int(self.prefs.getValue("sourcewidth",320))

        self.splitter.splitterMoved.connect(self.splitterMoved)

        self.main_splitter.addWidget(self.splitter)
        layout.addWidget(self.main_splitter, 1, 0)

        self.installEventFilter(self)

        #
        self._init_source_area()
        self._init_graphics_area()

        self.init_widget()

        QTimer.singleShot(500, self._check_preferences)
        self.splitter_handle = self.splitter.handle(1)
        if self.splitter_handle:
            self.splitter_handle.installEventFilter(self)

    def _init_source_area(self):
        self.sourceLayout = QGridLayout()
        self.sourceSide = QWidget()
        self.sourceSide.setLayout(self.sourceLayout)

        self.sourceSide.setMaximumWidth(460)
        self.sourceSide.setMinimumWidth(200)

        self.splitter.setSizes([300, 600])

        self.tabs = QTabWidget(self.sourceSide)
        self.splitter.addWidget(self.sourceSide)
        self.sourceLayout.addWidget(self.tabs,1,0)

        self.init_source_area()

    def _init_graphics_area(self):
        self.plot_w = self.init_graphics_area()
        if self.plot_w:
            self.splitter.addWidget(self.plot_w)

    def init_data(self):
        """ 
        STUB. To be filled up by implementing class
        Description:
           Allow for some sources to set data directly
           at instantiation time. Called after graphics
           is initialized
        """
        pass

    def init_widget(self):
        """ 
        STUB. To be filled up by implementing class
        Description:
           Allow sources to initialize their own 
           graphics area.
           methods:
               set_source_header_widget()
            and
               add_source_tab()
            allow implementing classes to modify
            the standard source widget area
        """
        pass

    def init_source_area(self):
        pass

    def init_graphics_area(self):
        return None

    def set_source_header_widget(self, widget):
        #self.sourceLayout.insertWidget(0, widget)
        self.sourceLayout.addWidget(widget,0,0)

    def add_source_tab(self, position, widget, label):
        self.tabs.insertTab(position, widget, label) 

    def _check_preferences(self):
        self.applyTheme()

        prefname = "source_%s" % self.getTypeString()

        if self.prefs.getValue(prefname,"show") == "hide":
            self.showing_info = False
        else:
            self.showing_info = True

        if self.showing_info:
            self.openSplitter()
        else:
            self.closeSplitter()

        self.check_preferences()

    def check_preferences(self):
        pass

    def applyTheme(self):
        self.theme = themes.get_theme(self.prefs.getValue("theme",None))
   
    def getPlotWidget(self):
        return self.plot_w

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def getDisplayName(self):
        return self.name

    def getSourceName(self):
        return self.sourcename

    def setSourceName(self, sourcename):
        self.sourcename = sourcename

    def getTypeString(self):
        return "source"

    def getType(self):
        return self.sourcetype

    def setActive(self):
        if self.active:
            return

        self.active = True

        if self.plot_w:
            self.plot_w.setActive()
        self.sourceActivated.emit(self)

    def setInactive(self):
        self.active = False

        if not self.isDetached():
            if self.plot_w:
                self.plot_w.setInactive()

    def is1D(self):
        return (self.sourcetype & SOURCE_1D) and True or False

    def is2D(self):
        return (self.sourcetype & SOURCE_2D) and True or False

    def isMCA(self):
        return (self.sourcetype & SOURCE_MCA) and True or False

    def isActive(self):
        return self.active

    def eventFilter(self, obj, ev):
        try:
            activate_ev = QEvent.WindowActivate
            release_ev = QEvent.MouseButtonRelease
        except AttributeError:
            activate_ev = QEvent.Type.WindowActivate
            release_ev = QEvent.Type.MouseButtonRelease

        if ev.type() == activate_ev:
            self.setActive()
            return True
        elif ev.type() == release_ev and obj is self.splitter_handle:
            splitter_pos = self.splitter.sizes()[0]
            if splitter_pos != 0:
                self.prefs.setValue("sourcewidth",splitter_pos)
            return True
        else:
            return False

    def closeEvent(self, e):
        self.attachMe()

    def xraise(self):
        if is_macos():
            log.log(3,"   raising window on mac ignored. needs cocoa, not x11")
            return
        #elif is_unity():
            #log.log(3,"   raising window on Unity ignored. needs rewriting")
            #return

        if self.isDetached():
            xraise_id(self.winId(), 2, 0)
        else:
            xraise_id(self.app.winId(), 2, 0)

    def update_menubar(self, menubar):
        pass

    def setDetachMode(self, flag):

        if flag == self.detachmode:
            return

        self.saveGeometry()
        self.detachmode = flag

        self.setWindowTitle("splot for spec: %s" % self.getSourceName())

        try:
            if flag:
                self.showPrivateMenubar()
                try:
                    self.setParent(None, Qt.Dialog)
                    self.setWindowModality(False)
                    self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)
                except AttributeError:
                    self.setParent(None, Qt.WindowType.Dialog)
                    self.setWindowModality(Qt.WindowModality.WindowModal)
                    self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)

                self.setStyleSheet(open(cssfile).read())
                self.restoreGeometry()
                flags = self.windowFlags()
                log.log(2, "detached. flags are 0x%x" % flags)
                self.show()
            else:
                self.hidePrivateMenubar()
                self.hide()
                self.app.addSourceTab(self, self.sourcename)
        except:
            import traceback
            log.log(2, traceback.format_exc())

        if not self.plot_w: 
            return

        if self.detachmode:
            self.plot_w.setActive()
        else: 
            if self.active:
                self.plot_w.setActive()
            else:
                self.plot_w.setInactive()

    def attachMe(self):
        self.setDetachMode(False)
        self.app.updateDetached()

    def detachMe(self):
        self.setDetachMode(True)
        self.app.updateDetached()

    def isDetached(self):
        return self.detachmode

    def attachWhenClosing(self):
        return True

    def getDescription(self):
        return self.getSourceName()

    def openSplitter(self):
        self.showing_info = True
        self.splitter.moveSplitter(self.splitter_pos, 1)
        prefname = self.getTypeString()
        self.prefs.setValue("source_%s" % prefname,"show")
        if self.plot_w:
            self.plot_w.setTitle("")
        self.emit_configuration_changed()

    def closeSplitter(self):
        self.showing_info = False
        self.splitter.moveSplitter(0, 1)
        prefname = self.getTypeString()
        self.prefs.setValue("source_%s" % prefname,"hide")
        if self.plot_w:
            self.plot_w.setTitle(self.getName())
        self.emit_configuration_changed()

    def isSourceInfoVisible(self):
        return self.showing_info 
 
    def saveGeometry(self):

        if not self.isDetached():
            return

        sourcename = self.getSourceName()
        prefs = Preferences()
        prefgeo = "geometry_%s" % sourcename
        geo = self.geometry()
        x = geo.x()
        y = geo.y()
        w = geo.width()
        h = geo.height()
        prefs.setValue(prefgeo,"%d,%d,%d,%d" % (x, y, w, h))

    def restoreGeometry(self):
        if not self.isDetached():
            return

        sourcename = self.getSourceName()
        prefs = Preferences()
        prefgeo = "geometry_%s" % sourcename

        geo = prefs.getValue(prefgeo, "200,200,800,600")  # default

        if prefs[prefgeo]:
            x, y, width, height = map(int, geo.split(","))
            self.move(x, y)
            self.setGeometry(x, y, width, height)

    def getMenuBarSet(self):
        return self.menubar_set

    def showPrivateMenubar(self):
        if self.menubar is None:
            self.createPrivateMenuBar()
            #if is_unity(): 
            self.layout().setMenuBar(self.menubar)

        self.menubar.show()

        self.app.updateMenuBar(self)
        self.layout().addWidget(self.menubar, 0, 0)

    def hidePrivateMenubar(self):
        self.menubar.hide()

    def createPrivateMenuBar(self):
        self.menubar = QMenuBar()
        log.log(2, "creating private menubar %s" % str(self.app))
        self.menubar_set = self.app.createMenuBarSet(self.menubar)

        self.menubar.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.layout().addWidget(self.menubar, 0, 0)

    def emit_configuration_changed(self):
        self.configurationChanged.emit(self)

    def close(self):
        self.active = False

    def splitterMoved(self, pos, idx):
        if (not self.showing_info) and pos > 100:
            self.openSplitter()

        if self.showing_info and pos < 100:
            self.closeSplitter()

    def toggleSourceInfoView(self):
        if self.showing_info:
            self.closeSplitter()
        else:
            self.openSplitter()

def main_test():
    app = QApplication([])
    win = QMainWindow()
    wid = DataSource(None, SOURCE_ANY, "Test")
    print("widget created")
    win.setWindowTitle('Data Source dumb test')

    win.setCentralWidget(wid)
    win.setGeometry(200, 100, 400, 400)
    win.show()

    try:
        sys.exit(app.exec_())
    except AttributeError:
        run = getattr(app, "exec")
        sys.exit(run())

if __name__ == '__main__':
    main_test()

