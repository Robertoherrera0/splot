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

def getPrinter(prefs=None,mute=False,parent=None, filename=None):
    printer = QPrinter()

    try:
        landscape = QPrinter.Landscape
        grayscale = QPrinter.GrayScale
    except AttributeError:
        landscape = QPageLayout.Orientation.Landscape
        grayscale = QPrinter.ColorMode.GrayScale

    try:
        custom = QPrinter.Custom
        letter = QPrinter.Letter
    except AttributeError:
        try:
            custom = QPageSize.Custom
            letter = QPageSize.Letter
        except AttributeError:
            custom = QPageSize.PageSizeId.Custom
            letter = QPageSize.PageSizeId.Letter
    

    if not prefs:
        prefs = Preferences()

    if 'printer_name' in prefs.keys():
        printer.setPrinterName(prefs['printer_name'])

    printer_orientation = prefs.getValue('printer_orientation', None)

    if printer_orientation is not None:
        if qt_variant() == 'PySide':
            printer_orientation = QPrinter.Orientation.values.get(printer_orientation, landscape)
        else:  # qt_variant PyQt4 or PyQt5 or PySide2
            try:
                printer_orientation = int(printer_orientation)  
            except:
                printer_orientation = landscape
    else:
        printer_orientation = landscape

    try:
        printer.setOrientation(printer_orientation)
    except AttributeError:
        printer.setPageOrientation(printer_orientation)

    outfilename = prefs.getValue('printer_outputfilename')
    if outfilename:
        printer.setOutputFileName(outfilename)

    psize = prefs.getValue('printer_papersize', None)
    if psize is not None:
        if qt_variant() == 'PySide':
            psize = QPrinter.PageSize.values.get(psize, None)
        else:  # qt_variant PyQt4 or PyQt5 or PySide2
            try:
                psize = int(psize)  
            except:
                psize = None

    if psize is not None:
        # Protect from buggy "Custom" support (=30)
        if psize == custom:
            psize = letter  # Letter
        printer.setPageSize(psize)

    pcolor = prefs.getValue('printer_colormode',None)

    if pcolor is not None: 
        if qt_variant() == 'PySide':
            pcolor = QPrinter.ColorMode.values.get(pcolor, QPrinter.GrayScale)
        else:  # qt_variant PyQt4 or PyQt5 or PySide2
            try:
                pcolor = int(pcolor)
            except:
                pcolor = grayscale
    else:
        pcolor = grayscale

    printer.setColorMode(pcolor)

    if not mute:
        printDialog = QPrintDialog(printer,parent)
 
        try:
            ret = printDialog.exec_() 
            accepted = QDialog.Accepted
        except AttributeError:
            exec_ = getattr(printDialog, "exec")
            ret = exec_()
            accepted = QDialog.DialogCode.Accepted
             
        if ret != accepted:
            log.log(2, " not accepted")
            return None

        log.log(2, "saving printing preferences")

        colormode = printer.colorMode()
        try:
            psize = printer.paperSize()
            orientation = printer.orientation()
        except AttributeError:
            psize = printer.pageLayout().pageSize().id()
            orientation = printer.pageLayout().orientation()

        if psize == custom:
            psize = letter

        if qt_variant() in ['PySide', 'PySide6', 'PyQt6']:
            prefs['printer_orientation'] = orientation.name
            prefs['printer_papersize'] = psize.name
            prefs['printer_colormode'] = colormode.name
        else:
            prefs['printer_orientation'] = orientation
            prefs['printer_papersize'] = psize
            prefs['printer_colormode'] = colormode
        try:
            prefs['printer_outputfilename'] = printer.outputFileName()
        except Exception:
            pass

    else:
        if filename:
            if str(filename).endswith(".pdf"):
                printer.setOutputFileName(filename)
            else:
                printer.setOutputFileName(filename + ".pdf")
        elif not printer.isValid():
            log.log(3,"invalid printer %s" % prefs['printer_name'])
            return None

    return printer


if __name__ == '__main__':
    from pyspec.graphics.QVariant import QApplication
    app = QApplication([])
    filename = getSaveFile(None, "choose maifail", "Image files (*.jpg *.png);;ALL (*)")
    print(filename)
