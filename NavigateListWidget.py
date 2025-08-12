#******************************************************************************
#
#  @(#)NavigateListWidget.py	3.5  10/01/20 CSS
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

from pyspec.graphics.QVariant import *

class NavigateListWidget(QWidget):

    valueChanged = pyqtSignal(int)

    def __init__(self, label="", nbitems=0, *args):

        super(NavigateListWidget,self).__init__(*args)

        self.current_idx = None
        self.nbitems = nbitems
        self.label = label

        self._layout = QHBoxLayout()

        self._label = QLabel(label)
        self._label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._current = QSpinBox()
        self._current.setAlignment(Qt.AlignRight)
        self._total = QLabel()

        self._current.valueChanged.connect(self.changed)

        self._layout.addWidget(self._label)
        self._layout.addWidget(self._current)
        self._layout.addWidget(self._total)

        self.setLayout(self._layout)

        self.setNumberOfItems(self.nbitems)

    def setNumberOfItems(self,nbitems):
        tot_str = "/%s" % nbitems
        self.nbitems = nbitems
        self._total.setText(tot_str)
        self._current.setMinimum(1)
        self._current.setMaximum(self.nbitems)
        self.setCurrentItem(nbitems-1)

    def setCurrentItem(self, idx):
        self.current_idx = idx
        self._current.setValue(idx+1)

    def changed(self, newvalue):
        if newvalue > 0 and newvalue <= self.nbitems:
            self.current_idx = newvalue-1
            self.valueChanged.emit(self.current_idx)

def test():

    def item_selected(itemno):
        print( itemno, " selected")
  
    app = QApplication([])
    win = QMainWindow()
    wid = NavigateListWidget("Slice:", 100)
    wid.valueChanged.connect(item_selected)
    wid.setNumberOfItems(1000)
    #wid.setCurrentItem(4)
    win.setCentralWidget(wid)  
    win.show()
    app.exec_()

if __name__ == '__main__':
   test()
