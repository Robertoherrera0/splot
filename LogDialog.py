#******************************************************************************
#
#  @(#)LogDialog.py	3.6  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2016,2017,2018,2020,2023,2024
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

import logging
import time
import os

from pyspec.graphics.QVariant import *
from pyspec.graphics import qt_variant
from css_logger import log

COLUMNS = ["Date", "Level", "File", "Line", "Function", "Message"]
DATE_COLUMN, LEVEL_COLUMN, PATH_COLUMN, LINE_COLUMN, FUNC_COLUMN, MSG_COLUMN = range(len(COLUMNS))

LOG_COLORS = {
   logging.INFO:  "white" ,
   logging.DEBUG:  "#66ff66" ,
   logging.WARNING:  "yellow" ,
   logging.ERROR:  "#ff6666" ,
   logging.CRITICAL:  "magenta" ,
}

class LogPanelItem(QTreeWidgetItem):
     def __init__(self, tree):
         QTreeWidgetItem.__init__(self, tree, QTreeWidgetItem.Type)
         self.tree = tree

     def setRecord(self, record):
         fmt_time = time.strftime(time.strftime("%H:%M:%S",time.localtime(record.created)))
         color = LOG_COLORS[record.levelno]

         level_label = QLabel(self.tree) # if no parent is given PySide will crash on setItemWidget
         level_label.setText(record.levelname)

         if record.levelno > logging.INFO: 
             level_label.setStyleSheet("background-color: %s;font-weight: bold" % color)
         else:
             level_label.setStyleSheet("background-color: %s;" % color)
         self.tree.setItemWidget(self, LEVEL_COLUMN, level_label)

         self.setText(DATE_COLUMN, fmt_time)
         self.setText(PATH_COLUMN, os.path.basename(record.pathname))
         self.setText(LINE_COLUMN, str(record.lineno))
         self.setText(FUNC_COLUMN, record.funcName)
         self.setText(MSG_COLUMN, record.msg)

class LogPanel(QTreeWidget):

     def __init__(self, logger_name=None):

         self.records = []
         self.max_records = 500

         self.logger_name = None
         self.loghandler = None
         self.loglevel = logging.WARNING  # default shows all (limited by the level of the logger )

         QTreeWidget.__init__(self)

         self.setColumnCount(len(COLUMNS))
         self.setHeaderLabels(COLUMNS)

         self.setRootIsDecorated(False)
         self.setAlternatingRowColors(True)

         if qt_variant() in ["PyQt4", "PySide"]:
             self.header().setResizeMode(DATE_COLUMN, QHeaderView.ResizeToContents)
             self.header().setResizeMode(LEVEL_COLUMN, QHeaderView.ResizeToContents)
             self.header().setResizeMode(PATH_COLUMN, QHeaderView.ResizeToContents)
             self.header().setResizeMode(LINE_COLUMN, QHeaderView.ResizeToContents)
             self.header().setResizeMode(FUNC_COLUMN, QHeaderView.ResizeToContents)
         else:
             if qt_variant() in ["PyQt6", "PySide6"]:
                 to_contents = QHeaderView.ResizeMode.ResizeToContents
             else:
                 to_contents = QHeaderView.ResizeToContents
             self.header().setSectionResizeMode(DATE_COLUMN, to_contents)
             self.header().setSectionResizeMode(LEVEL_COLUMN, to_contents)
             self.header().setSectionResizeMode(PATH_COLUMN, to_contents)
             self.header().setSectionResizeMode(LINE_COLUMN, to_contents)
             self.header().setSectionResizeMode(FUNC_COLUMN, to_contents)

         self.header().setStretchLastSection(True)

         self.items = []

         if logger_name is not None:
            self.addLogger(logger_name)

     def setMaxRecords(self, max_records):
         self.max_records = max_records

     def addLogger(self, logger_name):
         if self.logger_name: 
             # we should stop a handler if it is still getting records
             pass

         self.loghandler = GUILoggerHandler(self)
         logger = logging.getLogger(logger_name)
         logger.addHandler(self.loghandler)
         self.setLevel(self.loglevel)

     def setLevel(self, level):
         self.level = level
         if self.loghandler:
             self.loghandler.setLevel(level)

     def setMaxRecords(self, max_records):
         self.max_records = max_records
         if self.max_records:
             self._update()

     def showEvent(self,ev):
         log.log(2, "showing log panel max_records = %s " % self.max_records)
         log.log(2, "showing log panel total records = %s " % len(self.records))
         self._update()
         QTreeWidget.showEvent(self,ev)
 
     def addRecord(self, record):
         self.records.append(record)
         self._update()

     def _update(self):
         oldlen = len(self.items)

         # pop records from beginning if more than max
         record_no = len(self.records)
         while record_no > self.max_records:
             self.records.pop(0)
             record_no -= 1

         # only in case max_records have changed
         item_no = len(self.records)  
         if len(self.items) > self.max_records:
             self.items.pop(0)
             self.takeTopLevelItem(item_no)

         no_items = len(self.items)
         no_records = len(self.records)

         if not self.isVisible():
             return

         record_no = no_records
         # add new items to match number of records
         while record_no > no_items:
             item = LogPanelItem(self)
             self.addTopLevelItem(item)
             self.items.append(item)
             record_no -= 1

         no = 0
         for record in reversed(self.records):
             item = self.items[no]
             item.setRecord(record)
             no += 1
         return

class LogDialog(QDialog):

    def __init__(self,logger_name):
        QDialog.__init__(self)
        vlayout = QVBoxLayout() 
        self.setLayout(vlayout)

        self.panel = LogPanel(logger_name)

        close_but = QPushButton("Close")
        close_but.setFixedWidth(80)
        close_but.clicked.connect(self.accept)

        vlayout.addWidget(self.panel)
        vlayout.addWidget(close_but)
        if qt_variant() == "PyQt6":
            vlayout.setAlignment(close_but,Qt.AlignmentFlag.AlignRight)
        else:
            vlayout.setAlignment(close_but,Qt.AlignRight)

    def setLevel(self, level):
        self.panel.setLevel(level)

    def setMaxRecords(self, max_records):
        self.panel.setMaxRecords(max_records)

    def sizeHint(self):
        return QSize(900,500)

class GUILoggerHandler(logging.Handler):
    def __init__(self,guipanel=None,*args):
        logging.Handler.__init__(self,*args)
        self.guipanel = guipanel

    def setWidget(self, gui_panel):
        self.guipanel = gui_panel

    def emit(self, record):
        if self.guipanel is not None:
            self.guipanel.addRecord(record)

def test_timer():
   #logger = logging.getLogger("splot")
   #logger.setLevel(logging.INFO)
   #logging.getLogger("splot").info("record")  
   #logging.getLogger("splot").warning("record")  
   log.log(3, "tres record")
   log.log(2, "dos record")
   log.log(1, "un record")

if __name__ == '__main__':
   from pyspec.graphics.QVariant import *
   app = QApplication([])
   win = QMainWindow()
   but = QPushButton("Show logger")

   log.start()

   dia = LogDialog("splot") 
   dia.setLevel(logging.WARNING)
   dia.setMaxRecords(20)
   
   but.clicked.connect(dia.show)

   win.setCentralWidget(but)
   win.show()

   timer = QTimer()
   timer.timeout.connect(test_timer)
   timer.start(500)
   app.exec_()

