#******************************************************************************
#
#  @(#)SpecConnectionDialog.py	3.12  01/09/24 CSS
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
from pyspec.css_logger import log
from Constants import *

from Preferences import Preferences

# pass if not available (allow server mode to connect)
try:
    from pyspec.client import spec_shm
    no_sharedmem = False
except:
    log.log(3,"Cannot import datashm. Shared memory functionality disabled")
    no_sharedmem = True


class SpecConnectionDialog(QDialog):

    def __init__(self, parent, exclude=None, speclist=None, host=None):

        self.prefs = Preferences()
        QDialog.__init__(self, parent)

        self.setWindowTitle("SPEC Remote Connection")
        self.setModal(True)

        vBoxLayout = QVBoxLayout()
        self.setLayout(vBoxLayout)

        gridLayout = QGridLayout()

        specLabel = QLabel("SPEC:")
        self.specEntry = QLineEdit()
        self.specCombo = QComboBox()

        if not speclist:
            speclist = getSpecList()

        if exclude:
           for it in exclude: 
               if it in speclist: 
                   speclist.pop(speclist.index(it))  

        if speclist:
            self.specCombo.addItems(speclist)

        if self.prefs['remotespec'] is not None:
            self.specEntry.setText(self.prefs['remotespec'])

        self.hostLabel = QLabel("Host:")
        self.hostEntry = QLineEdit("")
        self.hostEntry.setStyleSheet("background-color: #eeeeee")

        if self.prefs['remotehost'] is not None:
            self.hostEntry.setText(self.prefs['remotehost'])

        self.use_remote_rb = QRadioButton("Remote")
        self.use_remote_rb.setChecked(False)
        self.use_remote_rb.toggled.connect(self.remote_selected)

        gridLayout.addWidget(self.use_remote_rb, 0, 0)
        gridLayout.addWidget(specLabel, 1, 0)

        if speclist:
            gridLayout.addWidget(self.specCombo, 1, 1)
        gridLayout.addWidget(self.specEntry,1,1)

        gridLayout.addWidget(self.hostLabel, 2, 0)
        gridLayout.addWidget(self.hostEntry, 2, 1)

        if host is not None:
            self.remote_selected(True)
            self.use_remote_rb.setChecked(True)
            self.hostEntry.setText(host)
        else:
            self.remote_selected(False)
        
        buttonHBoxLayout = QHBoxLayout()

        okPushButton = QPushButton("Connect")
        okPushButton.clicked.connect(self.okPushButtonClicked)

        cancelPushButton = QPushButton("Cancel")
        cancelPushButton.clicked.connect(self.cancelPushButtonClicked)

        buttonHBoxLayout.addWidget(okPushButton)
        buttonHBoxLayout.addWidget(cancelPushButton)

        vBoxLayout.addLayout(gridLayout)
        vBoxLayout.addLayout(buttonHBoxLayout)

    def remote_selected(self, value):
        if value:
            self.specCombo.hide()
            self.specEntry.show()
            self.hostLabel.show()
            self.hostEntry.show()
        else:
            self.specCombo.show()
            self.specEntry.hide()
            self.hostLabel.hide()
            self.hostEntry.hide()

    def cancelPushButtonClicked(self):
        self.reject()

    def okPushButtonClicked(self):
        self.accept()

    def getSelection(self):
        use_remote = self.use_remote_rb.isChecked()

        if use_remote:
            host = self.hostEntry.text()
            if host != "":
                 self.prefs['remotehost'] = host
            spec = self.specEntry.text()
            if spec != "":
                self.prefs['remotespec'] = spec
            host = str(host)
            spec = str(spec)
        else:
            spec = self.specCombo.currentText()
            host = None

        if host and spec:
            return "%s:%s" % (host, spec)
        elif spec:
            return "%s" % (spec)
        else:
            return None

