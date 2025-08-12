#******************************************************************************
#
#  @(#)SPlotBrowser.py	3.7  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2020,2023,2024
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

import VERSION 

from pyspec.graphics.QVariant import *
from pyspec.graphics import qt_version
from pyspec.css_logger import log

class SPlotBrowser(QTextBrowser):

    welcome_message = "welcome.html"
    about_file = "about.html"
    not_found = "not_found.html"

    def __init__(self, app):
        super(SPlotBrowser, self).__init__(app)

        self.app = app
        self.html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'html')
        self.setStyleSheet("background-color: white")
    
        self.setOpenLinks(False)
        self.setOpenExternalLinks(True)
        #self.setTextInteractionFlags(Qt.TextSelectableByMouse)

        log.log(2,"Setting html_path to %s" % self.html_path)
        self.setSearchPaths([self.html_path])

        self.short_version = True
        self.version_short = VERSION.getVersion()
        self.version_long =  VERSION.getFullVersion()
        self.version_str = self.version_short

        self.previous_url = None

        self.anchorClicked.connect(self._anchorClicked)

    def about(self):
        self.showFile(self.about_file, build=True)

    def welcome(self): 
        self.showFile(self.welcome_message, build=True)

    def _anchorClicked(self, url):

        url_str = str(url.toString())
        #url_file = str(url.fileName())
        url_file = str(url.path())

        if url_file.strip() != "":
            is_local = os.path.exists(self.get_file_path(url_file))
        else:
            is_local = False

        if qt_version()[0] >= 5:
            query = QUrlQuery(url)
            toggle_version = query.queryItemValue("toggleversion")
        else:
            toggle_version = url.encodedQueryItemValue("toggleversion")

        if toggle_version == "1":
            self.toggleVersion()
        else: 
            self.toggleVersion(short=True)

        if url_str.endswith("back"):
            self.backward()
        elif url_str.find(".action") != -1:
            self.handleApplicationAction(url_str, url)
        elif is_local:
            if url_str.startswith("about.html"):
                self.about()
            elif url_str.startswith("welcome.html"):
                self.welcome()
            else:
                self.showFile(url_str)
        else:
            QDesktopServices.openUrl(url)

    def toggleVersion(self,short=False):
        if short:
            self.short_version = True
        else:
            self.short_version = not self.short_version
        
        if self.short_version:
            self.version_str = self.version_short
        else:
            self.version_str = self.version_long

    def handleApplicationAction(self, action, url):
        action_name = action[:action.index(".action")] 

        if action_name == "loadfile":
            self.app.openFileChoose()
        elif action_name == "loadimage":
            self.app.load_image_data()
        elif action_name == "createnew":
            self.app.createNewSource()
        elif action_name == "connect":
            self.app.selectSpec()

    def get_file_path(self, filename):
        return os.path.join(self.html_path, filename) 

    def showFile(self,filename, build=False, values=None):

        if not build:
            self.setSource(QUrl(filename))
        else:
            template_file = self.get_file_path(filename)
            if not os.path.exists(template_file):
                log.log(1,"Trying to load a non-existent file %s" % filename)
                return
            template = open(template_file).read()
            idxhtml = template.find("<html>")
            if idxhtml > 0:
                template = template[idxhtml:]

            fields = {'version': self.version_str}
            fields.update(app_libraries())
            if values is not None:
                fields.update(values)
            content = template % fields
            self.setHtml(content)

class Welcome(SPlotBrowser):

    def __init__(self, app):
        super(Welcome, self).__init__(app)
        self.createMenus()

    def createMenus(self):
        self.fileMenu = QMenu("&File")

        self.connectToRemoteAction = QAction('&Remote', self)
        self.connectToRemoteAction.setStatusTip('Connect to Remote SPEC')
        
        self.connectToRemoteAction.triggered.connect(
                self.app.connectSpecRemote)

        self.openSpecMenu = QMenu('Connect to SPEC')
        self.openSpecMenu.setStatusTip('Connect to SPEC')

        self.openFileAction = QAction('&Open SPEC File', self)
        self.openFileAction.setStatusTip('Open SPEC File')
        self.openFileAction.triggered.connect(self.app.openFileChoose)

        self.loadImageAction = QAction('&Load Image Data', self)
        self.loadImageAction.setStatusTip('Open File')
        self.loadImageAction.triggered.connect(self.app.load_image_data)

        self.helpAction = QAction('&About splot', self)
        self.helpAction.setShortcut('Ctrl+H')
        self.helpAction.setStatusTip('About')
        
        self.helpAction.triggered.connect(self.app.helpAbout)

        self.exitAction = QAction('&Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.app.appQuit)

        self.newSourceAction = QAction('&New', self)
        self.newSourceAction.setStatusTip('Create new empty graph')
        self.newSourceAction.triggered.connect(self.app.createNewSource)

        self.fileMenu.addMenu(self.openSpecMenu)

        self.helpMenu = QMenu("&Help")

        self.helpMenu.addAction(self.helpAction)

    def setActive(self):
        self.updateMenuBar()

    def updateMenuBar(self):
        self.menubar = self.app.menuBar()
        menubar = self.menubar
        menubar.clear()
  
        menubar.addMenu(self.fileMenu)
        menubar.addMenu(self.helpMenu)

        self.newSourceAction.setDisabled(False)

        self.app.fillSpecMenu(self.openSpecMenu)

        self.fileMenu.addActions([self.newSourceAction, self.openFileAction, self.loadImageAction, self.exitAction])

        self.fileMenu.setDisabled(False)
        self.helpMenu.setDisabled(False)



def main_test():

    app = QApplication([])
    win = QMainWindow()
    wid = Welcome(None)
    wid.welcome()
    win.setWindowTitle('Welcome to SPLOT')

    win.setCentralWidget(wid)
    win.setGeometry(200, 100, 400, 400)
    win.show()

    try:
        exec_ = getattr(app,"exec_")
    except AttributeError:
        exec_ = getattr(app,"exec")

    sys.exit(exec_())

if __name__ == '__main__':
    main_test()
