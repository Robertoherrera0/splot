#******************************************************************************
#
#  @(#)RoiSelectionDialog.py	3.5  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2018,2020,2021,2023,2024
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

class RoiSelectionDialog(QDialog):

    operations = ['sum','ave','max','min']

    def __init__(self, parent):

        QDialog.__init__(self, parent)
        self.parent = parent
        self.device = None
        self.dtype = None

        self.counters = {}
        self.devices = []

        self.setWindowTitle("ROI Selection")
        self.setModal(False)

        vBoxLayout = QVBoxLayout()
        self.setLayout(vBoxLayout)

        gridLayout = QGridLayout()

        self.cnt_label = QLabel("Counter:")

        self.dev_label = QLabel("Device:")
        self.dev_cbox = QComboBox()
        self.dev_cbox.currentIndexChanged.connect(self.device_changed)
        self.devdesc_label = QLabel()

        self.mne_label = QLabel("Mnemonic:")
        self.name_label = QLabel("Name:")

        self.mne_cbox = QComboBox()
        self.mne_cbox.currentIndexChanged.connect(self.counter_changed)
        self.name_ledit = QLineEdit()

        oper_label = QLabel("ROI Operation:")
        self.oper_cbox = QComboBox()
        self.oper_cbox.addItems(self.operations)
        self.oper_cbox.currentIndexChanged.connect(self.operation_changed)

        self.cntadd_bt = QPushButton("Add New")
        self.cntadd_bt.clicked.connect(self.counter_add)

        self.cntdel_bt = QPushButton("Delete")
        self.cntdel_bt.clicked.connect(self.counter_delete)

        self.row_label = QLabel("Row")
        self.col_label = QLabel("Column")
        from_label = QLabel("From:")
        to_label = QLabel("To:")

        self.row_beg_ety = QLineEdit()
        self.row_end_ety = QLineEdit()
        self.col_beg_ety = QLineEdit()
        self.col_end_ety = QLineEdit()

        row = 0

        gridLayout.addWidget(self.mne_label,row,1)
        gridLayout.addWidget(self.name_label,row,2)
        row += 1
        
        gridLayout.addWidget(self.cnt_label,row,0)
        gridLayout.addWidget(self.mne_cbox,row,1)
        gridLayout.addWidget(self.name_ledit,row,2)
        row += 1

        gridLayout.addWidget(self.cntadd_bt,row,1)
        gridLayout.addWidget(self.cntdel_bt,row,2)
        row += 1

        gridLayout.addWidget(self.dev_label,row,0)
        gridLayout.addWidget(self.dev_cbox,row,1)
        gridLayout.addWidget(self.devdesc_label,row,2)
        row += 1

        gridLayout.addWidget(oper_label,row,0)
        gridLayout.addWidget(self.oper_cbox,row,1,1,2)
        row += 1

        gridLayout.addWidget(from_label, row,1)
        gridLayout.addWidget(to_label, row,2)
        row += 1

        gridLayout.addWidget(self.row_label, row,0)
        gridLayout.addWidget(self.row_beg_ety,row,1) 
        gridLayout.addWidget(self.row_end_ety,row,2)
        row += 1

        gridLayout.addWidget(self.col_label, row,0)
        gridLayout.addWidget(self.col_beg_ety,row,1)
        gridLayout.addWidget(self.col_end_ety,row,2)
        row += 1

        line_sep = QFrame()
        try:
            line_sep.setFrameShape(QFrame.HLine)
            line_sep.setFrameShadow(QFrame.Sunken)
        except AttributeError:
            line_sep.setFrameShape(QFrame.Shape.HLine)
            line_sep.setFrameShadow(QFrame.Shadow.Sunken)

        gridLayout.addWidget(line_sep,row,0,0,3)
        row += 1

        buttonGroup = QWidget()
        buttonLayout = QHBoxLayout()
        buttonGroup.setLayout(buttonLayout)

        okPushButton = QPushButton("Apply")
        okPushButton.clicked.connect(self.accept_changes)

        cancelPushButton = QPushButton("Cancel")
        cancelPushButton.clicked.connect(self.do_cancel)

        closePushButton = QPushButton("Close")
        closePushButton.clicked.connect(self.do_close)

        buttonLayout.addWidget(okPushButton)
        # buttonLayout.addWidget(cancelPushButton)
        buttonLayout.addWidget(closePushButton)

        gridLayout.addWidget(buttonGroup,row,1,1,2)

        vBoxLayout.addLayout(gridLayout)

        self.set_range()
        self.set_data_type()

    def keyPressEvent(self, ev):
        ky = ev.key()
        if ky in ( Qt.Key_Enter, Qt.Key_Return): 
            self.accept_changes()  
        else:
            QDialog.keyPressEvent(self,ev)

    def set_data_type(self, dtype="image"):
        if dtype == "image":
            self.col_beg_ety.show()
            self.col_end_ety.show()
    
            self.row_label.setText("Row")
            self.col_label.show()
        else:
            self.col_beg_ety.hide()
            self.col_end_ety.hide()
    
            self.row_label.setText("Channel")
            self.col_label.hide()

        self.dtype = dtype

    def operation_changed(self, idx):
        operation = str(self.oper_cbox.currentText()).lower() 
        cur_cnt = str(self.mne_cbox.currentText())
        self.counters[cur_cnt]['oper'] = operation

    def counter_add(self):
        new_mne, ok = QInputDialog.getText(self, "Add new Counter", "Mnemonic:")

        if ok and str(new_mne) != "":
           self.mne_cbox.addItem(new_mne)  
           self.mne_cbox.setCurrentIndex(self.mne_cbox.count()-1)
           self.name_ledit.setText(new_mne)
           self.set_range()

    def counter_delete(self):
        try:
            mne = str(self.mne_cbox.currentText())
            yn = QMessageBox.question(self, "Delete ROI", 
                                "Do you really want to delete counter %s?"%mne,
                                 QMessageBox.Yes|QMessageBox.No)

            if yn == QMessageBox.Yes:
                 self.parent.delete_roi(mne)
        except:
            import traceback
            traceback.print_exc()
                                         
    def do_nothing(self):
        pass

    def device_changed(self, idx):
        devdesc = self.devices[idx][1]
        self.devdesc_label.setText(devdesc)
        self.current_device = self.devices[idx][0]

        if self.current_device[0].startswith('i'):
            self.set_data_type('image')
        else:
            self.set_data_type('mca')

    def select_device(self, device):
        idx = 0
        for dev, _d in self.devices:
            if device == dev:
                self.dev_cbox.setCurrentText(dev)
                self.device_changed(idx)
                break
            idx += 1
        
    def counter_changed(self, idx):
        cur_cnt = str(self.mne_cbox.currentText())
        self.select_counter(cur_cnt)

    def select_counter(self, cnt):
        oper = self.counters[cnt].get('oper', 'sum')
        print("Counter changed to %s, operation is %s" % (cnt, oper))

        self.oper_cbox.setCurrentText(oper)

        self.name_ledit.setText(self.counters[cnt].get('name',cnt))

        device = self.counters[cnt].get('device',None)

        self.select_device(device)

        self.set_range(self.counters[cnt].get('range',[0,-1,0,-1]))

    def set_range(self, range=None):
        log.log(2, "roi range is %s" % str(range))
        if range is None:
            range = [0,-1,0,-1]

        r0, r1 = map(str, range[0:2])

        self.row_beg_ety.setText(r0)  # used ad ch_beg, ch_end
        self.row_end_ety.setText(r1)
            
        if len(range) == 4:
            r2, r3 = map(str, range[2:4])
            self.col_beg_ety.setText(str(r2))
            self.col_end_ety.setText(str(r3))

    def set_devices(self, devices):

        self.devices = []

        for dev in devices.split(";"):
            p = dev.split(":")
            if len(p) == 2:
                unit,desc = p
                self.devices.append([unit,desc])

            self.dev_cbox.clear()
            self.dev_cbox.addItems([dev[0] for dev in self.devices])

        log.log(2,"set_devices %s" % devices)

        if len(self.devices) > 0:
            self.device_changed(0) 

    def set_counters(self, counters):

        self.counters = {}
        device0 = None

        for cnt in counters.split(";"):
            p = cnt.split(":")

            if len(p) == 5:
                device, mne, name, oper, conf = p 
                self.counters[mne] = {}
                self.counters[mne]['device'] = device 
                self.counters[mne]['oper'] = oper
                self.counters[mne]['range'] = conf.split(",")
                self.counters[mne]['name'] = name
                if device is None:
                    device0 = device

        self.mne_cbox.clear()
        self.mne_cbox.addItems(list(self.counters.keys()))

        cnt = str(self.mne_cbox.currentText())
        oper = self.counters[cnt]['oper'] 
        self.oper_cbox.setCurrentText(oper)
        self.select_device(device0)

    def do_cancel(self):
        self.reject()

    def do_close(self):
        self.reject()

    def accept_changes(self):
        log.log(2, "applying changes")

        try:
            ctmne = self.mne_cbox.currentText()
            ctname = str(self.name_ledit.text())
            log.log(2, "applying changes 1")
 
            device = self.dev_cbox.currentText()

            log.log(2, "applying changes 2")

            operation = self.oper_cbox.currentText()

            rowbeg = str(self.row_beg_ety.text())
            rowend = str(self.row_end_ety.text())
            colbeg = str(self.col_beg_ety.text())
            colend = str(self.col_end_ety.text())

            if self.dtype == 'image':
                roi_values = [rowbeg, rowend, colbeg, colend]
            else:
                roi_values = [rowbeg, rowend]  # used as chbeg, chend

            log.log(3, "applying changes 2")

            if self.parent is not None:
                self.parent.set_roi(device, ctmne, ctname, operation, roi_values)
            else:
                print(device,ctmne,ctname,operation,roi_values)
        except:
            import traceback
            log.log(2, tracebackformat_exc())


# Returns a two value tuple with connpars as first parameter and variable
# name as second parameter
def getRoiSelection(parent): 

    cnts = "img0:iroi0:IROI 0:sum:19,899,23,223;img0:iroi1:IROI 1:ave:0,-1,0,-1;mca0:mroi0:MROI 0:sum:0,-1"

    dialog = RoiSelectionDialog(parent)
    dialog.set_counters(cnts)
    dialog.set_range([34,300,11,600])

    result = dialog.exec_()

    if result == QDialog.Accepted:
        retval = dialog.get_values()
    else:
        retval = None

    dialog.destroy()
    return retval

if __name__ == '__main__':
    app = QApplication([])
    print(getRoiSelection(None))
