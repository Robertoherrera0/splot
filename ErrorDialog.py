#******************************************************************************
#
#  @(#)ErrorDialog.py	3.4  01/09/24 CSS
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
from pyspec.graphics import qt_variant

if qt_variant() in ['PyQt6']:
    icons = {
        'question':  QMessageBox.Icon.Question,
        'info':      QMessageBox.Icon.Information,
        'warning':   QMessageBox.Icon.Warning,
        'critical':  QMessageBox.Icon.Critical,
    }
    close_but = QMessageBox.StandardButton.Close
    rich_text = Qt.TextFormat.RichText
    is_accepted = QDialog.DialogCode.Accepted
else:
    icons = {
        'question':  QMessageBox.Question,
        'info':      QMessageBox.Information,
        'warning':   QMessageBox.Warning,
        'critical':  QMessageBox.Critical,
    }
    close_but = QMessageBox.Close
    rich_text = Qt.RichText
    is_accepted = QDialog.Accepted

def popupError(parent, title, msg, severity='critical', moremsg=None):
    dialog = QMessageBox(parent)
    dialog.setIcon(icons[severity])
    dialog.setWindowTitle("splot / " + title)
    dialog.setStandardButtons(close_but)
    dialog.setTextFormat(rich_text)
    dialog.setText(msg)
    # work around to resize dialog (width)
    horizontalSpacer = QSpacerItem(
        350, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
    layout = dialog.layout()
    layout.addItem(horizontalSpacer, layout.rowCount(),
                   0, 1, layout.columnCount())
    if moremsg:
        dialog.setInformativeText('<i>' + moremsg + '</i>')

    try:
        exec_ = getattr(dialog, "exec_")
    except AttributeError:
        exec_ = getattr(dialog, "exec")
    result = exec_()
    dialog.destroy()

    if result == is_accepted:
        return None

if __name__ == '__main__':

    app = QApplication([])
    win = QMainWindow()
    bla = QWidget()
    lay = QVBoxLayout()
    bla.setLayout(lay)
    but = QPushButton("push me")
    lab = QLineEdit()
    lay.addWidget(lab)
    lay.addWidget(but)
    win.setCentralWidget(bla)

    def showit():
        text = lab.text()
        dialog = popupError(None, "Open File", text,
                            severity="question", moremsg="sorry for that")

    but.clicked.connect(showit)
    win.show()

    try:
        exec_ = getattr(app,"exec_")
    except AttributeError:
        exec_ = getattr(app,"exec")
    exec_() 
