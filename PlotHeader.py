#******************************************************************************
#
#  @(#)PlotHeader.py	3.8  01/15/22 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2020,2021,2022
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
import copy

from pyspec.graphics.QVariant import (QWidget, Qt,
                                      QHBoxLayout, QVBoxLayout,
                                      QLabel, QComboBox,
                                      QApplication, QMainWindow,
                                     )
from pyspec.css_logger import log
from Constants import *

from Preferences import Preferences
import themes

class HKLWidget(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0) 
        self.setLayout(layout)
        self.hkl_label = QLabel("HKL:")
        self.hkl_label.setFixedWidth(35) 
        self.hkl_value = QLabel()
        self.hkl_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.hkl_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.hkl_label)
        layout.addWidget(self.hkl_value)
        font = self.hkl_label.font()
        font.setPointSize(10)
        font.setBold(True)
        self.hkl_value.setFont(font)
        self.hkl_label.setFont(font)

    def set_value(self, value):
        self.hkl = value
        if value is not None:
            self.hkl_value.setText(value)
        else:
            self.hkl_value.setText("")

class PlotHeader(QWidget):

    def __init__(self, *args):

        # Init data
        self.dataBlock = None

        self.title = ""
        self.columns = None
        self.selected_column = None

        self.stats_text = ""
        self.hkl_text = ""

        self.prefs = Preferences()

        # Create the widget

        QWidget.__init__(self, *args)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        titleLayout = QHBoxLayout()
        titleLayout.setContentsMargins(0, 10, 0, 0)

        self.statsLayout = QHBoxLayout()
        self.statsLayout.setContentsMargins(0, 0, 0, 0)
        self.statsLayout.setSpacing(0)
        self.statsLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.hkl_widget = HKLWidget()
  
        layout.addLayout(titleLayout)
        layout.addWidget(self.hkl_widget)
        layout.addLayout(self.statsLayout)
        self.hkl_widget.hide() 

        self.setLayout(layout)

        # Add a title label
        self.titleLabel = QLabel()
        font = self.titleLabel.font()
        font.setBold(True)
        font.setPointSize(10)
        self.titleLabel.setFont(font)

        # Add a row for showing selected counters
        self.columnCombo = QComboBox()
        self.columnLabel = QLabel("")

        self.spacer1 = QLabel()
        self.spacer1.setFixedWidth(5)

        self.columnCombo.currentIndexChanged.connect(self._columnSelectionChanged)

        self.peakLabel = QLabel("")
        self.comLabel = QLabel("")
        self.fwhmLabel = QLabel("")
        self.resultLabel = QLabel("")

        self.peakLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.comLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.fwhmLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.resultLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.columnLabel.setFont(font)
        self.peakLabel.setFont(font)
        self.comLabel.setFont(font)
        self.fwhmLabel.setFont(font)

        self.columnLabel.setStyleSheet("QLabel {font-weight: bold;}")

        self.applyTheme()

        titleLayout.addWidget(self.titleLabel)

        self.statsLayout.addWidget(self.columnCombo)
        self.statsLayout.addWidget(self.columnLabel)
        self.statsLayout.addWidget(self.spacer1)
        self.statsLayout.addWidget(self.peakLabel)
        self.statsLayout.addWidget(self.comLabel)
        self.statsLayout.addWidget(self.fwhmLabel)
        self.statsLayout.addWidget(self.resultLabel)

    def setTitle(self, title):
        self.title = title
        self.titleLabel.setText(title)

        hkl_value = self.dataBlock.getMetaData("HKL")
        if hkl_value: 
            val = "   ".join(["%g"%val for val in map(float,hkl_value.split())])
            self.hkl_widget.set_value(val)
            self.hkl_widget.show()
            self.hkl_text = "HKL: " + val
        else:
            self.hkl_widget.hide()
            self.hkl_text = ""

        log.log(2, "NEW SCAN - HKL value for header is: %s\n" % str(hkl_value))


    def applyTheme(self):
        self.theme = themes.get_theme(self.prefs["theme"])
        if self.theme:
            try:
                self.peakLabel.setStyleSheet(
                    "QLabel {font-weight: bold; color: %s;}" % self.theme.marker_color_peak)
                self.comLabel.setStyleSheet(
                    "QLabel {font-weight: bold; color: %s;}" % self.theme.marker_color_com)
                self.fwhmLabel.setStyleSheet(
                    "QLabel {font-weight: bold; color: %s;}" % self.theme.marker_color_fwhm)
            except:
                pass

    def getTitle(self):
        ret_str = self.title
        if self.hkl_text != "":
            ret_str += "\n" + self.hkl_text
        if self.stats_text != "":
            ret_str += "\n" + self.stats_text
        return ret_str

    def getSelectedColumn(self):
        return self.selected_column

    def setStatistics(self,stats):
        self._updateStats(stats)

    def setDataBlock(self, datablock):

        if not datablock:  
            return

        if self.dataBlock and (self.dataBlock is not datablock):
            self.dataBlock.unsubscribe(self)

        self.dataBlock = datablock

        self.dataBlock.subscribe(self, STATS_UPDATED, self._updateStats)
        self.dataBlock.subscribe(self, Y_SELECTION_CHANGED, self._updateColumns)
        self.dataBlock.subscribe(self, TITLE_CHANGED, self.setTitle)

    def _updateColumns(self, columns):
        if columns == self.columns:
            return

        self.columns = copy.copy(columns)
        self._update()

    def _updateStats(self,newstats):

        if not newstats:
            self.showResultLabel("")
            return

        data_2d = newstats.get("2d", False)  

        if data_2d:
            self.theme = themes.get_theme(self.prefs["theme"])

            if self.theme is not None:
                try:
                    newstats['maxcolor'] = self.theme.marker_color_peak
                    newstats['poscolor'] = self.theme.marker_color_com
                    newstats['sumcolor'] = self.theme.marker_color_fwhm
                except:
                    pass

            txt = "<font color='%(sumcolor)s'><b>Sum = %(sum).2g. </b></font>" % newstats
            try:
                txt += "<b><font color='%(maxcolor)s'>Max value: %(peak).4g</font>" \
                    " at " \
                    "%(xcolumn)s=%(peak_x).3g / " \
                    "%(ycolumn)s=%(peak_y).3g" \
                    "</b>" % newstats
            except:
                import traceback
                log.log(2,traceback.format_exc())
                pass

            self.showResultLabel(txt)

            txt = "Sum = %(sum).2g. " \
                  " Max value: %(peak).4g" \
                  " at " \
                  "%(xcolumn)s=%(peak_x).3g / " \
                  "%(ycolumn)s=%(peak_y).3g"  % newstats

            self.stats_text = self.selected_column + txt
                   
        elif newstats['column'] == self.selected_column: 
            self.hideResultLabel()

            peakpos = newstats['peak'][0]
            peakval = newstats['peak'][1]
            fwhmval = newstats['fwhm'][0]
            fwhmpos = newstats['fwhm'][1]
            compos = newstats['com']

            columntxt = "%s: " % self.selected_column

            peaktxt = " Peak at %.5g is %.5g. " % (peakpos, peakval)
            comtxt = "COM at %.5g. " % compos
            fwhmtxt = "FWHM is %.5g at %.5g. " % (fwhmval, fwhmpos)

            self.columnLabel.setText(columntxt)
            self.peakLabel.setText(peaktxt)
            self.comLabel.setText(comtxt)
            self.fwhmLabel.setText(fwhmtxt)

            self.stats_text = self.selected_column + ": " + peaktxt + comtxt + fwhmtxt

    def showResultLabel(self,txt):
        self.peakLabel.hide()
        self.comLabel.hide()
        self.fwhmLabel.hide()
        self.resultLabel.show()
        self.resultLabel.setText(txt)

    def hideResultLabel(self):
        self.peakLabel.show()
        self.comLabel.show()
        self.fwhmLabel.show()
        self.resultLabel.hide()

    def _update(self):
        # Show them
        nb_columns = len(self.columns)

        if nb_columns == 0:
            self.columnLabel.hide()
            self.columnCombo.hide()
        elif nb_columns == 1:
            self.columnCombo.clear()
            self.columnCombo.hide()
            self.columnLabel.show()
            self.columnLabel.setText(self.columns[0])
        else:
            self.columnLabel.hide()
            self.columnCombo.show()
            self.columnCombo.clear()
            self.columnCombo.addItems(self.columns)

        # Select a default column if the one selected is gone
        if self.selected_column not in self.columns:
            if nb_columns:
                self._selectColumn(self.columns[0])

    def selectColumn(self, column):

        if self.columns is None:
            return

        self._selectColumn(column)

        if self.selected_column not in self.columns:
            return

        active_idx = self.columns.index(self.selected_column)
        self.columnCombo.setCurrentIndex(active_idx)

    def _selectColumn(self, column):
        self.selected_column = column
        if self.selected_column in self.columns:
            self.dataBlock.setActiveColumn(column)

    def _columnSelectionChanged(self, idx):
        self.selectColumn(self.columns[idx])
        
def test():
    app = QApplication([])
    win = QMainWindow()

    titlestats = PlotHeader()
    titlestats.setTitle("Scan 2 - ascan th 3 20 20 0.1")

    win.setCentralWidget(titlestats)
    win.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    test()
