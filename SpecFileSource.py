#******************************************************************************
#
#  @(#)SpecFileSource.py	3.15  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2020,2021,2023,2024
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
import sys
import time

from pyspec.file.spec import FileSpec
from pyspec.graphics.QVariant import *
from pyspec.graphics import qt_variant
from pyspec.css_logger import log

from icons import get_icon

from Constants import *
from Scan import Scan
from DataSource1D import DataSource1D

class SpecFileSource(DataSource1D):

    def __init__(self, app, filename=None, fd=None):

        if filename is not None:
            self.filename = filename
        else:
            self.filename = fd.getFileName()

        super(SpecFileSource, self).__init__(
            app, SOURCE_FILE, os.path.basename(self.filename))

        self.nb_scans = 0

        self.spec_connection = None
        self.spec_name = None

        self.setFile(filename,fd)
        self.realpath = os.path.realpath(self.filename)

    def getName(self):
        return os.path.basename(self.filename)

    def getTypeString(self):
        return "file"

    def getDescription(self):
        scannum = self.currentScan.getNumber()
        return "%s_s%s" % (self.getSourceName(), scannum)

    def init(self):
        DataSource1D.init(self)
        self.scanselected = None
        self.currentScan = None

    def init_widget(self):

        self.fileIDCard = QWidget()

        self.idBox = QGridLayout()
        self.fileIDCard.setLayout(self.idBox)

        self.fileLabel = QLabel("Current Filename:")
        self.fileNameLabel = QLabel()
        self.fileNameLabel.setObjectName("filename")
        self.spacer = QLabel()
        self.fileLabel.setStyleSheet("""
            color: #555555;
            font-size: 9pt;
            font-weight: 500;
        """)

        self.fileNameLabel.setStyleSheet("""
            color: #222222;
            font-size: 10pt;
            font-weight: 600;
        """)


        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setContentsMargins(0,0,0,0)
        self.buttonLayout.setSpacing(0)

        self.prevButton = QPushButton()
        self.prevButton.setFlat(True)
        self.prevButton.setIcon(get_icon('prev'))
        self.prevButton.setToolTip("Prev scan")
        self.prevButton.clicked.connect(self.prev)
        self.prevButton.setFixedWidth(38)

        self.nextButton = QPushButton()
        self.nextButton.setFlat(True)
        self.nextButton.setIcon(get_icon('next'))
        self.nextButton.setToolTip("Next scan")
        self.nextButton.clicked.connect(self.next)
        self.nextButton.setFixedWidth(38)

        self.buttonLayout.addWidget(self.prevButton)
        self.buttonLayout.addWidget(self.nextButton)

        self.infoBox = QTreeWidget()
        self.infoBox.setObjectName("fileinfo")
        self.infoBox.setAlternatingRowColors(True)
        self.infoBox.setStyleSheet("""
            QTreeWidget#fileinfo {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background: #ffffff;
                alternate-background-color: #fafafa;
                font-size: 10pt;
            }
            QTreeWidget#fileinfo::item {
                padding: 4px 6px;
            }
            QTreeWidget#fileinfo::item:selected {
                background-color: #dbeafe;   /* soft blue */
                color: #0f172a;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 2px 4px;
                border: 0px;
                border-bottom: 1px solid #d0d0d0;
                font-size: 9pt;        /* smaller header text */
                font-weight: 400;      /* lighter */
                color: #444444;        /* softer gray */
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.idBox.addWidget(self.fileLabel, 0, 0)
        self.idBox.addWidget(self.fileNameLabel, 0, 1)
        self.idBox.addWidget(self.spacer, 0, 2)
        self.idBox.addLayout(self.buttonLayout, 0, 3)

        self.scantree = QTreeWidget()
        self.scantree.setColumnCount(2)
        self.scantree.setAlternatingRowColors(True)
        self.scantree.setObjectName("scantree")
        try:
            self.scantree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        except AttributeError:
            self.scantree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.scantree.setStyleSheet("""
            QTreeWidget#scantree {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background: #ffffff;
                alternate-background-color: #fafafa;
                font-size: 10pt;
            }
            QTreeWidget#scantree::item {
                padding: 4px 6px;
            }
            QTreeWidget#scantree::item:selected {
                background-color: #dbeafe;   /* soft blue */
                color: #0f172a;              /* dark text */
                border-radius: 4px;
            }
            QTreeWidget#scantree::item:selected:active {
                background-color: #bfdbfe;   /* darker blue when active */
            }
            QTreeWidget#scantree::item:selected:!active {
                background-color: #e0e7ff;   /* lighter when not focused */
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 2px 4px;
                border: 0px;
                border-bottom: 1px solid #d0d0d0;
                font-weight: 400;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.scantree.setHeaderLabels(["#", "Scan command"])
        self.scantree.setRootIsDecorated(False)
        self.scantree.setColumnWidth(2, 20)
        self.scantree.resizeColumnToContents(0)
        if qt_variant() in ["PyQt4", "PySide"]:
            self.scantree.header().setResizeMode(0, QHeaderView.Fixed)
        elif qt_variant() in ["PyQt5", "PySide2"]:
            self.scantree.header().setSectionResizeMode(0, QHeaderView.Fixed)
        else:
            self.scantree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)

        self.scantree.setColumnWidth(1, 100)

        # Insert in standard DataSource widget
        self.set_source_header_widget(self.fileIDCard)
        self.add_source_tab(0, self.infoBox, "File Info")
        self.add_source_tab(1, self.scantree, "Scans")

        self.scantree.itemClicked.connect(self.treeClicked)
        self.scantree.itemSelectionChanged.connect(self.selectionChanged)

        self.tabs.setCurrentIndex(1)

    def init_source_area(self):
        self.show_column_selection_widget()
        self.show_metadata_widget()

    def setFile(self, filename=None, fd=None):

        if fd is not None:
            self.sf = fd
        else:
            if filename == "/dev/null":
                return False

            try:
                self.sf = FileSpec(filename)
            except BaseException as e:
                log.log(2, "----- error opening file %s" % str(e))
                raise e

        filename = self.sf.getFileName()

        self.name = str(filename)
        self.fileNameLabel.setText(os.path.basename(str(filename)))

        self.treeItems = []
        self._updateFile()

        self._updateFileInfo()

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateFile)
        self.timer.start(UPDATEFILE_INTERVAL)

    def set_spec_connection(self, conn):
        self.spec_connection = conn

    def connect_to_spec(self):
        log.log(2, "connecting file (spec=%s) to spec (name=%s)" % \
                self.spec_connection.getSpecName(), self.specname)

        if None in [self.specname, 
                    self.spec_connection,
                    self.spec_connection.getSpecName()]:
            return

        if  self.spec_connection.getSpecName() != self.specname:
            return

        log.log(2, "File %s is connected to spec" % self.name)

    def _updateFileInfo(self):

        self.infoBox.clear()
        self.infoBox.setHeaderHidden(True)
        self.infoBox.setColumnCount(2)
        self.infoBox.setRootIsDecorated(False)

        created, modified, user, spec = self.sf.getInfo()
        nb_scans = self.sf.getNumberScans()
        nb_headers = self.sf.getNumberHeaders()
        fullpath = self.sf.absolutePath()

        if user:
            item = QTreeWidgetItem(["User", user])
            self.infoBox.addTopLevelItem(item)

        if spec:
            self.spec_name = spec
            item = QTreeWidgetItem(["Spec", spec])
            self.infoBox.addTopLevelItem(item)

        if created:
            item = QTreeWidgetItem(["Created", created])
            item.setToolTip(1, created)
            self.infoBox.addTopLevelItem(item)

        if modified:
            item = QTreeWidgetItem(["Modified", modified])
            item.setToolTip(1, modified)
            self.infoBox.addTopLevelItem(item)

        item = QTreeWidgetItem(["Scans", str(nb_scans)])
        self.infoBox.addTopLevelItem(item)

        item = QTreeWidgetItem(["Header blocks", str(nb_headers)])
        self.infoBox.addTopLevelItem(item)

        item = QTreeWidgetItem(["Full path", fullpath])
        item.setToolTip(1, fullpath)
        self.infoBox.addTopLevelItem(item)

        self.infoBox.resizeColumnToContents(0)

    def peyPressEvent(self, e):
        if e.key() == Qt.Key_Up:
            self.prev()
        elif e.key() == Qt.Key_Down:
            self.next()
        elif e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.next()

        QWidget.keyPressEvent(self, e)

    def close(self):
        super(SpecFileSource, self).close()
        self.timer.stop()

    def addScansToTree(self, first=0):
        sn = first
        for scan in self.sf[first:]:
            no = str(scan.getNumber())
            cmd = scan.getCommand()
            #item = QTreeWidgetItem(['', str(scan)])
            item = QTreeWidgetItem([no,cmd])
            self.treeItems.append(item)
            self.scantree.addTopLevelItem(item)
            sn += 1
        return sn

    def updateFile(self):
        if self.sf.update():
            self._updateFile()

    def _updateFile(self):
        if self.scanselected is None or self.scanselected == self.nb_scans - 1:
            autoselect = 1
        else:
            autoselect = 0

        if len(self.sf) > self.nb_scans:
            self.nb_scans = self.addScansToTree(self.nb_scans)

        if autoselect and len(self.sf) > 0:
            self.selectScan(-1, force=True)

        self.scantree.resizeColumnToContents(0)

    def treeClicked(self, item, column):
        # TODO. is this really necessary? It should be active (visible) 
        #     before it is clicked
        self.setActive()

    
    def selectionChanged(self):
        """Overlay all selected scans in the plot, but update metadata only for the first one."""
        selected_indices = [
            idx for idx, item in enumerate(self.treeItems) if item.isSelected()
        ]

        if not selected_indices:
            log.log(3, "No scans selected")
            return

        # Clear existing curves
        if hasattr(self.plot, "curves"):
            self.plot.curves.clear()

        # --- update metadata for primary scan WITHOUT resetting selection
        primary_scanno = selected_indices[0]
        try:
            scan = self.sf[primary_scanno]
            self.currentScan = scan
            self.scanselected = primary_scanno

            data = scan.getData()
            labels = scan.getLabels()
            scanmeta = {
                'title': f"Scan {scan.getNumber()} - {scan.getCommand()}",
                'command': scan.getCommand(),
                'scanno': scan.getNumber(),
            }
            scanmeta.update(scan.getMeta())

            self.metadata = {}
            self.metadata.update(scanmeta)

            # refresh datasource
            self.setData(data, labels, scanmeta)

        except Exception as e:
            import traceback
            log.log(2, f"Error setting primary scan metadata: {e}")
            log.log(2, traceback.format_exc())

        # --- plot all selected scans (overlay)
        for scanno in selected_indices:
            try:
                scan = self.sf[scanno]
                data = scan.getData()
                labels = scan.getLabels()
                num = scan.getNumber()
                cmd = scan.getCommand()

                if not data.any() or len(labels) < 2:
                    continue

                x = data[:, 0]
                y = data[:, -1]

                curve_name = f"scan{num}_{labels[-1]}"
                self.plot.addCurve(curve_name)
                curve = self.plot.curves[curve_name]

                curve._x = x
                curve._y = y
                curve.attach()
                curve.setColor(self.plot.colorTable.getColor(curve_name))
                curve.mne = f"Scan {num}: {cmd}"

            except Exception as e:
                import traceback
                log.log(2, f"Error overlaying scan {scanno}: {e}")
                log.log(2, traceback.format_exc())

        # Force redraw
        self.plot.queue_replot()


    def getAllItems(self):
        root = self.scantree.invisibleRootItem()
        return self.getItems(root)

    def getItems(self, rootitem):
        nb_childs = rootitem.childCount()
        retlist = []

        for itno in range(nb_childs):
            child = rootitem.child(itno)
            retlist.append(child)
            retlist.extend(self.getItems(child))
        return retlist

    def getMcaData(self, index):
        if self.currentScan is not None:
            return self.currentScan.getMcaData(index)

    def next(self):
        scanno = self.scanselected
        scanno += 1
        if scanno < len(self.sf):
            self.selectScan(scanno)

    def prev(self):
        scanno = self.scanselected
        if scanno > 0:
            scanno -= 1
            self.selectScan(scanno)

    def selectScan(self, scanno, force=False):

        try:
            scan = self.sf[scanno]
    
            if scanno < 0:
                scanno = len(self.sf) + scanno
    
            if scanno == self.scanselected and force is False:
                return
    
            self.scanselected = scanno
            self.currentScan = scan
    
            data = scan.getData()
    
            self.datastatus = DATA_FILE
    
            labels = scan.getLabels()
    
            scanmeta = {
                'title':          "Scan %d - %s" % (scan.getNumber(), scan.getCommand()),
                'command':        scan.getCommand(),
                'scanno':         scan.getNumber(),
            }
    
            scanobj = Scan(scanmeta['command'])
            self.setScanObject(scanobj)
    
            if data.any():
                if len(labels) > 0:
                    scanmeta['xColumn'] = labels[0]
                    scanmeta['yColumns'] = [labels[-1], ]
    
            scanmeta.update(scan.getMeta())
    
            self.metadata = {}
            self.metadata.update(scanmeta)
    
            self.scantree.setCurrentItem(self.treeItems[scanno])
    
            self.setData(data, labels, scanmeta)

            mcas = [mca.data for mca in scan.getMcas()]
            if len( mcas ) > 0:
                self.app.show_mcas( mcas, parent=self )
        except:
            import traceback
            log.log(2, "error selecting scan")
            log.log(2, traceback.format_exc())


def main_test():

    filename = sys.argv[1]
    app = QApplication([])
    win = QMainWindow()
    wid = SpecFileSource(None, filename)
    win.setWindowTitle('Spec File Browser test')

    win.setCentralWidget(wid)
    win.setGeometry(200, 100, 400, 400)
    win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: %s filename" % sys.argv[0])
        sys.exit(1)

    main_test()
