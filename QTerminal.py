#!/usr/bin/env python
#-*- coding:utf-8 -*-
#******************************************************************************
#
#  @(#)QTerminal.py	3.3  04/28/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2017,2020
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

from Features import setFeature

try:
    from Xlib import display
except:
    setFeature("embed_xterm", False)

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log
import distutils.spawn

XTERM_CMD = 'xterm'

class QTerminal(QWidget):

    exited = pyqtSignal()
    margin = 2

    def __init__(self, specname):

        self.ready_to_resize = False
        self.specname = specname

        QWidget.__init__(self)
        self.termProcess  = QProcess(self)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        QTimer.singleShot(1000, self.do_start)
        getQApp().aboutToQuit.connect(self.stopProcess)
       
    def start(self):
        
        log.log(3,"Starting %s in terminal" % self.specname)

        if not distutils.spawn.find_executable(XTERM_CMD):
            log.log(3,"Cannot find xterm command %s in computer" % XTERM_CMD)
            return

        winid = int(self.winId())
        xterm_args = ['-bg', 'white', '-fg', 'black']
        xterm_args.extend(['-name', 'Spec'])
        xterm_args.extend(['-j', '-into', str(winid), '-e', self.specname, '-S']) 

               
        self.termProcess.start(
            XTERM_CMD, 
            xterm_args
        )
        if self.termProcess.waitForStarted():
            success = True
            print("Process started")
        else:
            success = False

        if success is True:
            print("resizing terminal")

        return success

    def resizeEvent(self,ev):
        QWidget.resizeEvent(self,ev)
        self.resizeTerminal()

    def do_start(self):
        """
        Theres is a timing issue here so that it works with any
         PyQt4 or PyQt5
        """
        self.ready_to_resize = True
        self.start()
        QTimer.singleShot(300, self.resizeTerminal)
        #self.resizeTerminal()

    def resizeTerminal(self):
        if not self.ready_to_resize:
            return

        winid = int(self.winId())
        width = self.width()
        height = self.height()

        # use Xlib to resize the embedded terminal
        dpy = display.Display()
        win = dpy.create_resource_object('window', winid)
        win.configure(width=width,height=height)
        children = win.query_tree().children
        if len(children):
            children[0].configure(width=width-2*self.margin,height=height-2*self.margin)
            
        dpy.sync()

    # process control
    def closeEvent(self, ev):
        self.stopProcess()
        ev.accept()

    def isRunning(self):
        return self.termProcess and self.termProcess.state() == QProcess.Running

    def stopProcess(self):
        if not self.tryTerminate():
            print("Warning, cannot terminate process")

    def tryTerminate(self):
        if self.isRunning():
            self.termProcess.terminate()
            return self.termProcess.waitForFinished()
        return True

    def termProcessExited(self):
        if not self.termProcess:
            return

        del self.termProcess
        self.termProcess = None
        self.exited.emit()

if __name__ == "__main__":
    specname = sys.argv[1]
    app = QApplication(sys.argv)

    main = QWidget()

    lay = QVBoxLayout()
    lay.setContentsMargins(2,2,2,2)
    lab = QLabel("Running: %s" % specname)      
    term = QTerminal(specname)
    lay.addWidget(lab)
    lay.addWidget(term)
    lay.setStretchFactor(term, 100)

    #term.start()

    main.resize(640,480)
    main.setLayout(lay)

    main.show()
    sys.exit(app.exec_())

    #main = embeddedTerminal()
    #main.show()
    #sys.exit(app.exec_())
