#******************************************************************************
#
#  @(#)HelpDialog.py	3.5  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2020,2023,2024
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

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log

from SPlotBrowser import SPlotBrowser

class HelpDialog(QDialog):

    def __init__(self, parent=None, filename=None):

        QDialog.__init__(self, parent)

        self.setWindowTitle("SPEC Plot Help")
        self.setModal(False)

        self.resize(500, 500)
        layout = QGridLayout()
        layout.setContentsMargins(1, 1, 1, 1)

        self.title = QLabel("Title")

        self.content = SPlotBrowser(parent)

        self.closeButton = QPushButton("Close")
        self.closeButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.closeButton.clicked.connect(self.closeButtonPressed)

        layout.addWidget(self.title, 0, 0)
        layout.addWidget(self.content, 1, 0)
        layout.addWidget(self.closeButton, 2, 0, Qt.AlignRight)

        self.setLayout(layout)

        if filename is not None:
            self.content.showFile(filename)

    def setTitle(self, title):
        self.title.setText(title)

    def closeButtonPressed(self):
        self.accept()

    def loadFile(self,filename):
        self.content

    def loadAbout(self):
        about_path = os.path.join(self.html_path, 'about.html')
     
        if os.path.exists(about_path):
            self.about_template = open(about_path).read()

            # ignore anything before the initial html tag
            idxhtml = self.about_template.find("<html>")
            if idxhtml > 0: 
                self.about_template = self.about_template[idxhtml:]

            self.aboutText()
        else:
            print("Cannot find about file")

class AboutDialog(HelpDialog):

    def __init__(self, parent=None):
        HelpDialog.__init__(self, parent)
        self.title.setText("")
        self.content.about()

    def anchorClicked(self, url):
        if os.path.basename(str(url.toString())).endswith("about.html"):
            self.toggleVersion()
            self.aboutText()
            return

        self.shortVersion = False
        HelpDialog.anchorClicked(self, url)

def showHelpDialog(parent):

    dialog = AboutDialog(parent)
    result = dialog.exec_()
    dialog.destroy()
    return None
    
if __name__ == '__main__':

    app = QApplication([])
    dialog = AboutDialog(None)
    dialog.show()

    try:
        exec_ = getattr(app,"exec_")
    except AttributeError:
        exec_ = getattr(app,"exec")
    exec_()

