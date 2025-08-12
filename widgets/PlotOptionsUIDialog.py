# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PlotOptionsUIDialog.ui'
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

class Ui_plotOptionsDialog(object):
    def setupUi(self, plotOptionsDialog):
        plotOptionsDialog.setObjectName(_fromUtf8("plotOptionsDialog"))
        plotOptionsDialog.resize(461, 219)
        try:
            sizePolicy = QSizePolicy_(QSizePolicy.Expanding, QSizePolicy.Expanding)
        except NameError:
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(plotOptionsDialog.sizePolicy().hasHeightForWidth())
        plotOptionsDialog.setSizePolicy(sizePolicy)
        self.verticalLayoutWidget_2 = QWidget(plotOptionsDialog)
        self.verticalLayoutWidget_2.setGeometry(QRect(10, 10, 441, 201))
        self.verticalLayoutWidget_2.setObjectName(_fromUtf8("verticalLayoutWidget_2"))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QLabel(self.verticalLayoutWidget_2)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.optionsLayout = QGridLayout()
        #self.optionsLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.optionsLayout.setSpacing(6)
        self.optionsLayout.setObjectName(_fromUtf8("optionsLayout"))
        self.useDotsCheck = QCheckBox(self.verticalLayoutWidget_2)
        self.useDotsCheck.setObjectName(_fromUtf8("useDotsCheck"))
        self.optionsLayout.addWidget(self.useDotsCheck, 0, 1, 1, 1)
        self.showLegendCheck = QCheckBox(self.verticalLayoutWidget_2)
        self.showLegendCheck.setObjectName(_fromUtf8("showLegendCheck"))
        self.optionsLayout.addWidget(self.showLegendCheck, 3, 1, 1, 1)
        self.useLinesCheck = QCheckBox(self.verticalLayoutWidget_2)
        self.useLinesCheck.setObjectName(_fromUtf8("useLinesCheck"))
        self.optionsLayout.addWidget(self.useLinesCheck, 1, 1, 1, 1)
        self.legendPositionCombo = QComboBox(self.verticalLayoutWidget_2)
        self.legendPositionCombo.setObjectName(_fromUtf8("legendPositionCombo"))
        self.optionsLayout.addWidget(self.legendPositionCombo, 3, 3, 1, 1)
        self.lineThickLabel = QLabel(self.verticalLayoutWidget_2)
        self.lineThickLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lineThickLabel.setObjectName(_fromUtf8("lineThickLabel"))
        self.optionsLayout.addWidget(self.lineThickLabel, 1, 2, 1, 1)
        self.showErrorBarsCheck = QCheckBox(self.verticalLayoutWidget_2)
        self.showErrorBarsCheck.setObjectName(_fromUtf8("showErrorBarsCheck"))
        self.optionsLayout.addWidget(self.showErrorBarsCheck, 2, 1, 1, 1)
        self.legendLabel = QLabel(self.verticalLayoutWidget_2)
        self.legendLabel.setObjectName(_fromUtf8("legendLabel"))
        self.optionsLayout.addWidget(self.legendLabel, 3, 0, 1, 1)
        self.errorBarsLabel = QLabel(self.verticalLayoutWidget_2)
        self.errorBarsLabel.setObjectName(_fromUtf8("errorBarsLabel"))
        self.optionsLayout.addWidget(self.errorBarsLabel, 2, 0, 1, 1)
        self.linesLabel = QLabel(self.verticalLayoutWidget_2)
        self.linesLabel.setObjectName(_fromUtf8("linesLabel"))
        self.optionsLayout.addWidget(self.linesLabel, 1, 0, 1, 1)
        self.legentPositionLabel = QLabel(self.verticalLayoutWidget_2)
        self.legentPositionLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.legentPositionLabel.setObjectName(_fromUtf8("legentPositionLabel"))
        self.optionsLayout.addWidget(self.legentPositionLabel, 3, 2, 1, 1)
        self.lineThickSpin = QSpinBox(self.verticalLayoutWidget_2)
        try:
            sizePolicy = QSizePolicy_(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except NameError:
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineThickSpin.sizePolicy().hasHeightForWidth())
        self.lineThickSpin.setSizePolicy(sizePolicy)
        self.lineThickSpin.setMinimum(1)
        self.lineThickSpin.setMaximum(10)
        self.lineThickSpin.setObjectName(_fromUtf8("lineThickSpin"))
        self.optionsLayout.addWidget(self.lineThickSpin, 1, 3, 1, 1)
        self.dotsLabel = QLabel(self.verticalLayoutWidget_2)
        self.dotsLabel.setObjectName(_fromUtf8("dotsLabel"))
        self.optionsLayout.addWidget(self.dotsLabel, 0, 0, 1, 1)
        self.dotSizeSpin = QSpinBox(self.verticalLayoutWidget_2)
        try:
            sizePolicy = QSizePolicy_(QSizePolicy.Ignored, QSizePolicy.Fixed)
        except NameError:
            sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dotSizeSpin.sizePolicy().hasHeightForWidth())
        self.dotSizeSpin.setSizePolicy(sizePolicy)
        self.dotSizeSpin.setMinimumSize(QSize(0, 0))
        self.dotSizeSpin.setMinimum(1)
        self.dotSizeSpin.setMaximum(14)
        self.dotSizeSpin.setObjectName(_fromUtf8("dotSizeSpin"))
        self.optionsLayout.addWidget(self.dotSizeSpin, 0, 3, 1, 1)
        self.dotSizeLabel = QLabel(self.verticalLayoutWidget_2)
        self.dotSizeLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dotSizeLabel.setObjectName(_fromUtf8("dotSizeLabel"))
        self.optionsLayout.addWidget(self.dotSizeLabel, 0, 2, 1, 1)
        self.optionsLayout.setColumnStretch(0, 4)
        self.optionsLayout.setRowStretch(0, 1)
        self.optionsLayout.setRowStretch(1, 1)
        self.optionsLayout.setRowStretch(2, 1)
        self.optionsLayout.setRowStretch(3, 1)
        self.verticalLayout.addLayout(self.optionsLayout)
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setObjectName(_fromUtf8("bottomLayout"))
        self.restoreButton = QPushButton(self.verticalLayoutWidget_2)
        self.restoreButton.setObjectName(_fromUtf8("restoreButton"))
        self.bottomLayout.addWidget(self.restoreButton)
        self.buttonBox = QDialogButtonBox(self.verticalLayoutWidget_2)
        self.buttonBox.setOrientation(Qt.Horizontal)
        try:
            self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        except AttributeError:
            self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.bottomLayout.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.bottomLayout)
        self.widget = QWidget(plotOptionsDialog)
        self.widget.setGeometry(QRect(40, 440, 120, 80))
        try:
            sizePolicy = QSizePolicy_(QSizePolicy.Expanding, QSizePolicy.Expanding)
        except NameError:
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName(_fromUtf8("widget"))

        self.retranslateUi(plotOptionsDialog)
        self.buttonBox.accepted.connect(plotOptionsDialog.accept)
        self.buttonBox.rejected.connect(plotOptionsDialog.reject)


    def retranslateUi(self, plotOptionsDialog):
        plotOptionsDialog.setWindowTitle(_translate("plotOptionsDialog", "Dialog", None))
        self.label.setText(_translate("plotOptionsDialog", "Plot Options:", None))
        self.useDotsCheck.setText(_translate("plotOptionsDialog", "Use", None))
        self.showLegendCheck.setText(_translate("plotOptionsDialog", "Show", None))
        self.useLinesCheck.setText(_translate("plotOptionsDialog", "Draw", None))
        self.lineThickLabel.setText(_translate("plotOptionsDialog", "Thickness: ", None))
        self.showErrorBarsCheck.setText(_translate("plotOptionsDialog", "Show", None))
        self.legendLabel.setText(_translate("plotOptionsDialog", "Legend on Plot", None))
        self.errorBarsLabel.setText(_translate("plotOptionsDialog", "Error bars: ", None))
        self.linesLabel.setText(_translate("plotOptionsDialog", "Lines", None))
        self.legentPositionLabel.setText(_translate("plotOptionsDialog", "Position: ", None))
        self.dotsLabel.setText(_translate("plotOptionsDialog", "Dots ", None))
        self.dotSizeLabel.setText(_translate("plotOptionsDialog", "Dot Size: ", None))
        self.restoreButton.setText(_translate("plotOptionsDialog", "Restore Defaults", None))

