#******************************************************************************
#
#  @(#)ScanMetadataWidget.py	3.5  10/01/20 CSS
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
#*******#******************************************************************************
#
#  @(#)ScanMetadataWidget.py  3.5  10/01/20 CSS
#
#  "splot" Release 3
#
#******************************************************************************

import os
import sys
import time

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import QTimer

from pyspec.graphics.QVariant import *   # brings in Qt widgets/symbols in this tree
from pyspec.css_logger import log
import icons


class ScanMetadataWidget(QWidget):
    """Scan metadata panel with tabs:
       Motors | Current Scan (blank placeholder) | Comments | Messages | More...
       NO LiveScanTable, NO polling — just the original metadata UI restored.
    """

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.sources = []
        self.activeSource = None

        self.showingComments = True
        self.showingMessages = True
        self.showingHKL = True
        self.showingMore = True

        self._conn = None
        self._scan_timer = None


        self.scanno = -1
        self.has_motmnes = False

        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(4)
        self.setLayout(layout)

        # --- Header container ---
        headerFrame = QWidget()
        headerLayout = QGridLayout(headerFrame)
        headerLayout.setContentsMargins(0, 0, 0, 4)
        headerLayout.setHorizontalSpacing(20)
        headerLayout.setVerticalSpacing(2)

        # --- Label + Value style (subtle, like File Info) ---
        labelStyle = """
            font-family: 'IBM Plex Sans','Segoe UI',sans-serif;
            font-size: 9pt;
            color: #555555;
        """
        valueStyle = """
            font-family: 'IBM Plex Sans','Segoe UI',sans-serif;
            font-size: 9pt;
            color: #222222;
        """

        def makeLabel(text, isValue=False):
            w = QLabel(text)
            w.setStyleSheet(valueStyle if isValue else labelStyle)
            if isValue:
                w.setTextInteractionFlags(Qt.TextSelectableByMouse)
            return w

        # --- Labels + Values ---
        self.scanNoLabel   = makeLabel("Scan Number:")
        self.scanNoValue   = makeLabel("", isValue=True)
        self.pointsLabel   = makeLabel("Total Points:")
        self.pointsValue   = makeLabel("", isValue=True)

        self.hklLabel      = makeLabel("HKL:")
        self.hklValue      = makeLabel("", isValue=True)
        self.columnsLabel  = makeLabel("Columns:")
        self.columnsValue  = makeLabel("", isValue=True)

        self.dateLabel     = makeLabel("Date:")
        self.dateValue     = makeLabel("", isValue=True)

        # --- Layout placement ---
        headerLayout.addWidget(self.scanNoLabel, 0, 0)
        headerLayout.addWidget(self.scanNoValue, 0, 1)
        headerLayout.addWidget(self.pointsLabel, 0, 2)
        headerLayout.addWidget(self.pointsValue, 0, 3)

        headerLayout.addWidget(self.hklLabel, 1, 0)
        headerLayout.addWidget(self.hklValue, 1, 1)
        headerLayout.addWidget(self.columnsLabel, 1, 2)
        headerLayout.addWidget(self.columnsValue, 1, 3)

        headerLayout.addWidget(self.dateLabel, 2, 0)
        headerLayout.addWidget(self.dateValue, 2, 1, 1, 3)

        layout.addWidget(headerFrame, 0, 0, 1, 5)


        # --- Tabs ---
        self.infoTabs = QTabWidget()
        self.infoTabs.setObjectName("infotabs")

        # Motors (drop-in replacement)
        self.motorArea = QScrollArea()
        self.motorArea.setWidgetResizable(True)
        self.motorArea.setFrameShape(QFrame.NoFrame)
        self.motorArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.motorArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.motorArea.setAlignment(Qt.AlignLeft)  # don't center/crop

        self.motorTreeWidget = QTreeWidget()
        self.motorTreeWidget.setObjectName("MotorTree")
        self.motorTreeWidget.setAlternatingRowColors(False)
        self.motorTreeWidget.setRootIsDecorated(False)
        self.motorTreeWidget.setIndentation(0)
        self.motorTreeWidget.setUniformRowHeights(True)
        self.motorTreeWidget.setFocusPolicy(Qt.NoFocus)
        self.motorTreeWidget.setSelectionMode(QTreeWidget.NoSelection)

        # IMPORTANT: let it expand (no fixed/min/max width here)
        self.motorTreeWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Match MotorTable look
        self.motorTreeWidget.setStyleSheet("""
        QTreeWidget#MotorTree {
            border: 1px solid #dcdfe3;
            border-radius: 6px;
            font-family: 'IBM Plex Sans','Segoe UI',sans-serif;
            font-size: 8pt;
        }
        QHeaderView::section {
            background-color: #f4f5f7;
            font-weight: 500;
            padding: 2px 6px;
            font-size: 8pt;
            color: #2b2b2b;
            border: none;
        }
        QTreeWidget#MotorTree::item {
            height: 22px;
            border-bottom: 1px solid #e1e4e8;  /* subtle row line */
        }
        """)

        self.motorArea.setWidget(self.motorTreeWidget)


        # Current Scan (blank placeholder)
        # Current Scan (table)  — the only widget inside the scroll area
        self.currentScanArea = QScrollArea()
        self.currentScanArea.setWidgetResizable(True)
        self.currentScanArea.setAlignment(Qt.AlignHCenter)

        self.scanTable = QTableWidget()
        self.scanTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.scanTable.setSelectionMode(QTableWidget.NoSelection)
        self.scanTable.setAlternatingRowColors(True)
        self.scanTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.scanTable.verticalHeader().setVisible(True)

        # put the table into the scroll area exactly once
        self.currentScanArea.setWidget(self.scanTable)

        # Comments
        self.commentsArea = QTextBrowser()

        # Messages
        self.messageArea = QScrollArea()
        self.messageArea.setWidgetResizable(True)
        self.messageArea.setAlignment(Qt.AlignHCenter)

        self.messageTreeWidget = QTreeWidget()
        self.messageTreeWidget.setObjectName("errortree")
        self.messageTreeWidget.setAlternatingRowColors(True)
        self.messageArea.setWidget(self.messageTreeWidget)

        # More...
        self.moreArea = QScrollArea()
        self.moreArea.setWidgetResizable(True)
        self.moreArea.setAlignment(Qt.AlignHCenter)

        self.moreTreeWidget = QTreeWidget()
        self.moreTreeWidget.setObjectName("moretree")
        self.moreTreeWidget.setAlternatingRowColors(True)
        self.moreArea.setWidget(self.moreTreeWidget)

        # Add tabs in the exact order you wanted
        self.infoTabs.addTab(self.motorArea, "Starting Positions")
        self.infoTabs.addTab(self.currentScanArea, "Scan Data")
        self.infoTabs.addTab(self.commentsArea, "Comments")
        self.infoTabs.addTab(self.messageArea, "Messages")
        self.infoTabs.addTab(self.moreArea, "More...")

        # Spacer
        self.spacer = QLabel("")
        self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # --- Layout grid (3 rows header + tabs) ---
        layout.addWidget(self.scanNoLabel,  0, 0)
        layout.addWidget(self.scanNoValue,  0, 1)
        layout.addWidget(self.pointsLabel,  0, 2)
        layout.addWidget(self.pointsValue,  0, 3)

        layout.addWidget(self.hklLabel,     1, 0)
        layout.addWidget(self.hklValue,     1, 1)
        layout.addWidget(self.columnsLabel, 1, 2)
        layout.addWidget(self.columnsValue, 1, 3)

        layout.addWidget(self.dateLabel,    2, 0)
        layout.addWidget(self.dateValue,    2, 1, 1, 3)

        layout.addWidget(self.spacer,       0, 4, 3, 1)
        layout.addWidget(self.infoTabs, 5, 0, 1, 5)
        self.infoTabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # let the tabs area take the horizontal/vertical space
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)  # give content room
        layout.setColumnStretch(2, 0)
        layout.setColumnStretch(3, 0)
        layout.setRowStretch(5, 1)     # the tab row expands


        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # initial hiding logic
        self.setHKL(None)
        self.setComments(None)
        self.setMessages(None)
        self.setMore(None)

    def set_connection(self, conn):
        self._conn = conn
        if self._scan_timer is None:
            self._scan_timer = QTimer(self)
            self._scan_timer.timeout.connect(self._update_scan_table_from_conn)
            self._scan_timer.start(500)
        # initial populate
        self._update_scan_table_from_conn()

    def setScanData(self, columns, data):
        """Populate/refresh the Current Scan table using arrays."""
        if not columns or not data:
            self.scanTable.clear()
            self.scanTable.setRowCount(0)
            self.scanTable.setColumnCount(0)
            return

        rows, cols = len(data), len(columns)
        self.scanTable.setColumnCount(cols)
        self.scanTable.setHorizontalHeaderLabels([str(c) for c in columns])

        # Fast path: grow/shrink rows only when needed
        self.scanTable.setRowCount(rows)
        for r in range(rows):
            row = data[r]
            for c in range(cols):
                try:
                    val = row[c]
                except Exception:
                    val = ""
                if isinstance(val, float):
                    text = f"{val:.6g}"
                elif isinstance(val, int):
                    text = str(val)
                else:
                    text = "" if val is None else str(val)
                it = QTableWidgetItem(text)
                it.setTextAlignment(Qt.AlignCenter)
                self.scanTable.setItem(r, c, it)

        self.scanTable.resizeColumnsToContents()

    def _update_scan_table_from_conn(self):
        if self._conn is None:
            return
        try:
            columns = getattr(self._conn, "scan_columns", None)
            data    = getattr(self._conn, "scan_data", None)

            # handle numpy arrays or lists safely
            has_cols = columns is not None and len(columns) > 0
            has_data = data is not None and len(data) > 0

            if has_cols and has_data:
                self.setScanData(columns, data)
        except Exception as e:
            log.log(2, f"_update_scan_table_from_conn failed: {e}")

    # ---- metadata setters (unchanged behavior) ----
    def setMetadata(self, data):
        if "scanno" in data:
            no = str(data["scanno"])
            if "order" in data:
                order = data["order"]
                if order > 1:
                    no += ".%s" % order
            no = "<b>" + no + "</b>"
            if "noinfile" in data:
                no += " (%s)" % data["noinfile"]
            self.scanno = no
            self.scanNoValue.setText(no)

        if "date" in data:
            try:
                itime = float(data["date"])
                dat = time.asctime(time.localtime(itime))
                self.dateValue.setText(dat)
            except ValueError:
                self.dateValue.setText(data["date"])

        if "HKL" in data and data['HKL']:
            self.setHKL(data['HKL'])
        else:
            self.setHKL(None)

        if "points" in data:
            self.setPoints(data["points"])
        else:
            self.setPoints("")

        if "columns" in data:
            self.setColumns(data["columns"])
        else:
            self.setColumns("")

        if "motormnes" in data:
            self.setMotorMnemonics(data["motormnes"])
        else:
            self.setMotorMnemonics(None)

        if "motors" in data:
            self.setMotors(data["motors"])

        if "comments" in data and data["comments"]:
            self.setComments(data["comments"])
        else:
            self.setComments(None)

        if "errors" in data and data["errors"]:
            self.setMessages(data["errors"])
        else:
            self.setMessages(None)

        more = []
        if "userlines" in data and data["userlines"]:
            more.append(["user", data["userlines"]])
        if "extra" in data and data["extra"]:
            more.append(["extra", data["extra"]])
        if "geo" in data and data["geo"]:
            more.append(["geo", data["geo"]])

        if more:
            self.setMore(more)
        else:
            self.setMore(None)

    def setHKL(self, value):
        showit = value is not None
        if showit:
            self.hklValue.setText(value)
        if showit and not self.showingHKL:
            self.hklLabel.show()
            self.hklValue.show()
        elif not showit and self.showingHKL:
            self.hklLabel.hide()
            self.hklValue.hide()
        self.showingHKL = showit

    def setPoints(self, value):
        self.pointsValue.setText("" if value is None else str(value))

    def setColumns(self, value):
        self.columnsValue.setText("" if value is None else str(value))

    def setMotorMnemonics(self, mnes):
        if not mnes:
            self.has_motmnes = False
        else:
            self.motmnes = mnes
            self.has_motmnes = True

    def setMotors(self, motors):
        self.motorTreeWidget.clear()
        if not motors:
            return

        if self.has_motmnes:
            self.motorTreeWidget.setColumnCount(3)
            self.motorTreeWidget.setHeaderLabels(["Motor", "Mnemonic", "Pos"])
        else:
            self.motorTreeWidget.setColumnCount(2)
            self.motorTreeWidget.setHeaderLabels(["Motor", "Pos"])

        header = self.motorTreeWidget.header()
        # Stretch name like MotorTable; keep mnemonic/pos snug
        if self.has_motmnes:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.Stretch)          # Motor (full name)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Mnemonic
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Pos
        else:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.Stretch)          # Motor
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Pos

        for idx, entry in enumerate(motors):
            if self.has_motmnes:
                name, pos = entry
                mne = self.motmnes[idx] if idx < len(self.motmnes) else ""
                try:
                    pos_txt = f"{float(pos):.3f}"
                except Exception:
                    pos_txt = "—"

                item = QTreeWidgetItem([name, mne, pos_txt])
                item.setTextAlignment(0, Qt.AlignLeft  | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignCenter)
            else:
                name, pos = entry
                try:
                    pos_txt = f"{float(pos):.3f}"
                except Exception:
                    pos_txt = "—"

                item = QTreeWidgetItem([name, pos_txt])
                item.setTextAlignment(0, Qt.AlignLeft  | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)

            self.motorTreeWidget.addTopLevelItem(item)

    def setComments(self, comments):
        showit = comments is not None
        if showit:
            txtstr = "".join("<b>-</b>" + c + "<br>" for c in comments)
            self.commentsArea.setText(txtstr)

        # keep tab visibility in sync
        if showit and not self.showingComments:
            self.infoTabs.insertTab(2, self.commentsArea, "Comments")
        elif not showit and self.showingComments:
            idx = self.infoTabs.indexOf(self.commentsArea)
            if idx != -1:
                self.infoTabs.removeTab(idx)
        self.showingComments = showit

    def setMessages(self, messages):
        showit = messages is not None
        if showit:
            self.messageTreeWidget.clear()
            self.messageTreeWidget.setColumnCount(3)  # fixed: 3 headers -> 3 columns
            self.messageTreeWidget.setHeaderLabels(["ID", "Loc", "Message"])
            self.messageTreeWidget.setRootIsDecorated(False)

            for msg in messages:
                try:
                    _id, _loc, _msg = msg
                    item = QTreeWidgetItem([str(_id), str(_loc), str(_msg)])
                    item.setToolTip(2, str(_msg))
                    self.messageTreeWidget.addTopLevelItem(item)
                except ValueError:
                    log.log(2, "Error message is wrongly formatted (should be [id,locator,msg]. %s " % str(msg))

            self.messageTreeWidget.resizeColumnToContents(0)
            self.messageTreeWidget.resizeColumnToContents(1)

        # toggle Messages tab if needed
        if showit != self.showingMessages:
            if showit:
                self.infoTabs.addTab(self.messageArea, icons.get_icon('attention'), "Messages")
                idx = self.infoTabs.indexOf(self.messageArea)
                self.infoTabs.setCurrentIndex(idx)
            else:
                idx = self.infoTabs.indexOf(self.messageArea)
                if idx != -1:
                    self.infoTabs.removeTab(idx)
        self.showingMessages = showit

    def setMore(self, messages):
        showit = messages is not None
        if showit:
            self.moreTreeWidget.clear()
            self.moreTreeWidget.setColumnCount(1)
            self.moreTreeWidget.header().close()
            for title, msgs in messages:
                item = QTreeWidgetItem([title])
                self.moreTreeWidget.addTopLevelItem(item)
                for msg in msgs:
                    subitem = QTreeWidgetItem([str(msg)])
                    subitem.setToolTip(0, str(msg))
                    item.addChild(subitem)

        if showit != self.showingMore:
            if showit:
                self.infoTabs.addTab(self.moreArea, "More...")
            else:
                idx = self.infoTabs.indexOf(self.moreArea)
                if idx != -1:
                    self.infoTabs.removeTab(idx)
        self.showingMore = showit

    # Only used if someone plugs something else in later; safe no-op otherwise
    def setHeaderContent(self, data):
        # headerArea is not part of this widget; left for compatibility
        pass


if __name__ == '__main__':
    from pyspec.file.spec import FileSpec

    filename = sys.argv[1]
    scanno = int(sys.argv[2])

    sf = FileSpec(filename)
    scan = sf[scanno]

    app = QApplication([])
    win = QMainWindow()
    wid = ScanMetadataWidget(win)

    wid.setMetadata(scan.getMeta())
    win.setWindowTitle('Scan Meta Data')
    win.setCentralWidget(wid)
    win.setGeometry(200, 100, 600, 500)
    win.show()

    sys.exit(app.exec_())
