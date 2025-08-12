#******************************************************************************
#
#  @(#)LoadImageDialog.py	3.3  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2018,2020,2023,2024
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

from ErrorDialog import popupError

import os

class LoadImageDialog(QDialog):

    known_suffixes  = {
                'h5': 'HDF5',
                'hdf5': 'HDF5',
                'tif': 'TIFF',
                'tiff': 'TIFF',
                'itx': 'ITEX',
      }


    new_label = '-- create new --'
    def __init__(self, parent):

        QDialog.__init__(self, parent)

        self.filedir = None
        self.filename = None

        self.setWindowTitle("Load Image")
        self.setModal(True)

        vBoxLayout = QVBoxLayout()
        self.setLayout(vBoxLayout)

        gridLayout = QGridLayout()

        file_label = QLabel("File:")
        self.file_entry = QLineEdit()
        self.file_entry.textChanged.connect(self.filename_changed)

        file_bt = QPushButton('...')
        file_bt.clicked.connect(self.select_file)

        format_label = QLabel("Format:")
        self.format_cbox = QComboBox()
        self.format_cbox.addItems(self.get_formats())
  
        self.dest_label = QLabel("Open in tab:")
        self.dest_cbox = QComboBox()

        gridLayout.addWidget(file_label, 0, 0)
        gridLayout.addWidget(self.file_entry, 0, 1,1,2)
        gridLayout.addWidget(file_bt, 0, 3)

        gridLayout.addWidget(format_label,1,0)
        gridLayout.addWidget(self.format_cbox,1,1)
        gridLayout.addWidget(self.dest_label,1,2)
        gridLayout.addWidget(self.dest_cbox,1,3)

        buttonHBoxLayout = QHBoxLayout()

        okPushButton = QPushButton("Load")
        okPushButton.clicked.connect(self.okPushButtonClicked)

        cancelPushButton = QPushButton("Cancel")
        cancelPushButton.clicked.connect(self.cancelPushButtonClicked)

        buttonHBoxLayout.addWidget(okPushButton)
        buttonHBoxLayout.addWidget(cancelPushButton)

        vBoxLayout.addLayout(gridLayout)
        vBoxLayout.addLayout(buttonHBoxLayout)

    def filename_changed(self, filename):
        if os.path.sep not in filename:
            fff = os.path.join(self.filedir,filename)
        else:
            fff = filename
        self.set_filename(fff)

    def set_filename(self, filename):
        if filename is None:
            return
        self.filename = str(filename)
        self.filedir = os.path.dirname(filename)
        self.file_entry.setText(os.path.basename(filename))

        suffix = self.get_suffix(filename)

        ftype = self.known_suffixes.get(suffix,None)
        if ftype:
            self.suffix = suffix
            try:
                self.format_cbox.setCurrentText(ftype)
            except AttributeError:   # qt 4.6 or sooner
                pass

    def set_sources(self, sources):
        self.dest_cbox.clear()
        if sources:
            sources.append(self.new_label)
            self.dest_cbox.addItems(sources)

        self.sources = sources
        
    def get_filter(self, suffix):
        ftype = self.known_suffixes.get(suffix, None)

        if not ftype:
            return None

        sufx_list = ["*"+sufx for sufx,ftyp in 
             self.known_suffixes.items()
             if ftyp == ftype]

        _filter = "%s (%s)" % (ftype, " ".join(sufx_list))
        return _filter

    def get_all_filters(self):

        _all_filters = [self.get_filter(sfx) 
                for sfx in self.known_suffixes.keys()]

        _all_filters = list(set(_all_filters))
        _all_filters.append("ALL (*)")

        return ";;".join(_all_filters)

    def get_formats(self,filename=None):
        format_list = [ftyp for sufx,ftyp in self.known_suffixes.items() ]
        format_list = list(set(format_list))
        return format_list


    def get_suffix(self,filename=None):
        if filename is None:
            filename = self.file_entry.text()

        suffix = None
        if str(filename):
            try:
                suffix = os.path.splitext(str(filename))[1][1:]
            except:
                pass
        
        return suffix

    def select_file(self):
        last_selected = self.file_entry.text()

        sfx = self.get_suffix()
        filters = self.get_all_filters()
        selected_filter = self.get_filter(sfx)
        if selected_filter is None:
            selected_filter = "ALL (*)"
        
        filename = QFileDialog.getOpenFileName(self, "Open Image File", self.filedir, filters, selected_filter)

        if qt_variant() != "PyQt4":
            # in PySide getOpenFileNamNamee returns a tuple
            filename = filename[0]

        if filename:
            self.set_filename(filename)

    def cancelPushButtonClicked(self):
        self.reject()

    def okPushButtonClicked(self):
        if self.filename and not os.path.exists(self.filename):
            popupError(self, "File Error", 
                    "file %s does not exist" % self.filename, 
                    severity="warning")
            return
        else:
            self.accept()

    def get_values(self):
        img_format = self.format_cbox.currentText()

        if not self.sources:
            destination = None
        else:
            destination = self.dest_cbox.currentText()

        if destination == self.new_label:
            destination = None

        return [self.filename, img_format, destination]

# Returns a two value tuple with connpars as first parameter and variable
# name as second parameter
def getLoadImageFile(parent, filename, sources=None):

    dialog = LoadImageDialog(parent)
    dialog.set_filename(filename)
    dialog.set_sources(sources)

    try:
        exec_ = getattr(dialog,"exec_")
        is_accepted = QDialog.Accepted
    except AttributeError:
        exec_ = getattr(dialog,"exec")
        is_accepted = QDialog.DialogCode.Accepted

    result = exec_()

    if result == is_accepted:
        retval = dialog.get_values()
    else:
        retval = None

    dialog.destroy()
    return retval

if __name__ == '__main__':
    app = QApplication([])
    print(getLoadImageFile(None,"", ['one','two']))
