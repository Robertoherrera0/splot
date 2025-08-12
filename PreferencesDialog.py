#******************************************************************************
#
#  @(#)PreferencesDialog.py	3.5  12/13/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2018,2019,2020
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
from widgets.PreferencesUIDialog import Ui_preferencesDialog
from SwitchButton import SwitchButton
from Preferences import Preferences
from HelpDialog import HelpDialog
from pyspec.css_logger import log
import copy

import themes

class PreferencesDialog(QDialog, Ui_preferencesDialog):

    def __init__(self,parent):
        super(PreferencesDialog, self).__init__(parent)

        self.prefs = Preferences()
        self.orig_prefs = copy.copy(self.prefs)
  
        self.setupUi(self)
        self.serverActiveRadio.hide() 
        self.serverSwitch = SwitchButton()
        self.horizontalLayout.insertWidget(0, self.serverSwitch)

        self.themeCombo.currentIndexChanged.connect(self.theme_changed)
        self.serverSwitch.toggled.connect(self.server_toggled)

        self.serverHelpButton.clicked.connect(self.showServerHelp)
        self.themeHelpButton.clicked.connect(self.showThemeHelp)
        self.serverName.textChanged.connect(self.server_name_changed)

        # default values
        self.serv_runs = False
        self.serv_name = ""
        self.allow_name_change = True

    def _update(self):

        self.themes = themes.get_themes()
        current_theme = self.prefs['theme']

        self.themeCombo.addItems(list(self.themes))

        if current_theme in self.themes:
            idx = self.themes.index(current_theme)
            self.themeCombo.setCurrentIndex(idx)

        if self.serv_runs:
            self.serverSwitch.setChecked(True)
        else:
            self.serverSwitch.setChecked(False)

        self.serverName.setText(str(self.serv_name)) 

        if not self.allow_name_change:
            self.serverSwitch.setDisabled(True)
            self.serverName.setDisabled(True)

    def show(self):
        QDialog.show(self)
        self._update()
        self.setFixedSize(self.size())

    def set_info(self, info):
        self.serv_runs = info['running']
        self.serv_name = info['name']
        self.allow_name_change = info['allow_name_change']

    def theme_changed(self, themeidx):
        themename = self.themes[themeidx]
        self.prefs["theme"] = themename

    def server_toggled(self,newstate):
        self.serv_runs = newstate

    def server_name_changed(self,newtxt):
        self.serv_name = str(newtxt)

    def showThemeHelp(self):
        diag = HelpDialog(self, filename="themes.html")
        diag.setTitle("SPlot Themes Information")
        diag.show()

    def showServerHelp(self):
        diag = HelpDialog(self, filename="cmdserver.html")
        diag.setTitle("SPlot Command Server ")
        diag.show()

    def accept(self):
        self.close()
        
        if self.serv_runs:
            self.prefs.setValue('cmd_server', self.serv_name)
        else:
            self.prefs.removeValue('cmd_server')
        self.prefs.save()

        self.parent().apply_command_server_prefs(self.serv_runs, self.serv_name)

    def cancel(self):
        for key,value in self.orig_prefs.items():
            self.prefs[key] = value

def main():
    import sys
    app = QApplication(sys.argv)
    form = PreferencesDialog(None)
    form.setValues([True, "torito", False])
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
