# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PreferencesUIDialog.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from pyspec.graphics.QVariant import *

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
except NameError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)

class Ui_preferencesDialog(object):
    def setupUi(self, preferencesDialog):
        try:
            ok_button = QDialogButtonBox.Ok
            cancel_button = QDialogButtonBox.Cancel
        except AttributeError:
            ok_button = QDialogButtonBox.StandardButton.Ok
            cancel_button = QDialogButtonBox.StandardButton.Cancel
        preferencesDialog.setObjectName(_fromUtf8("preferencesDialog"))
        preferencesDialog.resize(420, 176)
        self.buttonBox = QDialogButtonBox(preferencesDialog)
        self.buttonBox.setGeometry(QRect(70, 140, 341, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(ok_button|cancel_button)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.preferencesGroup = QGroupBox(preferencesDialog)
        self.preferencesGroup.setGeometry(QRect(10, 10, 481, 121))
        self.preferencesGroup.setFlat(False)
        self.preferencesGroup.setObjectName(_fromUtf8("preferencesGroup"))
        self.gridLayoutWidget = QWidget(self.preferencesGroup)
        self.gridLayoutWidget.setGeometry(QRect(0, 30, 401, 91))
        self.gridLayoutWidget.setObjectName(_fromUtf8("gridLayoutWidget"))
        self.gridLayout = QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.themeCombo = QComboBox(self.gridLayoutWidget)
        self.themeCombo.setObjectName(_fromUtf8("themeCombo"))
        self.gridLayout.addWidget(self.themeCombo, 0, 1, 1, 1)
        self.themeLabel = QLabel(self.gridLayoutWidget)
        self.themeLabel.setObjectName(_fromUtf8("themeLabel"))
        self.gridLayout.addWidget(self.themeLabel, 0, 0, 1, 1)
        self.serverLabel = QLabel(self.gridLayoutWidget)
        self.serverLabel.setObjectName(_fromUtf8("serverLabel"))
        self.gridLayout.addWidget(self.serverLabel, 2, 0, 1, 1)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.serverActiveRadio = QRadioButton(self.gridLayoutWidget)
        self.serverActiveRadio.setObjectName(_fromUtf8("serverActiveRadio"))
        self.horizontalLayout.addWidget(self.serverActiveRadio)
        spacerItem = QSpacerItem(20, 29, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QLabel(self.gridLayoutWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.serverName = QLineEdit(self.gridLayoutWidget)
        self.serverName.setObjectName(_fromUtf8("serverName"))
        self.horizontalLayout.addWidget(self.serverName)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)
        self.themeHelpButton = QToolButton(self.gridLayoutWidget)
        self.themeHelpButton.setObjectName(_fromUtf8("themeHelpButton"))
        self.gridLayout.addWidget(self.themeHelpButton, 0, 2, 1, 1)
        self.serverHelpButton = QToolButton(self.gridLayoutWidget)
        self.serverHelpButton.setObjectName(_fromUtf8("serverHelpButton"))
        self.gridLayout.addWidget(self.serverHelpButton, 2, 2, 1, 1)
        self.gridLayout.setColumnStretch(0, 2)
        self.gridLayout.setColumnStretch(1, 3)

        self.retranslateUi(preferencesDialog)
        self.buttonBox.accepted.connect(preferencesDialog.accept)
        self.buttonBox.rejected.connect(preferencesDialog.reject)
        #QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), preferencesDialog.accept)
        #QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), preferencesDialog.reject)
        #QtCore.QMetaObject.connectSlotsByName(preferencesDialog)

    def retranslateUi(self, preferencesDialog):
        preferencesDialog.setWindowTitle(_translate("preferencesDialog", "Application Preferences", None))
        self.preferencesGroup.setTitle(_translate("preferencesDialog", "Preferences:", None))
        self.themeLabel.setText(_translate("preferencesDialog", "Application Theme:", None))
        self.serverLabel.setText(_translate("preferencesDialog", "Command server: ", None))
        self.serverActiveRadio.setText(_translate("preferencesDialog", "Active", None))
        self.label.setText(_translate("preferencesDialog", "Name:", None))
        self.themeHelpButton.setText(_translate("preferencesDialog", "...", None))
        self.serverHelpButton.setText(_translate("preferencesDialog", "...", None))