class SpecVariableDialog(QDialog):

    def __init__(self, parent, specname):

        self.prefs = Preferences()
        QDialog.__init__(self, parent)

        self.setWindowTitle("SPEC Variable Selection")
        self.setModal(True)

        vBoxLayout = QVBoxLayout()
        self.setLayout(vBoxLayout)

        gridLayout = QGridLayout()

        varnameLabel = QLabel("Variable name:")
        self.varnameCombo = QComboBox()
        self.varinfoLabel = QLabel()

        self.shm_varlist = getSHMVariables(specname)

        if self.shm_varlist:
            self.shm_varlist.sort(key=lambda v:v[0])
            varname_list = [var[0] for var in self.shm_varlist]
            log.log(2, str(varname_list))
            self.varnameCombo.addItems(varname_list)
            #self.varnameCombo.setCurrentIndex(-1)
            self.varnameCombo.setCurrentIndex(0)
            #self.varnameCombo.setEditable(True)
            self.varnameCombo.activated.connect(self.selectionChanged)
            self.varnameCombo.show()
        else:
            self.varnameCombo.hide()

        self.vartype_gb = QGroupBox()
        self.vartype_gb.setStyleSheet("QGroupBox::title { border: 0px ; border-radius: 0px; " \
                   "padding: 0px 0px 0px 0px; margin = 0px 0px 0px 0px } " \
                   "QGroupBox { border: 0px ; border-radius: 0px; padding: 0px 0px 0px 0px;} ");

        self.vartype_layout = QHBoxLayout()
        self.vartype_layout.setContentsMargins(0,0,0,0)

        self.vartype_gb.setLayout(self.vartype_layout)

        self.oned_rb = QRadioButton("1-D")
        self.twod_rb = QRadioButton("2-D")

        self.oned_rb.setChecked(False)
        self.twod_rb.setChecked(True)

        self.vartype_layout.addWidget(self.oned_rb)
        self.vartype_layout.addWidget(self.twod_rb)
        self.vartype_layout.setAlignment(Qt.AlignTop)

        self.followed_cb = QCheckBox("Follow changes")
        self.followed_cb.setChecked(True) 

        gridLayout.addWidget(varnameLabel, 1, 0)
        gridLayout.addWidget(self.varnameCombo, 1, 1)
        gridLayout.addWidget(self.varinfoLabel, 1, 2)

        gridLayout.addWidget(self.vartype_gb, 2, 0)
        gridLayout.addWidget(self.followed_cb, 2, 2)

        buttonHBoxLayout = QHBoxLayout()

        okPushButton = QPushButton("Select")
        okPushButton.clicked.connect(self.okPushButtonClicked)

        cancelPushButton = QPushButton("Cancel")
        cancelPushButton.clicked.connect(self.cancelPushButtonClicked)

        buttonHBoxLayout.addWidget(okPushButton)
        buttonHBoxLayout.addWidget(cancelPushButton)

        vBoxLayout.addLayout(gridLayout)
        vBoxLayout.addLayout(buttonHBoxLayout)

        self.selectionChanged()

    def cancelPushButtonClicked(self):
        self.reject()

    def okPushButtonClicked(self):
        self.accept()

    def selectionChanged(self):
        curtxt = self.varnameCombo.currentText() 

        found = False
        for varname,info in self.shm_varlist:
            if curtxt == varname:
                found = True
                break

        if not found:
            infotxt = ""  
            self.varinfoLabel.setText(infotxt)
            return 

        hint_1d = False
        only_1d = False

        infotxt = "(%d x %d)" % (info[0],info[1])
        is_mca = is_image = is_info = is_scan = is_frames = False

        if info[3] & 0x10: #mca
            infotxt = "mca %s" % infotxt
            is_mca = True
        if info[3] & 0x20: #image
            infotxt = "image %s" % infotxt
            is_image = True
        if info[3] & 0x40: #scan
            infotxt = "scan %s" % infotxt
            is_scan = True
        if info[3] & 0x80: #info
            infotxt = "info %s" % infotxt
            is_info = True
        if info[3] & 0x100: #frames
            infotxt = "frames %s" % infotxt
            is_frames = True
        
        if 1 in info[0:2]:
            log.log(2, "info is %s. can only be 1d" % (str(info)))
            only_1d = True
        elif 2 in info[0:2]:
            log.log(2, "info is %s. could be 1d" % (str(info)))
            hint_1d = True
        elif is_scan or is_mca:
            hint_1d = True

        if only_1d: 
            self.oned_rb.setChecked(True)
            self.twod_rb.setEnabled(False)
        elif hint_1d: 
            self.oned_rb.setChecked(True)
            self.twod_rb.setChecked(False)
            self.twod_rb.setEnabled(True)
        else:
            self.oned_rb.setChecked(False)
            self.twod_rb.setChecked(True)
            self.twod_rb.setEnabled(True)

        # uhmmm... something for a proper 1D selection
        # should be done if more than 2 columns in array
        # maybe the widget should take care of that

        self.varinfoLabel.setText(infotxt)

    def getSelection(self):
        shmvar = self.varnameCombo.currentText()

        varname = str(shmvar)

        is_1d = self.oned_rb.isChecked()
        is_2d = self.twod_rb.isChecked()

        follow_it = self.followed_cb.isChecked()

        if (is_2d):
            vartype = DATA_2D
        elif (is_1d):
            vartype = DATA_1DS
        else:
            vartype = "unknown"

        return [varname, vartype, follow_it]

