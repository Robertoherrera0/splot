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
import re

from pyspec.graphics.QVariant import (
    QWidget, Qt,
    QHBoxLayout, QVBoxLayout,
    QLabel, QComboBox, QFrame,
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.setLayout(layout)

        self.hkl_label = QLabel("HKL:")
        self.hkl_label.setFixedWidth(42)

        self.hkl_value = QLabel()
        self.hkl_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.hkl_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(self.hkl_label)
        layout.addWidget(self.hkl_value)

        font = self.hkl_label.font()
        font.setFamily("IBM Plex Sans")
        font.setPointSize(10)
        font.setBold(True)
        self.hkl_label.setFont(font)

        vfont = self.hkl_value.font()
        vfont.setFamily("IBM Plex Sans")
        vfont.setPointSize(10)
        self.hkl_value.setFont(vfont)

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

        QWidget.__init__(self, *args)

        # === Outer container (matches your panel style) ===
        self.outer_frame = QFrame()
        self.outer_frame.setObjectName("PlotHeaderFrame")
        self.outer_frame.setStyleSheet("""
            QFrame#PlotHeaderFrame {
                border: 1px solid #dcdfe3;
                border-radius: 6px;
                background: #ffffff;
            }
            QLabel {
                font-family: 'IBM Plex Sans';
                font-size: 10pt;
                color: #1e1e1e;
            }
            QComboBox {
                font-family: 'IBM Plex Sans';
                font-size: 10pt;
            }
        """)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(self.outer_frame)

        outer_layout = QVBoxLayout(self.outer_frame)
        outer_layout.setContentsMargins(8, 6, 8, 6)
        outer_layout.setSpacing(4)

        # --- Row 1: Scan row (Scan: <num> | <cmd>) ---
        self.row1 = QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setSpacing(8)

        self.scan_label = QLabel("Scan:")
        sfont = self.scan_label.font()
        sfont.setFamily("IBM Plex Sans")
        sfont.setPointSize(10)
        sfont.setBold(True)
        self.scan_label.setFont(sfont)

        self.scan_number = QLabel("")
        nfont = self.scan_number.font()
        nfont.setFamily("IBM Plex Sans")
        nfont.setPointSize(10)
        nfont.setBold(True)
        self.scan_number.setFont(nfont)
        self.scan_number.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.scan_sep = QLabel("|")
        self.scan_sep.setFont(nfont)

        self.scan_command = QLabel("")
        cfont = self.scan_command.font()
        cfont.setFamily("IBM Plex Sans")
        cfont.setPointSize(10)
        self.scan_command.setFont(cfont)
        self.scan_command.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.row1.addWidget(self.scan_label)
        self.row1.addWidget(self.scan_number)
        self.row1.addWidget(self.scan_sep)
        self.row1.addWidget(self.scan_command, 1, Qt.AlignLeft)

        # --- Separator line ---
        self.sep1 = QFrame()
        self.sep1.setFrameShape(QFrame.HLine)
        self.sep1.setFrameShadow(QFrame.Plain)
        self.sep1.setStyleSheet("color: #e6e8eb;")

        # --- Row 2: HKL row ---
        self.hkl_widget = HKLWidget()
        self.hkl_widget.hide()

        # --- Separator line ---
        self.sep2 = QFrame()
        self.sep2.setFrameShape(QFrame.HLine)
        self.sep2.setFrameShadow(QFrame.Plain)
        self.sep2.setStyleSheet("color: #e6e8eb;")

        # --- Row 3: Detector stats row ---
        self.statsLayout = QHBoxLayout()
        self.statsLayout.setContentsMargins(0, 0, 0, 0)
        self.statsLayout.setSpacing(10)
        self.statsLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.detector_label = QLabel("Detector:")
        dfont = self.detector_label.font()
        dfont.setFamily("IBM Plex Sans")
        dfont.setPointSize(10)
        dfont.setBold(True)
        self.detector_label.setFont(dfont)

        self.columnCombo = QComboBox()
        self.columnLabel = QLabel("")
        self.columnCombo.currentIndexChanged.connect(self._columnSelectionChanged)

        spacer = QLabel()
        spacer.setFixedWidth(6)

        self.peakLabel = QLabel("")
        self.comLabel = QLabel("")
        self.fwhmLabel = QLabel("")
        self.resultLabel = QLabel("")

        for lbl in [self.peakLabel, self.comLabel, self.fwhmLabel, self.resultLabel,
                    self.columnLabel]:
            f = lbl.font()
            f.setFamily("IBM Plex Sans")
            f.setPointSize(10)
            lbl.setFont(f)
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.columnLabel.setStyleSheet("QLabel { font-weight: bold; }")

        self.applyTheme()

        # Assemble rows
        outer_layout.addLayout(self.row1)
        outer_layout.addWidget(self.sep1)
        outer_layout.addWidget(self.hkl_widget)
        outer_layout.addWidget(self.sep2)
        self.statsLayout.addWidget(self.detector_label)
        self.statsLayout.addWidget(self.columnCombo)
        # self.statsLayout.addWidget(self.columnLabel)
        self.statsLayout.addWidget(spacer)
        self.statsLayout.addWidget(self.peakLabel)
        self.statsLayout.addWidget(self.comLabel)
        self.statsLayout.addWidget(self.fwhmLabel)
        self.statsLayout.addWidget(self.resultLabel, 1, Qt.AlignLeft)
        outer_layout.addLayout(self.statsLayout)

    def _parse_scan_title(self, title):
        m = re.match(r"\s*Scan\s+(\d+)\s*-\s*(.*)$", title)
        if m:
            return m.group(1), m.group(2)
        return None, title

    def setTitle(self, title):
        self.title = title

        num, rest = self._parse_scan_title(title)
        if num is None:
            self.scan_number.setText("")
            self.scan_sep.setText("")
            self.scan_command.setText(title)
        else:
            self.scan_number.setText(num)
            self.scan_sep.setText("|")
            self.scan_command.setText(rest.strip())

        hkl_value = self.dataBlock.getMetaData("HKL")
        if hkl_value:
            val = "   ".join(["%g" % val for val in map(float, hkl_value.split())])
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
                    "QLabel { font-weight: bold; color: %s; }" % self.theme.marker_color_peak
                )
                self.comLabel.setStyleSheet(
                    "QLabel { font-weight: bold; color: %s; }" % self.theme.marker_color_com
                )
                self.fwhmLabel.setStyleSheet(
                    "QLabel { font-weight: bold; color: %s; }" % self.theme.marker_color_fwhm
                )
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

    def setStatistics(self, stats):
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

    def _updateStats(self, newstats):
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
                txt += (
                    "<b><font color='%(maxcolor)s'>Max value: %(peak).4g</font> "
                    "at %(xcolumn)s=%(peak_x).3g / %(ycolumn)s=%(peak_y).3g</b>"
                ) % newstats
            except:
                import traceback
                log.log(2, traceback.format_exc())
                pass

            self.showResultLabel(txt)
            self.stats_text = self.selected_column + txt

        elif newstats['column'] == self.selected_column:
            self.hideResultLabel()

            peakpos = newstats['peak'][0]
            peakval = newstats['peak'][1]
            fwhmval = newstats['fwhm'][0]
            fwhmpos = newstats['fwhm'][1]
            compos = newstats['com']

            # columntxt = "%s: " % self.selected_column
            peaktxt = " Peak at %.5g is %.5g. " % (peakpos, peakval)
            comtxt = "COM at %.5g. " % compos
            fwhmtxt = "FWHM is %.5g at %.5g. " % (fwhmval, fwhmpos)

            self.columnLabel.setText(self.selected_column)
            self.peakLabel.setText(peaktxt)
            self.comLabel.setText(comtxt)
            self.fwhmLabel.setText(fwhmtxt)

            self.stats_text = self.selected_column + ": " + peaktxt + comtxt + fwhmtxt

    def showResultLabel(self, txt):
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
        nb_columns = len(self.columns)

        # Always hide label and combo
        self.columnLabel.hide()
        self.columnCombo.hide()

        # Optional: keep logic for multiple columns if you still want selection later
        if nb_columns > 1:
            self.columnCombo.show()
            self.columnCombo.clear()
            self.columnCombo.addItems(self.columns)

        if self.selected_column not in self.columns and nb_columns:
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


# Local test harness (optional)
def test():
    app = QApplication([])
    win = QMainWindow()
    titlestats = PlotHeader()
    titlestats.setTitle("Scan 100 - ascan th 3 4 3 2")
    win.setCentralWidget(titlestats)
    win.resize(700, 130)
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test()