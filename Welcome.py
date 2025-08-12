#******************************************************************************
#
#  @(#)Welcome.py	3.4  04/28/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2020
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
from SPlotBrowser import SPlotBrowser

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log

class Welcome(SPlotBrowser):

     
    sourceActivated = pyqtSignal(object)

    def __init__(self, parentwindow):
        super(Welcome, self).__init__(parentwindow)

    def isDetached(self):
        return False

    def getSourceName(self):
        return "Welcome"

    def setActive(self):
        self.sourceActivated.emit(self)

    def setInactive(self):
        self.sourceActivated.emit(self)

def main_test():

    app = QApplication([])
    win = QMainWindow()
    wid = Welcome(None)
    wid.welcome()
    win.setWindowTitle('Welcome to SPLOT')

    win.setCentralWidget(wid)
    win.setGeometry(200, 100, 400, 400)
    win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main_test()
