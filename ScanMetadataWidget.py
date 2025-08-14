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
#******************************************************************************

import sys
import time

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log

import icons

class ScanMetadataWidget(QWidget):

    def __init__(self, parent=None):

        QWidget.__init__(self, parent)

        self.sources = []
        self.activeSource = None

        self.showingComments = True
        self.showingMessages = True
        self.showingHKL = True
        self.showingMore = True

        self.scanno = -1

        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setHorizontalSpacing(20)
        self.setLayout(layout)

        self.scanNoLabel = QLabel("Scan Number:")
        self.dateLabel = QLabel("Date:")
        self.hklLabel = QLabel("HKL:")
        self.pointsLabel = QLabel("Total Points:")
        self.columnsLabel = QLabel("Columns:")

        self.scanNoValue = QLabel("")
        self.dateValue = QLabel("")
        self.hklValue = QLabel("")
        self.pointsValue = QLabel("")
        self.columnsValue = QLabel("")

        self.scanNoValue.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.dateValue.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.hklValue.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.pointsValue.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.columnsValue.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.spacer = QLabel("")
        self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.infoTabs = QTabWidget()
        self.infoTabs.setObjectName("infotabs")

        self.motorArea = QScrollArea()

        self.motorTreeWidget = QTreeWidget()
        self.motorTreeWidget.setObjectName("motortree")
        self.motorTreeWidget.setAlternatingRowColors(True)

        self.motorArea.setWidget(self.motorTreeWidget)
        self.motorArea.setWidgetResizable(True)
        self.motorArea.setAlignment(Qt.AlignHCenter)

        self.commentsArea = QTextBrowser()

        self.messageArea = QScrollArea()

        self.messageTreeWidget = QTreeWidget()
        self.messageTreeWidget.setObjectName("errortree")
        self.messageTreeWidget.setAlternatingRowColors(True)

        self.messageArea.setWidget(self.messageTreeWidget)
        self.messageArea.setWidgetResizable(True)
        self.messageArea.setAlignment(Qt.AlignHCenter)

        self.moreArea = QScrollArea()

        self.moreTreeWidget = QTreeWidget()
        self.moreTreeWidget.setObjectName("moretree")
        self.moreTreeWidget.setAlternatingRowColors(True)

        self.moreArea.setWidget(self.moreTreeWidget)
        self.moreArea.setWidgetResizable(True)
        self.moreArea.setAlignment(Qt.AlignHCenter)

        self.infoTabs.addTab(self.motorArea, "Motors")
        self.infoTabs.addTab(self.commentsArea, "Comments")
        self.infoTabs.addTab(self.messageArea, "Messages")
        self.infoTabs.addTab(self.moreArea, "More...")

        # --- Metadata layout (clean 2+1 rows) ---
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(4)

        label_style = """
            font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
            font-size: 12px;
            color: #444;
        """
        value_style = """
            font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: #111;
        """
        # Make labels right-aligned, values left-aligned
        for w in (self.scanNoLabel, self.pointsLabel, self.hklLabel, self.columnsLabel, self.dateLabel):
            w.setAlignment(Qt.AlignLeft | Qt.AlignLeft)
            w.setStyleSheet(label_style)

        for w in (self.scanNoValue, self.pointsValue, self.hklValue, self.columnsValue, self.dateValue):
            w.setAlignment(Qt.AlignLeft | Qt.AlignLeft)
            w.setStyleSheet(value_style)

        # Row 0
        layout.addWidget(self.scanNoLabel, 0, 0)
        layout.addWidget(self.scanNoValue, 0, 1)
        layout.addWidget(self.pointsLabel, 0, 2)
        layout.addWidget(self.pointsValue, 0, 3)

        # Row 1
        layout.addWidget(self.hklLabel, 1, 0)
        layout.addWidget(self.hklValue, 1, 1)
        layout.addWidget(self.columnsLabel, 1, 2)
        layout.addWidget(self.columnsValue, 1, 3)

        # Row 2
        layout.addWidget(self.dateLabel, 2, 0)
        layout.addWidget(self.dateValue, 2, 1, 1, 3)


        layout.addWidget(self.spacer, 0, 4, 3, 1)

        layout.addWidget(self.infoTabs, 5, 0, 1, 3)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setHKL(None)
        self.setComments(None)
        self.setMessages(None)
        self.setMore(None)

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
        if value is not None:
            self.hklValue.setText(value)
            showit = True
        else:
            showit = False

        if showit and not self.showingHKL:
            self.hklLabel.show()
            self.hklValue.show()
        elif not showit and self.showingHKL:
            self.hklLabel.hide()
            self.hklValue.hide()

        self.showingHKL = showit

    def setPoints(self, value):
        if value is not None:
            self.pointsValue.setText(str(value))
        else:
            self.pointsValue.setText("")

    def setColumns(self, value):
        if value is not None:
            self.columnsValue.setText(str(value))
        else:
            self.columnsValue.setText("")

    def setMotorMnemonics(self, mnes):
        if not mnes:
            self.has_motmnes = False
            return
        else:
            self.motmnes = mnes
            self.has_motmnes = True

    def setMotors(self, motors):

        self.motorTreeWidget.clear()

        if not motors:
            return

        if self.has_motmnes:
            if len(motors) != len(self.motmnes):
                return
            self.motorTreeWidget.setColumnCount(3)
            self.motorTreeWidget.setHeaderLabels(["Mne", "Name", "Position"])
            self.motorTreeWidget.setRootIsDecorated(False)
        else:
            self.motorTreeWidget.setColumnCount(2)
            self.motorTreeWidget.setHeaderLabels(["Name", "Position"])
            self.motorTreeWidget.setRootIsDecorated(False)

        for mnum in range(len(motors)):
            name, motorpos = motors[mnum]
            if self.has_motmnes:
                mne = self.motmnes[mnum]
                item = QTreeWidgetItem([mne, name, motorpos])
            else:
                item = QTreeWidgetItem([name, motorpos])
            self.motorTreeWidget.addTopLevelItem(item)

        self.motorTreeWidget.resizeColumnToContents(0)
        if self.has_motmnes:
            self.motorTreeWidget.resizeColumnToContents(1)

    def setComments(self, comments):
        if comments is not None:
            txtstr = ""
            for comment in comments:
                txtstr += "<b>-</b>" + comment + "<br>"
            self.commentsArea.setText(txtstr)
            showit = True
        else:
            showit = False

        if showit and not self.showingComments:
            self.infoTabs.insertTab(1, self.commentsArea, "Comments")
        elif not showit and self.showingComments:
            self.infoTabs.removeTab(1)

        self.showingComments = showit

    def setMessages(self, messages):

        if messages is not None:

            self.messageTreeWidget.clear()
            self.messageTreeWidget.setColumnCount(1)
            self.messageTreeWidget.setHeaderLabels(["ID", "Loc", "Message"])
            self.messageTreeWidget.setRootIsDecorated(False)

            for msg in messages:
                try:
                    _id, _loc, _msg = msg
                    item = QTreeWidgetItem(list(map(str,msg)))
                    item.setToolTip(2, _msg)
                    self.messageTreeWidget.addTopLevelItem(item)
                except ValueError:
                    log.log(2,
                        "Error message is wrongly formatted (should be [id,locator,msg]. %s " % str(msg))
            self.messageTreeWidget.resizeColumnToContents(0)
            self.messageTreeWidget.resizeColumnToContents(1)
            showit = True
        else:
            showit = False

        if showit != self.showingMessages:
            if showit:
                icondir = os.path.join(os.path.dirname(__file__), 'icons')
                self.infoTabs.addTab(self.messageArea, icons.get_icon('attention'), "Messages")
                idx = self.infoTabs.indexOf(self.messageArea)
                self.infoTabs.setCurrentIndex(idx)
            else:
                idx = self.infoTabs.indexOf(self.messageArea)
                self.infoTabs.removeTab(idx)

        self.showingMessages = showit

    def setMore(self, messages):

        if messages is not None:
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
            showit = True
        else:
            showit = False

        if showit != self.showingMore:
            if showit:
                self.infoTabs.addTab(self.moreArea, "More...")
                idx = self.infoTabs.indexOf(self.moreArea)
            else:
                idx = self.infoTabs.indexOf(self.moreArea)
                self.infoTabs.removeTab(idx)

        self.showingMore = showit

    def setHeaderContent(self, data):

        self.headerArea.setText("hi there")

if __name__ == '__main__':

    from pyspec.file.spec import FileSpec
    import sys

    filename = sys.argv[1]
    scanno = int(sys.argv[2])

    sf = FileSpec(filename)
    scan = sf[scanno]

    app = QApplication([])
    win = QMainWindow()
    wid = ScanMetadataWidget(win)

    print(scan.getMeta())

    wid.setMetadata(scan.getMeta())
    win.setWindowTitle('Scan Meta Data')

    win.setCentralWidget(wid)
    win.setGeometry(200, 100, 400, 400)
    win.show()

    sys.exit(app.exec_())