def getSpecList(exclude=None):
    shm_speclist = None

    try:
        shm_list = spec_shm.getspeclist()
    except:
        shm_list = None

    if shm_list:
        shm_list.sort()

    # second method. get list of existing
    specd = os.getenv("SPECD", "/usr/local/lib/spec.d")
    if not os.path.exists(specd):
        # try directory where this file is installed
        splot_dir = os.path.dirname(__file__)
        specd = os.path.join(splot_dir,"..")

    import glob
    l1 = glob.glob("%s/*/config" % specd)
    l2 = glob.glob("%s/*/settings" % specd) 
 
    l1 = [ety[len(specd)+1:-(len("config")+1)] for ety in l1] 
    l2 = [ety[len(specd)+1:-(len("settings")+1)] for ety in l2] 

    specd_list = [ety for ety in l1 if ety in l2]

    if specd_list:
        specd_list.sort()

    if shm_list:
        spec_list = [ spec for spec in shm_list ]
        spec_list.extend(specd_list)  
    else:
        spec_list = specd_list  
    return spec_list

def getSHMVariables(specname):
    if no_sharedmem: 
       return None

    print("getting SHM variables for ", specname)

    parts = specname.split(":")
    print( parts )

    if len(parts) == 2:
        specapp = parts[1]
    elif len(parts) == 1:
        specapp = parts[0]
    else:
        log.log(1,"Wrong spec specification")
        return None

    print( "spec is ", specapp) 
    varlist = spec_shm.getarraylist(specapp)
    if "SCAN_D" in varlist:
        varlist.pop(varlist.index("SCAN_D"))

    retlist = []

    for var in varlist:
        varinfo = spec_shm.getarrayinfo(specapp,var)
        print("var: %s - info: %s" % (var,varinfo)) 
        retlist.append([var,varinfo])

    log.log(2, "returning %s" % str(retlist))
    return retlist

def getSpecVariableParameters(specname, parent=None):
    """
    Returns a 
    """
    dialog = SpecVariableDialog(parent, specname)

    try:
        exec_ = getattr(dialog, "exec_")
        is_accepted = QDialog.Accepted
    except AttributeError:
        exec_ = getattr(dialog, "exec")
        is_accepted = QDialog.DialogCode.Accepted

    result = exec_()

    if result == is_accepted:
        retval = dialog.getSelection()
    else:
        retval = None

    dialog.destroy()
    return retval
      
# Returns a two value tuple with connpars as first parameter and variable
# name as second parameter
def getSpecConnectionParameters(parent=None, host=None, exclude=None, speclist=None):

    dialog = SpecConnectionDialog(parent, host=host, exclude=exclude, speclist=speclist)

    try:
        exec_ = getattr(dialog, "exec_")
        is_accepted = QDialog.Accepted
    except AttributeError:
        exec_ = getattr(dialog, "exec")
        is_accepted = QDialog.DialogCode.Accepted

    result = exec_()

    if result == is_accepted:
        retval = dialog.getSelection()
    else:
        retval = None, None

    dialog.destroy()
    return retval

if __name__ == '__main__':
    print(getSpecList())
    app = QApplication([])
    print(getSpecVariableParameters("fourc"))
