#******************************************************************************
#
#  @(#)AddPlotCurveDialog.py	3.3  12/13/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2020
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

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log
import time


class AddPlotCurveDialog(QDialog):

    def __init__(self, parent, colname, pars):

        QDialog.__init__(self, parent)

        self.setWindowTitle("Add Curve")
        self.setModal(True)

        self.pars = pars

        vBoxLayout = QVBoxLayout()
        self.setLayout(vBoxLayout)

        gridLayout = QGridLayout()
        sourceLabel = QLabel("Source:")
        self.sourceComboBox = QComboBox()
        if 'sources' in self.pars:
              self.sourceComboBox.addItems(self.pars['sources'])

        keepLayout = QHBoxLayout()
        onnewLabel = QLabel("On new scan:")
        self.keepbut = QRadioButton("keep")
        self.forgetbut = QRadioButton("forget")
        self.forgetbut.setChecked(True)

        gridLayout.addWidget(sourceLabel, 0, 0)
        gridLayout.addWidget(self.sourceComboBox, 0, 1)

        keepLayout.addWidget(onnewLabel)
        keepLayout.addWidget(self.keepbut)
        keepLayout.addWidget(self.forgetbut)

        buttonHBoxLayout = QHBoxLayout()

        okPushButton = QPushButton("Ok")
        okPushButton.clicked.connect(self.okPushButtonClicked)

        cancelPushButton = QPushButton("Cancel")
        cancelPushButton.clicked.connect(self.cancelPushButtonClicked)

        buttonHBoxLayout.addWidget(okPushButton)
        buttonHBoxLayout.addWidget(cancelPushButton)

        vBoxLayout.addLayout(gridLayout)
        vBoxLayout.addLayout(keepLayout)
        vBoxLayout.addLayout(buttonHBoxLayout)

    def show(self):
        self.is_open = True
        QDialog.show(self)
    def cancelPushButtonClicked(self):
        self.is_open = False
        self.reject()

    def okPushButtonClicked(self):
        self.is_open = False
        self.accept()

    def getSelection(self):
        self.pars["source"] = str(self.sourceComboBox.currentText())
        self.pars["keep"] = self.keepbut.isChecked()

        return self.pars

# Returns a two value tuple with connpars as first parameter and variable
# name as second parameter


def getAddPlotCurveDialog(parent, curve, pars):

    ycolumn = curve['colname']

    dialog = AddPlotCurveDialog(parent, ycolumn, pars)
    result = dialog.exec_()

    if result == QDialog.Accepted:
         retval = dialog.getSelection()
    else:
         retval = None
     
    dialog.destroy()
    return retval
    
if __name__ == '__main__':

    app = QApplication([])
    curve = {'colname': ['Detector']}
    pars = {}
    ycolumn = 'Detector'
    dialog = AddPlotCurveDialog(None, ycolumn, pars)
    result = dialog.exec_()
    ret = dialog.getSelection()
    print("result is %s " % ret)

    if result == QDialog.Accepted:
       print("Adding curve. with parameters: %s" % str(pars))
    else:
       print("Bye")
