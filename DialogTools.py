#******************************************************************************
#
#  @(#)DialogTools.py	3.2  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2020,2023,2024
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
from pyspec.graphics import qt_variant
from pyspec.css_logger import log

from Preferences import Preferences

import os

def getSaveFile(parent=None, prompt=None, filetypes="", prefs=None):
    if prompt == None:
        prompt = "File name"

    if not prefs:
        prefs = Preferences()

    dirname = prefs.get('savedir',os.getenv("HOME"))

    user_select = QFileDialog.getSaveFileName(parent, prompt, dirname, filetypes)

    if type(user_select) in [list,tuple]:
        filename = str(user_select[0])
    else:
        filename = str(user_select)

    if filename:
        dirname = os.path.dirname(os.path.abspath(filename))
        if os.path.isdir(dirname):
            prefs['savedir'] = dirname
            prefs.save()

    return filename
def getPrinter(prefs=None, mute=False, parent=None, filename=None):
    """
    Safe printer dialog for both legacy (matplotlib) and modern (Plotly) backends.
    Under Wayland, this will never block or crash.
    """
    import os
    from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPageLayout, QPageSize, QAbstractPrintDialog
    from PySide6.QtWidgets import QFileDialog, QColorDialog, QDialog

    # --- If running Plotly backend (non-legacy), skip the Qt printer entirely ---
    if os.environ.get("GANS_BACKEND", "").lower() == "plotly":
        print("[INFO] Plotly backend detected: skipping legacy QPrintDialog.")
        return None

    printer = QPrinter()

    # Fallback for systems without portals (Wayland or headless)
    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        print("[INFO] Wayland session detected: using internal non-native print dialog.")
        dialog = QPrintDialog(printer, parent)
        dialog.setOption(QAbstractPrintDialog.DontUseNativeDialog, True)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return printer

    # Normal path for X11 or full desktops
    dialog = QPrintDialog(printer, parent)
    dialog.setWindowModality(Qt.ApplicationModal)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return printer



if __name__ == '__main__':
    from pyspec.graphics.QVariant import QApplication
    app = QApplication([])
    filename = getSaveFile(None, "choose maifail", "Image files (*.jpg *.png);;ALL (*)")
    print(filename)
