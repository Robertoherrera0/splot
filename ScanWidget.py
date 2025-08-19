# #******************************************************************************
# #
# #  @(#)ScanWidget.py	3.8  01/09/24 CSS
# #
# #  "splot" Release 3
# #
# #  Copyright (c) 2013,2014,2015,2016,2017,2020,2023,2024
# #  by Certified Scientific Software.
# #  All rights reserved.
# #
# #  Permission is hereby granted, free of charge, to any person obtaining a
# #  copy of this software ("splot") and associated documentation files (the
# #  "Software"), to deal in the Software without restriction, including
# #  without limitation the rights to use, copy, modify, merge, publish,
# #  distribute, sublicense, and/or sell copies of the Software, and to
# #  permit persons to whom the Software is furnished to do so, subject to
# #  the following conditions:
# #
# #  The above copyright notice and this permission notice shall be included
# #  in all copies or substantial portions of the Software.
# #
# #  Neither the name of the copyright holder nor the names of its contributors
# #  may be used to endorse or promote products derived from this software
# #  without specific prior written permission.
# #
# #     * The software is provided "as is", without warranty of any   *
# #     * kind, express or implied, including but not limited to the  *
# #     * warranties of merchantability, fitness for a particular     *
# #     * purpose and noninfringement.  In no event shall the authors *
# #     * or copyright holders be liable for any claim, damages or    *
# #     * other liability, whether in an action of contract, tort     *
# #     * or otherwise, arising from, out of or in connection with    *
# #     * the software or the use of other dealings in the software.  *
# #
# #******************************************************************************

# import time

# from pyspec.graphics.QVariant import *
# from pyspec.graphics import qt_variant
# from pyspec.css_logger import log

# (MOTOR, VSCANMOTOR, INT, FLOAT, INTERVAL, HKL, FILE) = (0, 1, 2, 3, 4, 5, 6)

# class ScanPar(QObject):

#     le_width = 50
#     cmb_width = 50
#     hkl_width = 70

#     edited = pyqtSignal()

#     def __init__(self, name, ptype=FLOAT, vnames=None, optional=False, default="1.0", null=False):

#         QObject.__init__(self)
#         self.name = name
#         self.ptype = ptype
#         self.multiple = False
#         self.null = null
#         self.optional = optional

#         self.valuenames = None
#         self.value = None
#         self.values = []

#         self.default = default

#         self.widget = None

#         if vnames and type(vnames) == list:
#             self.valuenames = vnames
#             self.multiple = True
#             self.values = [None, ] * len(self.valuenames)

#     def getWidget(self):
#         if not self.widget:
#             self.buildWidget()
#         return self.widget

#     def isValid(self):
#         # Each par class should implement its own validation algorithm
#         return True

#     def buildWidget(self):
#         self.widget = QWidget()
#         layout = QHBoxLayout()
#         layout.setSpacing(1)
#         layout.setContentsMargins(1, 1, 1, 1)
#         layout.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

#         self.label = QLabel(self.name + ":")
#         self.value = QLineEdit()
#         self.value.setFixedWidth(self.le_width)
#         self.value.setText(str(self.default))
#         self.value.textEdited.connect(self.valueEdited)

#         sspacer = QWidget()
#         sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         layout.addWidget(self.label)
#         layout.addWidget(self.value)
#         layout.addWidget(sspacer)

#         if self.optional:
#             self.value.setStyleSheet("background-color: #c0c0c0")

#         self.widget.setLayout(layout)

#     def resetEdited(self):
#         if self.optional:
#             self.value.setStyleSheet("background-color: #c0c0c0")
#         else:
#             self.value.setStyleSheet("background-color:  white")

#     def setValue(self, value):
#         if self.multiple:
#             log.log(3,
#                 "parameter type %s should implement its own setValue method " % self.getType())
#             return

#         value = value.replace('[','')
#         value = value.replace(']','')
#         self.value.setText(value)
#         self.resetEdited()

#     def valueEdited(self, value):
#         self.value.setStyleSheet("background-color:  #ccccff")
#         self.edited.emit()

#     def getType(self):
#         return self.ptype

#     def getName(self):
#         return self.name

#     def getValueNames(self):
#         return self.valuenames

#     def getValue(self):
#         if self.multiple:
#             log.log(3,
#                 "parameter type %s should implement its own getValue method " % self.getType())
#             return

#         return self.value.text()


# class FloatPar(ScanPar):

#     def getValue(self):
#         value = str(self.value.text())

#         if value == "" and self.null:
#             return value

#         try:
#             return float(self.value.text())
#         except ValueError:
#             return "float"

#     def isValid(self):
#         try:
#             fval = float(self.value.text())
#             return True
#         except ValueError:
#             return False


# class TimePar(ScanPar):

#     def getValue(self):
#         try:
#             return float(self.value.text())
#         except ValueError:
#             return "time"

#     def isValid(self):
#         try:
#             fval = float(self.value.text())
#             return True
#         except ValueError:
#             return False


# class IntPar(ScanPar):

#     def __init__(self, name):
#         ScanPar.__init__(self, name, ptype=INT)
#         self.default = 1

#     def getValue(self):
#         try:
#             return int(self.value.text())
#         except ValueError:
#             return "int"

#     def isValid(self):
#         try:
#             fval = int(self.value.text())
#             return True
#         except ValueError:
#             return False


# class IntervalPar(IntPar):

#     def __init__(self, name):
#         ScanPar.__init__(self, name, ptype=INTERVAL)
#         self.default = "10"

#     def getValue(self):
#         val = self._getValue()
#         if val > 0:
#             return val
#         else:
#             return "int"

#     def isValid(self):
#         val = self._getValue()
#         if val > 0:
#             return True
#         else:
#             return False

#     def _getValue(self):
#         try:
#             return(int(self.value.text()))
#         except:
#             return 0


# class MotorPar(ScanPar):

#     def __init__(self, name, vnames=None):

#         if not vnames:
#             vnames = [name, 'start', 'end']

#         ScanPar.__init__(self, name, ptype=MOTOR, vnames=vnames)
#         self.mne = ""
#         self.start = None
#         self.end = None
#         self.aliases = None

#     def buildWidget(self):
#         self.widget = QWidget()
#         layout = QHBoxLayout()
#         layout.setSpacing(2)
#         layout.setContentsMargins(1, 1, 1, 1)

#         valnames = self.getValueNames()

#         fromlabel = QLabel(valnames[1] + ":")
#         fromlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         tolabel = QLabel(valnames[2] + ":")
#         tolabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

#         self.mnecombo = QComboBox()

#         self.fromval = QLineEdit()
#         self.fromval.setFixedWidth(self.le_width)
#         self.toval = QLineEdit()
#         self.toval.setFixedWidth(self.le_width)

#         self.mnecombo.currentIndexChanged.connect(self.motorChanged)
#         self.fromval.textEdited.connect(self.fromEdited)
#         self.toval.textEdited.connect(self.toEdited)

#         self.fromval.setText(str(self.default))
#         self.toval.setText(str(self.default))
#         self.mnecombo.setCurrentIndex(1)
#         self.mnecombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

#         sspacer = QWidget()
#         sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         layout.addWidget(self.mnecombo)
#         layout.addWidget(fromlabel)
#         layout.addWidget(self.fromval)
#         layout.addWidget(tolabel)
#         layout.addWidget(self.toval)
#         layout.addWidget(sspacer)

#         self.widget.setLayout(layout)

#     def isValid(self):
#         if self.mnecombo.currentIndex() == 0:
#             return False
#         else:
#             return True

#     def resetEdited(self):
#         self.fromval.setStyleSheet("background-color:  white")
#         self.toval.setStyleSheet("background-color:  white")

#     def fromEdited(self, value):
#         self.fromval.setStyleSheet("background-color:  #ccccff")
#         self.edited.emit()

#     def toEdited(self, value):
#         self.toval.setStyleSheet("background-color:  #ccccff")
#         self.edited.emit()

#     def motorChanged(self, value):
#         self.edited.emit()

#     def setMotors(self, motormnes, aliases):
#         self.mnecombo.clear()
#         self.mnecombo.addItems(["---", ] + motormnes)

#         self.motormnes = motormnes
#         self.aliases = aliases

#     def setMotor(self, motor):
#         if motor not in self.motormnes:
#             if motor in self.aliases:
#                 motor = self.aliases[motor]
    
#         if motor in self.motormnes:
#             try:
#                 motidx = self.motormnes.index(motor) + 1
#             except IndexError:
#                 motidx = 0
#             self.mnecombo.setCurrentIndex(motidx)

#     def getValues(self):
#         mne = str(self.mnecombo.currentText())
#         try:
#             fromv = float(self.fromval.text())
#         except:
#             fromv = 0
#         try:
#             tov = float(self.toval.text())
#         except:
#             tov = 0
#         return [mne, fromv, tov]

#     def setValues(self, values):
#         if len(values) != 3:
#             return

#         mne, fromval, toval = values

#         self.setMotor(mne)
#         self.fromval.setText(str(fromval))
#         self.toval.setText(str(toval))


# class VscanMotorPar(MotorPar):
#     def __init__(self, name, vnames=None):

#         if not vnames:
#             vnames = [name, 'start', 'center','finish']

#         ScanPar.__init__(self, name, ptype=VSCANMOTOR, vnames=vnames)
#         self.mne = ""
#         self.start = None
#         self.center = None
#         self.finish = None

#     def buildWidget(self):
#         self.widget = QWidget()
#         layout = QHBoxLayout()
#         layout.setSpacing(2)
#         layout.setContentsMargins(1, 1, 1, 1)

#         valnames = self.getValueNames()

#         startlabel = QLabel(valnames[1] + ":")
#         startlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         centerlabel = QLabel(valnames[2] + ":")
#         centerlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         finishlabel = QLabel(valnames[3] + ":")
#         finishlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

#         self.mnecombo = QComboBox()

#         self.startval = QLineEdit()
#         self.startval.setFixedWidth(self.le_width)
#         self.centerval = QLineEdit()
#         self.centerval.setFixedWidth(self.le_width)
#         self.finishval = QLineEdit()
#         self.finishval.setFixedWidth(self.le_width)

#         self.mnecombo.currentIndexChanged.connect(self.motorChanged)
#         self.startval.textEdited.connect(self.startEdited)
#         self.centerval.textEdited.connect(self.centerEdited)
#         self.finishval.textEdited.connect(self.centerEdited)

#         self.startval.setText(str(self.default))
#         self.centerval.setText(str(self.default))
#         self.finishval.setText(str(self.default))
#         self.mnecombo.setCurrentIndex(1)
#         self.mnecombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

#         sspacer = QWidget()
#         sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         layout.addWidget(self.mnecombo)
#         layout.addWidget(startlabel)
#         layout.addWidget(self.startval)
#         layout.addWidget(centerlabel)
#         layout.addWidget(self.centerval)
#         layout.addWidget(finishlabel)
#         layout.addWidget(self.finishval)
#         layout.addWidget(sspacer)

#         self.widget.setLayout(layout)

#     def resetEdited(self):
#         self.startval.setStyleSheet("background-color:  white")
#         self.centerval.setStyleSheet("background-color:  white")
#         self.finishval.setStyleSheet("background-color:  white")

#     def startEdited(self, value):
#         self.startval.setStyleSheet("background-color:  #ccccff")
#         self.edited.emit()

#     def centerEdited(self, value):
#         self.centerval.setStyleSheet("background-color:  #ccccff")
#         self.edited.emit()

#     def finishEdited(self, value):
#         self.finishval.setStyleSheet("background-color:  #ccccff")
#         self.edited.emit()

#     def getValues(self):
#         mne = str(self.mnecombo.currentText())
#         try:
#             startv = float(self.startval.text())
#         except:
#             startv = 0

#         try:
#             centerv = float(self.centerval.text())
#         except:
#             centerv = 0

#         try:
#             finishv = float(self.finishval.text())
#         except:
#             finishv = 0

#         return [mne, startv, centerv, finishv]

#     def setValues(self, values):
#         if len(values) != 4:
#             return

#         mne, startval, centerval, finishval = values

#         self.setMotor(mne)

#         self.startval.setText(str(startval))
#         self.centerval.setText(str(centerval))
#         self.finishval.setText(str(finishval))


# class FilePar(ScanPar):
#     def __init__(self, name, vnames=None):
#         ScanPar.__init__(self, name, ptype=FILE)
#         self.filename = ""

#     def buildWidget(self):
#         self.widget = QWidget()
#         layout = QHBoxLayout()
#         layout.setSpacing(2)
#         layout.setContentsMargins(1, 1, 1, 1)

#         self.filename_le = QLineEdit()
#         self.browser_bt = QPushButton("...")
#         self.browser_bt.clicked.connect(self.chooseFile)

#         layout.addWidget(self.filename_le)
#         layout.addWidget(self.browser_bt)
#         self.widget.setLayout(layout)

#     def chooseFile(self):
#         filename = QFileDialog.getOpenFileName(self.widget, "Select File", self.getFileName())

#         if qt_variant() != "PyQt4":
#             # in PySide getOpenFileNamNamee returns a tuple. PyQt5??
#             filename = str(filename[0])
#         else:
#             filename = str(filename)


#         if str(filename) != "":
#             self.filename_le.setText(filename)
#             self.filename = filename

#     def getValue(self):
#         return self.getFileName()

#     def setValue(self,value):
#         self.setFileName(value)

#     def getFileName(self):
#         return str(self.filename_le.text())

#     def setFileName(self,filename):
#         self.filename_le.setText(filename)

# class HKLPar(ScanPar):

#     def __init__(self, name, vnames=None):
#         ScanPar.__init__(self, name, ptype=HKL, vnames=['start', 'end'])

#     def buildWidget(self):
#         self.widget = QWidget()
#         layout = QHBoxLayout()
#         layout.setSpacing(2)
#         layout.setContentsMargins(1, 1, 1, 1)

#         valnames = self.getValueNames()

#         fromlabel = QLabel(valnames[0] + ":")
#         fromlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         tolabel = QLabel(valnames[1] + ":")
#         tolabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

#         self.clabel = QLabel(self.name)
#         self.fromval = QLineEdit()
#         self.fromval.setFixedWidth(self.hkl_width)
#         self.fromval.setText(str(self.default))

#         self.toval = QLineEdit()
#         self.toval.setFixedWidth(self.hkl_width)
#         self.toval.setText(str(self.default))

#         self.fromval.textEdited.connect(self.fromEdited)
#         self.toval.textEdited.connect(self.toEdited)

#         sspacer = QWidget()
#         sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         layout.addWidget(self.clabel)
#         layout.addWidget(fromlabel)
#         layout.addWidget(self.fromval)
#         layout.addWidget(tolabel)
#         layout.addWidget(self.toval)
#         layout.addWidget(sspacer)

#         self.widget.setLayout(layout)

#     def resetEdited(self):
#         self.fromval.setStyleSheet("background-color:  white")
#         self.toval.setStyleSheet("background-color:  white")

#     def fromEdited(self, value):
#         self.fromval.setStyleSheet("background-color:  #ccccff")
#         # self.emit(Qt.SIGNAL("edited"))
#         self.edited.emit()

#     def toEdited(self, value):
#         self.toval.setStyleSheet("background-color:  #ccccff")
#         # self.emit(Qt.SIGNAL("edited"))
#         self.edited.emit()

#     def getValues(self):
#         try:
#             fromv = float(self.fromval.text())
#         except:
#             fromv = 0

#         try:
#             tov = float(self.toval.text())
#         except:
#             tov = 0

#         return [fromv, tov]

#     def setValues(self, values):
#         if len(values) != 2:
#             return

#         fromval, toval = values

#         self.fromval.setText(str(fromval))
#         self.toval.setText(str(toval))


# scanList = [
#     'ascan', 'a2scan', 'a3scan', 'a4scan', 'a5scan',
#     'dscan', 'd2scan', 'd3scan', 'd4scan',
#     'cscan', 'c2scan', 'c3scan', 'c4scan',
#     'vscan', 'v2scan', 'fscan',
#     'mesh', 'cmesh', 
#     'timescan', 'loopscan',
# ]

# hklList = [
#     'hscan', 'kscan', 'lscan', 'hklscan', 'aziscan',
# ]


# class _ScanW(QWidget):

#     edited = pyqtSignal()

#     def __init__(self, name, pars=None):

#         self.name = name
#         self.motormnes = []
#         self.aliases = []

#         if pars is None:
#             self.pars = []
#         else:
#             self.pars = pars

#         QWidget.__init__(self)

#         wlyt = QVBoxLayout()
#         wlyt.setContentsMargins(0, 0, 0, 0)
#         self.setLayout(wlyt)

#         parno = 0
#         self.wids = []
#         self.total_points = 0

#         for par in self.pars:
#             wid = par.getWidget()
#             self.wids.append(wid)
#             wlyt.addWidget(wid)
#             par.edited.connect(self._edited)
#             parno += 1

#     def resetEdited(self):
#         for par in self.pars:
#             par.resetEdited()

#     def _edited(self):
#         # self.emit(Qt.SIGNAL("edited"))
#         self.edited.emit()

#     def setMotors(self, motormnes, aliases):
#         parno = 0
#         for par in self.pars:
#             if par.getType() in [MOTOR, VSCANMOTOR]:
#                 par.setMotors(motormnes,aliases)
#             parno += 1
#         self.motormnes = motormnes
#         self.aliases = aliases

#     def setValues(self, values):
#         cursor = 0
#         intervals = 1
        
#         for par in self.pars:
#             if par.getType() == VSCANMOTOR:
#                 par.setValues(values[cursor:cursor + 4])
#                 cursor += 5
#             elif par.getType() == MOTOR:
#                 par.setValues(values[cursor:cursor + 3])
#                 cursor += 3
#             elif par.getType() == HKL:
#                 par.setValues(values[cursor:cursor + 2])
#                 cursor += 2
#             elif par.getType() == INTERVAL:
#                 ival_value = int(values[cursor])
#                 intervals *= ival_value
#                 par.setValue(values[cursor])
#                 cursor += 1
#             else:
#                 par.setValue(values[cursor])
#                 cursor += 1

#         if intervals > 1:
#             self.total_points = intervals + 1
#         else:
#             self.total_points = 0

#         print("Total scan points are: %s" % (total_points))

#     def getValues(self):
#         retvals = []
#         parno = 0

#         for par in self.pars:
#             if par.getType() in [MOTOR, VSCANMOTOR,HKL]:
#                 vals = par.getValues()
#                 retvals.extend(vals)
#             else:
#                 value = par.getValue()
#                 retvals.extend([value, ])
#                 parno += 1

#         valid = True
#         for par in self.pars:
#             if not par.isValid():
#                 valid = False
#                 break

#         return valid, retvals

#     def getCountTime(self):
#         for par in self.pars:
#             if par.getName() == "count-time":
#                 return par.getValue()
#         else:
#             return None

#     def getNumberPoints(self):
#         return self.total_points

#     def setBusy(self, flag):
#         if flag:
#             self.busy = True
#         else:
#             self.busy = False

# class ScanWidget(QWidget):

#     def __init__(self, *args):
#         self.cmdstr = None
#         self.widgets = {}
#         self.cmd = None
#         self.motormnes = None
#         self.aliases = None

#         self.scanStartTime = 0
#         self.elapsed = -1
#         self.total_points = 0

#         self.datasource_ref = None
#         self.hklChecked = False

#         self.currentScanW = None

#         QWidget.__init__(self, *args)
#         self.initWidget()

#     def initWidget(self):
#         # Scan group
#         self.createPars()

#         self.scanLayout = QVBoxLayout()

#         self.scanLayout.setSpacing(1)
#         self.scanLayout.setContentsMargins(1, 1, 1, 1)

#         self.commandLayout = QHBoxLayout()
#         self.commandLayout.setContentsMargins(1, 1, 1, 1)
#         self.commandLayout.setSpacing(3)

#         self.bottomLayout = QHBoxLayout()
#         self.bottomLayout.setSpacing(3)
#         self.bottomLayout.setContentsMargins(1, 1, 1, 1)

#         self.commandLabel = QLabel("Command:")
#         self.commandCombo = QComboBox()
#         self.commandCombo.addItems(scanList)
#         self.scanList = scanList
        
#         self.commandCombo.currentIndexChanged.connect(self.setCommandNumber)

#         font = self.commandLabel.font()
#         font.setBold(True)
#         self.commandLabel.setFont(font)

#         self.scanCommand = QLabel()
#         self.scanCommand.setStyleSheet("background-color: #ececdd")
#         self.scanCommand.setTextInteractionFlags(Qt.TextSelectableByMouse)

#         sspacer = QWidget()
#         sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         sspacer2 = QWidget()
#         sspacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         self.goButton = QPushButton('Go')
#         self.goButton.setFixedWidth(50)
#         self.goButton.clicked.connect(self.go)

#         self.progressBar = QProgressBar()
#         self.estimatedEnd = QLabel()
#         try:
#             self.estimatedEnd.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
#         except AttributeError:
#             self.estimatedEnd.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

#         self.commandLayout.addWidget(self.commandLabel)
#         self.commandLayout.addWidget(self.commandCombo)
#         self.commandLayout.addWidget(sspacer)

#         self.bottomLayout.addWidget(self.scanCommand)
#         self.bottomLayout.addWidget(self.goButton)
#         self.bottomLayout.addWidget(sspacer2)

#         self.scanLayout.addLayout(self.commandLayout)
#         self.scanLayout.addLayout(self.bottomLayout)
#         self.scanLayout.addWidget(self.progressBar)
#         self.scanLayout.addWidget(self.estimatedEnd)
#         self.setLayout(self.scanLayout)

#     def createPars(self):
#         self.scanPars = {
#             'ascan':    [_ScanW, [MotorPar('mot1'), IntervalPar('intervals'), TimePar('count-time')]],
#             'a2scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), IntervalPar('intervals'), TimePar('count-time')]],
#             'a3scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'),
#                                   IntervalPar('intervals'), TimePar('count-time')]],
#             'a4scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
#                                   IntervalPar('intervals'), TimePar('count-time')]],
#             'a5scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
#                                   MotorPar('mot5'), IntervalPar('intervals'), TimePar('count-time')]],
#             'vscan':    [_ScanW, [VscanMotorPar('mot1'), IntervalPar('intervals'), TimePar('count-time'), 
#                                   FloatPar('minstep', null=True, default="", optional=True), 
#                                   FloatPar('exponent',null=True, default="", optional=True)]],
#             'v2scan':   [_ScanW, [VscanMotorPar('mot1'),  VscanMotorPar('mot2'), 
#                                   IntervalPar('intervals'), TimePar('count-time'), 
#                                   FloatPar('minstep', null=True, default="", optional=True), 
#                                   FloatPar('exponent',null=True, default="", optional=True)]],
#             'fscan':    [_ScanW, [FilePar('filename'), FloatPar('count-time', default="", null=True, optional=True)]],
#             'mesh':     [_ScanW, [MotorPar('mot1'), IntervalPar('intervals1'), MotorPar('mot2'),
#                                   IntervalPar('intervals2'), TimePar('count-time')]],
#             'cscan':    [_ScanW, [MotorPar('mot1'),  TimePar('scantime'), TimePar('sleeptime', default=0, optional=True)]],
#             'c2scan':   [_ScanW, [MotorPar('mot1'),  MotorPar('mot2'), TimePar('scantime'), TimePar('sleeptime', default=0, optional=True)]],
#             'c3scan':   [_ScanW, [MotorPar('mot1'),  MotorPar('mot2'), MotorPar('mot3'),
#                                   TimePar('scantime'), TimePar('sleeptime', default=0, optional=True)]],
#             'c4scan':   [_ScanW, [MotorPar('mot1'),  MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
#                                   TimePar('scantime'), TimePar('sleeptime', default=0, optional=True)]],
#             'cmesh':   [_ScanW, [MotorPar('mot1'),  TimePar('scantime'), MotorPar('mot2'), 
#                                   IntervalPar('intervals'), TimePar('sleeptime', default=0, optional=True)]],

#             'dscan':    [_ScanW, [MotorPar('mot1', vnames=["mot1", "relat.start", "relat.end"]), 
#                                  IntervalPar('intervals'), TimePar('count-time')]],
#             'd2scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), 
#                                   IntervalPar('intervals'), TimePar('count-time')]],
#             'd3scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
#                                   IntervalPar('intervals'), TimePar('count-time')]],
#             'd4scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
#                                   IntervalPar('intervals'), TimePar('count-time')]],
#             'timescan': [_ScanW, [TimePar('count-time', optional=True), 
#                                   TimePar('sleep-time', default="", null=True, optional=True)]],
#             'loopscan': [_ScanW, [IntervalPar('nb-points'), TimePar('count-time', optional=True), 
#                                   TimePar('sleep-time', default="", null=True, optional=True)]],
#             'tscan':    [_ScanW, [FloatPar('start'), FloatPar('finish'), 
#                                   IntervalPar('intervals'), TimePar('time'), 
#                                   TimePar('sleep', default="", null=True, optional=True)]],
#             'hscan':    [_ScanW, [HKLPar('H'), IntervalPar('intervals'), TimePar('count-time')]],
#             'kscan':    [_ScanW, [HKLPar('K'), IntervalPar('intervals'), TimePar('count-time')]],
#             'lscan':    [_ScanW, [HKLPar('L'), IntervalPar('intervals'), TimePar('count-time')]],
#             'hklscan':  [_ScanW, [HKLPar('H'), HKLPar('K'), HKLPar('L'), 
#                                   IntervalPar('intervals'), TimePar('count-time')]],
#             'aziscan':  [_ScanW, [HKLPar('azi'), IntervalPar('intervals'), TimePar('count-time')]],
#             'Escan':    [_ScanW, [MotorPar('mot1'), IntervalPar('intervals'), 
#                                   TimePar('count-time')]],

#         }

#     def setCommandNumber(self, cmdno):
#         cmd = self.scanList[cmdno]
#         self.setCommandWidget(cmd)

#     def setCommandWidget(self, cmd):

#         cmd = str(cmd)

#         if self.cmd == cmd:
#             return

#         self.checkHKL()

#         if self.currentScanW:
#             self.scanLayout.removeWidget(self.currentScanW)
#             self.currentScanW.hide()

#         self.currentScanW = self.getWidget(cmd)
#         self.currentScanW.show()
#         self.scanLayout.insertWidget(1, self.currentScanW)
#         self.cmd = cmd

#         if self.motormnes and self.currentScanW:
#             self.currentScanW.setMotors(self.motormnes,self.aliases)

#         try:
#             cmdidx = self.scanList.index(cmd)
#             self.commandCombo.setCurrentIndex(cmdidx)
#         except IndexError:
#             pass
#         except ValueError:
#             pass

#         self.updateCommand()

#     def setDataSource(self, datasource):
#         self.datasource_ref = datasource

#     def newScan(self, cmdstr):
#         self.setCommand(cmdstr)

#         self.scanStartTime = time.time()
#         self.elapsed = 0
#         self.estTotalTime = 0
#         self.total_points = self.currentScanW.getNumberPoints()

#         if self.total_points:
#             self.progressBar.setRange(0, self.total_points - 1)
#             self.progressBar.setValue(self.total_points - 1)
#         else:
#             self.progressBar.setRange(0, 1)
#             self.progressBar.setValue(1)

#         self.estimatedEnd.setStyleSheet("background-color: #ccccff")

#     def setCommand(self, cmdstr):

#         self.cmdstr = cmdstr
#         self.cmdparts = self.cmdstr.split()
#         if not len(self.cmdparts):
#             return
#         cmd = self.cmdparts[0]

#         self.scanCommand.setText(self.cmdstr)
#         self.checkHKL()

#         self.setCommandWidget(cmd)

#         try:
#             self.currentScanW.setValues(self.cmdparts[1:])
#         except:
#             pass

#         self.updateCommand()

#     def getWidget(self, cmd):
#         if cmd not in self.widgets:
#             self.createWidget(cmd)
#             #Qt.QObject.connect( self.widgets[cmd], Qt.SIGNAL("edited"), self.updateCommand )
#             self.widgets[cmd].edited.connect(self.updateCommand)
#         return self.widgets[cmd]

#     def getCommand(self):
#         return self.cmdstr

#     def checkHKL(self):
#         # Add HKL commands if necessary
#         if (not self.hklChecked) and self.datasource_ref:
#             hasHKL = self.datasource_ref().hasHKL()

#             if hasHKL > -1:
#                 if hasHKL > 0:
#                     self.commandCombo.addItems(hklList)
#                     self.scanList.extend(hklList)
#                 self.hklChecked = True

#     def updateCommand(self):

#         # Read values and prepare command string
#         valid, gopars = self.currentScanW.getValues()
#         cmd = self.cmd + " " + " ".join([str(par) for par in gopars])
#         self.scanCommand.setText(cmd)
#         self.estimatedEnd.setText("")

#         if not valid:
#             self.goButton.setDisabled(True)
#         else:
#             self.goButton.setDisabled(False)

#     def setMotors(self, motormnes, aliases):
#         self.motormnes = motormnes
#         self.aliases = aliases

#         if self.currentScanW:
#             self.currentScanW.setMotors(self.motormnes, self.aliases)
#             if self.cmdstr:
#                 self.setCommand(self.cmdstr)

#     def createWidget(self, scantype):
#         if scantype not in self.scanPars:
#             log.log(3,"scantype of name %s not recognized", scantype)
#             self.widgets[scantype] = _ScanW("No scan")
#             return
#         scanclass, scanpars = self.scanPars[scantype]
#         self.widgets[scantype] = scanclass(scantype, scanpars)

#     def setMotorInterval(self, motor, begin, end):
#         ct_time = self.currentScanW.getCountTime() 
#         if ct_time is None:
#             ct_time = 1
#         self.setCommand("ascan %s %3.3s %3.3s %s" % (motor,begin,end, ct_time))

#     def newPoint(self, ptno):

#         if not self.currentScanW:
#             return

#         # show progress bar here
#         self.elapsed = time.time() - self.scanStartTime

#         if ptno == 0:
#             return

#         # The first point arrives with timestamp 0 (newscan = first point)
#         #  this stops us from properly calculating total scan time

#         if self.scanStartTime:
#             if self.total_points:
#                 self.progressBar.setValue(ptno)
#                 self.estTotalTime = (self.total_points - 1) * \
#                     self.elapsed / (ptno)
#                 eTotalEnd = self.scanStartTime + self.estTotalTime
#                 ltime = time.localtime(eTotalEnd)
#                 remain = "%4.2g" % (self.estTotalTime - self.elapsed)
#                 eta = "%d:%02d" % (ltime.tm_hour, ltime.tm_min)
#                 stime = "time left: % 8s sec / Est.finish: %s" % (remain, eta)
#             else:
#                 elapsed = "%4.2g" % (self.elapsed)
#                 stime = "time elapsed: % 8s sec " % elapsed
#             self.estimatedEnd.setText(stime)
#             self.progressBar.setTextVisible(True)

#     def setBusy(self, flag):
#         if self.currentScanW:
#             self.currentScanW.setBusy(flag)

#         if not flag:
#             # state is idle
#             self.scanOn = False
#             self.estimatedEnd.setStyleSheet("background-color: #e0e0bb")

#             # if self.elapsed > 0:
#             #self.estimatedEnd.setText( "Elapsed time: %0.2g sec" % self.elapsed )

#             remain = "0"
#             stime = "time left: % 8s sec " % (remain)
#             self.estimatedEnd.setText(stime)

#             self.progressBar.setRange(0, 100)
#             self.progressBar.setValue(100)
#             self.progressBar.setTextVisible(False)
#         else:
#             # to be actually busy. it has to have received at least one point
#             # since last time idle
#             if self.scanOn:
#                 self.estimatedEnd.setStyleSheet("background-color: #c0c0aa")

#     def go(self):
#         try:
#             # should validate values here
#             valid, gopars = self.currentScanW.getValues()
#             cmd = self.cmd + " " + " ".join([str(par) for par in gopars])

#             if self.datasource_ref:
#                 self.datasource_ref().sendCommandA(cmd)

#             self.currentScanW.resetEdited()
#         except:
#             log.log(3,"Cannot decode parameters. Check boxes")


# def test():
#     import sys
#     app = QApplication([])
#     win = QMainWindow()
#     scan = ScanWidget()
#     scan.setMotors(['th', 'chi', 'tth', 'phi'], ['Theta','Chi','Two Theta','Phi'])
#     scan.setCommand("ascan th 3 10 20 0.1")
#     scan.setCommand("a2scan chi 3 10 tth 5 5.5 10 0.1")
#     scan.setCommand("fscan toto")
#     scan.setCommand("mesh th 3 7 20 chi 5 10 3 0.1")
#     #scan.setCommand("timescan 0.1 0.3")

#     win.setCentralWidget(scan)
#     win.show()

#     sys.exit(app.exec_())


# if __name__ == '__main__':
#     test()


#******************************************************************************
#
#  @(#)ScanWidget.py	3.8  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2020,2023,2024
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

import time

from pyspec.graphics.QVariant import *
from pyspec.graphics import qt_variant
from pyspec.css_logger import log
from PySide6.QtWidgets import QFormLayout

(MOTOR, VSCANMOTOR, INT, FLOAT, INTERVAL, HKL, FILE) = (0, 1, 2, 3, 4, 5, 6)

class ScanPar(QObject):

    le_width = 50
    cmb_width = 50
    hkl_width = 70

    edited = pyqtSignal()

    def __init__(self, name, ptype=FLOAT, vnames=None, optional=False, default="1.0", null=False):

        QObject.__init__(self)
        self.name = name
        self.ptype = ptype
        self.multiple = False
        self.null = null
        self.optional = optional

        self.valuenames = None
        self.value = None
        self.values = []

        self.default = default

        self.widget = None

        if vnames and type(vnames) == list:
            self.valuenames = vnames
            self.multiple = True
            self.values = [None, ] * len(self.valuenames)

    def getWidget(self):
        if not self.widget:
            self.buildWidget()
        return self.widget

    def isValid(self):
        # Each par class should implement its own validation algorithm
        return True

    def buildWidget(self):
        self.widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

        self.label = QLabel(self.name + ":")
        self.value = QLineEdit()
        self.value.setFixedWidth(self.le_width)
        self.value.setText(str(self.default))
        self.value.textEdited.connect(self.valueEdited)

        sspacer = QWidget()
        sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.label)
        layout.addWidget(self.value)
        layout.addWidget(sspacer)

        if self.optional:
            self.value.setStyleSheet("background-color: #c0c0c0")

        self.widget.setLayout(layout)

    def resetEdited(self):
        if self.optional:
            self.value.setStyleSheet("background-color: #c0c0c0")
        else:
            self.value.setStyleSheet("background-color:  white")

    def setValue(self, value):
        if self.multiple:
            log.log(3,
                "parameter type %s should implement its own setValue method " % self.getType())
            return

        value = value.replace('[','')
        value = value.replace(']','')
        self.value.setText(value)
        self.resetEdited()

    def valueEdited(self, value):
        self.value.setStyleSheet("background-color:  #ccccff")
        self.edited.emit()

    def getType(self):
        return self.ptype

    def getName(self):
        return self.name

    def getValueNames(self):
        return self.valuenames

    def getValue(self):
        if self.multiple:
            log.log(3,
                "parameter type %s should implement its own getValue method " % self.getType())
            return

        return self.value.text()


class FloatPar(ScanPar):

    def getValue(self):
        value = str(self.value.text())

        if value == "" and self.null:
            return value

        try:
            return float(self.value.text())
        except ValueError:
            return "float"

    def isValid(self):
        try:
            fval = float(self.value.text())
            return True
        except ValueError:
            return False


class TimePar(ScanPar):

    def getValue(self):
        try:
            return float(self.value.text())
        except ValueError:
            return "time"

    def isValid(self):
        try:
            fval = float(self.value.text())
            return True
        except ValueError:
            return False


class IntPar(ScanPar):

    def __init__(self, name):
        ScanPar.__init__(self, name, ptype=INT)
        self.default = 1

    def getValue(self):
        try:
            return int(self.value.text())
        except ValueError:
            return "int"

    def isValid(self):
        try:
            fval = int(self.value.text())
            return True
        except ValueError:
            return False


class IntervalPar(IntPar):

    def __init__(self, name):
        ScanPar.__init__(self, name, ptype=INTERVAL)
        self.default = "10"

    def getValue(self):
        val = self._getValue()
        if val > 0:
            return val
        else:
            return "int"

    def isValid(self):
        val = self._getValue()
        if val > 0:
            return True
        else:
            return False

    def _getValue(self):
        try:
            return(int(self.value.text()))
        except:
            return 0


class MotorPar(ScanPar):

    def __init__(self, name, vnames=None):

        if not vnames:
            vnames = [name, 'start', 'end']

        ScanPar.__init__(self, name, ptype=MOTOR, vnames=vnames)
        self.mne = ""
        self.start = None
        self.end = None
        self.aliases = None

    def buildWidget(self):
        self.widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(1, 1, 1, 1)

        valnames = self.getValueNames()

        fromlabel = QLabel(valnames[1] + ":")
        fromlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tolabel = QLabel(valnames[2] + ":")
        tolabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.mnecombo = QComboBox()

        self.fromval = QLineEdit()
        self.fromval.setFixedWidth(self.le_width)
        self.toval = QLineEdit()
        self.toval.setFixedWidth(self.le_width)

        self.mnecombo.currentIndexChanged.connect(self.motorChanged)
        self.fromval.textEdited.connect(self.fromEdited)
        self.toval.textEdited.connect(self.toEdited)

        self.fromval.setText(str(self.default))
        self.toval.setText(str(self.default))
        self.mnecombo.setCurrentIndex(1)
        self.mnecombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        sspacer = QWidget()
        sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.mnecombo)
        layout.addWidget(fromlabel)
        layout.addWidget(self.fromval)
        layout.addWidget(tolabel)
        layout.addWidget(self.toval)
        layout.addWidget(sspacer)

        self.widget.setLayout(layout)

    def isValid(self):
        if self.mnecombo.currentIndex() == 0:
            return False
        else:
            return True

    def resetEdited(self):
        self.fromval.setStyleSheet("background-color:  white")
        self.toval.setStyleSheet("background-color:  white")

    def fromEdited(self, value):
        self.fromval.setStyleSheet("background-color:  #ccccff")
        self.edited.emit()

    def toEdited(self, value):
        self.toval.setStyleSheet("background-color:  #ccccff")
        self.edited.emit()

    def motorChanged(self, value):
        self.edited.emit()

    def setMotors(self, motormnes, aliases):
        self.mnecombo.clear()
        self.mnecombo.addItems(["---", ] + motormnes)

        self.motormnes = motormnes
        self.aliases = aliases

    def setMotor(self, motor):
        if motor not in self.motormnes:
            if motor in self.aliases:
                motor = self.aliases[motor]
    
        if motor in self.motormnes:
            try:
                motidx = self.motormnes.index(motor) + 1
            except IndexError:
                motidx = 0
            self.mnecombo.setCurrentIndex(motidx)

    def getValues(self):
        mne = str(self.mnecombo.currentText())
        try:
            fromv = float(self.fromval.text())
        except:
            fromv = 0
        try:
            tov = float(self.toval.text())
        except:
            tov = 0
        return [mne, fromv, tov]

    def setValues(self, values):
        if len(values) != 3:
            return

        mne, fromval, toval = values

        self.setMotor(mne)
        self.fromval.setText(str(fromval))
        self.toval.setText(str(toval))


class VscanMotorPar(MotorPar):
    def __init__(self, name, vnames=None):

        if not vnames:
            vnames = [name, 'start', 'center','finish']

        ScanPar.__init__(self, name, ptype=VSCANMOTOR, vnames=vnames)
        self.mne = ""
        self.start = None
        self.center = None
        self.finish = None

    def buildWidget(self):
        self.widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(1, 1, 1, 1)

        valnames = self.getValueNames()

        startlabel = QLabel(valnames[1] + ":")
        startlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        centerlabel = QLabel(valnames[2] + ":")
        centerlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        finishlabel = QLabel(valnames[3] + ":")
        finishlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.mnecombo = QComboBox()

        self.startval = QLineEdit()
        self.startval.setFixedWidth(self.le_width)
        self.centerval = QLineEdit()
        self.centerval.setFixedWidth(self.le_width)
        self.finishval = QLineEdit()
        self.finishval.setFixedWidth(self.le_width)

        self.mnecombo.currentIndexChanged.connect(self.motorChanged)
        self.startval.textEdited.connect(self.startEdited)
        self.centerval.textEdited.connect(self.centerEdited)
        self.finishval.textEdited.connect(self.centerEdited)

        self.startval.setText(str(self.default))
        self.centerval.setText(str(self.default))
        self.finishval.setText(str(self.default))
        self.mnecombo.setCurrentIndex(1)
        self.mnecombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        sspacer = QWidget()
        sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.mnecombo)
        layout.addWidget(startlabel)
        layout.addWidget(self.startval)
        layout.addWidget(centerlabel)
        layout.addWidget(self.centerval)
        layout.addWidget(finishlabel)
        layout.addWidget(self.finishval)
        layout.addWidget(sspacer)

        self.widget.setLayout(layout)

    def resetEdited(self):
        self.startval.setStyleSheet("background-color:  white")
        self.centerval.setStyleSheet("background-color:  white")
        self.finishval.setStyleSheet("background-color:  white")

    def startEdited(self, value):
        self.startval.setStyleSheet("background-color:  #ccccff")
        self.edited.emit()

    def centerEdited(self, value):
        self.centerval.setStyleSheet("background-color:  #ccccff")
        self.edited.emit()

    def finishEdited(self, value):
        self.finishval.setStyleSheet("background-color:  #ccccff")
        self.edited.emit()

    def getValues(self):
        mne = str(self.mnecombo.currentText())
        try:
            startv = float(self.startval.text())
        except:
            startv = 0

        try:
            centerv = float(self.centerval.text())
        except:
            centerv = 0

        try:
            finishv = float(self.finishval.text())
        except:
            finishv = 0

        return [mne, startv, centerv, finishv]

    def setValues(self, values):
        if len(values) != 4:
            return

        mne, startval, centerval, finishval = values

        self.setMotor(mne)

        self.startval.setText(str(startval))
        self.centerval.setText(str(centerval))
        self.finishval.setText(str(finishval))


class FilePar(ScanPar):
    def __init__(self, name, vnames=None):
        ScanPar.__init__(self, name, ptype=FILE)
        self.filename = ""

    def buildWidget(self):
        self.widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(1, 1, 1, 1)

        self.filename_le = QLineEdit()
        self.browser_bt = QPushButton("...")
        self.browser_bt.clicked.connect(self.chooseFile)

        layout.addWidget(self.filename_le)
        layout.addWidget(self.browser_bt)
        self.widget.setLayout(layout)

    def chooseFile(self):
        filename = QFileDialog.getOpenFileName(self.widget, "Select File", self.getFileName())

        if qt_variant() != "PyQt4":
            # in PySide getOpenFileNamNamee returns a tuple. PyQt5??
            filename = str(filename[0])
        else:
            filename = str(filename)


        if str(filename) != "":
            self.filename_le.setText(filename)
            self.filename = filename

    def getValue(self):
        return self.getFileName()

    def setValue(self,value):
        self.setFileName(value)

    def getFileName(self):
        return str(self.filename_le.text())

    def setFileName(self,filename):
        self.filename_le.setText(filename)

class HKLPar(ScanPar):

    def __init__(self, name, vnames=None):
        ScanPar.__init__(self, name, ptype=HKL, vnames=['start', 'end'])

    def buildWidget(self):
        self.widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(1, 1, 1, 1)

        valnames = self.getValueNames()

        fromlabel = QLabel(valnames[0] + ":")
        fromlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tolabel = QLabel(valnames[1] + ":")
        tolabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.clabel = QLabel(self.name)
        self.fromval = QLineEdit()
        self.fromval.setFixedWidth(self.hkl_width)
        self.fromval.setText(str(self.default))

        self.toval = QLineEdit()
        self.toval.setFixedWidth(self.hkl_width)
        self.toval.setText(str(self.default))

        self.fromval.textEdited.connect(self.fromEdited)
        self.toval.textEdited.connect(self.toEdited)

        sspacer = QWidget()
        sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.clabel)
        layout.addWidget(fromlabel)
        layout.addWidget(self.fromval)
        layout.addWidget(tolabel)
        layout.addWidget(self.toval)
        layout.addWidget(sspacer)

        self.widget.setLayout(layout)

    def resetEdited(self):
        self.fromval.setStyleSheet("background-color:  white")
        self.toval.setStyleSheet("background-color:  white")

    def fromEdited(self, value):
        self.fromval.setStyleSheet("background-color:  #ccccff")
        # self.emit(Qt.SIGNAL("edited"))
        self.edited.emit()

    def toEdited(self, value):
        self.toval.setStyleSheet("background-color:  #ccccff")
        # self.emit(Qt.SIGNAL("edited"))
        self.edited.emit()

    def getValues(self):
        try:
            fromv = float(self.fromval.text())
        except:
            fromv = 0

        try:
            tov = float(self.toval.text())
        except:
            tov = 0

        return [fromv, tov]

    def setValues(self, values):
        if len(values) != 2:
            return

        fromval, toval = values

        self.fromval.setText(str(fromval))
        self.toval.setText(str(toval))


scanList = [
    'ascan', 'a2scan', 'a3scan', 'a4scan', 'a5scan',
    'dscan', 'd2scan', 'd3scan', 'd4scan',
    'cscan', 'c2scan', 'c3scan', 'c4scan',
    'vscan', 'v2scan', 'fscan',
    'mesh', 'cmesh', 
    'timescan', 'loopscan',
]

hklList = [
    'hscan', 'kscan', 'lscan', 'hklscan', 'aziscan',
]


class _ScanW(QWidget):

    edited = pyqtSignal()

    def __init__(self, name, pars=None):

        self.name = name
        self.motormnes = []
        self.aliases = []

        if pars is None:
            self.pars = []
        else:
            self.pars = pars

        QWidget.__init__(self)

        wlyt = QVBoxLayout()
        wlyt.setContentsMargins(0, 0, 0, 0)
        self.setLayout(wlyt)

        parno = 0
        self.wids = []
        self.total_points = 0

        for par in self.pars:
            wid = par.getWidget()
            self.wids.append(wid)
            wlyt.addWidget(wid)
            par.edited.connect(self._edited)
            parno += 1

    def resetEdited(self):
        for par in self.pars:
            par.resetEdited()

    def _edited(self):
        # self.emit(Qt.SIGNAL("edited"))
        self.edited.emit()

    def setMotors(self, motormnes, aliases):
        parno = 0
        for par in self.pars:
            if par.getType() in [MOTOR, VSCANMOTOR]:
                par.setMotors(motormnes,aliases)
            parno += 1
        self.motormnes = motormnes
        self.aliases = aliases

    def setValues(self, values):
        cursor = 0
        intervals = 1
        
        for par in self.pars:
            if par.getType() == VSCANMOTOR:
                par.setValues(values[cursor:cursor + 4])
                cursor += 4   # was 5
            elif par.getType() == MOTOR:
                par.setValues(values[cursor:cursor + 3])
                cursor += 3
            elif par.getType() == HKL:
                par.setValues(values[cursor:cursor + 2])
                cursor += 2
            elif par.getType() == INTERVAL:
                ival_value = int(values[cursor])
                intervals *= ival_value
                par.setValue(values[cursor])
                cursor += 1
            else:
                par.setValue(values[cursor])
                cursor += 1

        if intervals > 1:
            self.total_points = intervals + 1
        else:
            self.total_points = 0

        print("Total scan points are: %s" % (self.total_points))  # was total_points


    def getValues(self):
        retvals = []
        parno = 0

        for par in self.pars:
            if par.getType() in [MOTOR, VSCANMOTOR,HKL]:
                vals = par.getValues()
                retvals.extend(vals)
            else:
                value = par.getValue()
                retvals.extend([value, ])
                parno += 1

        valid = True
        for par in self.pars:
            if not par.isValid():
                valid = False
                break

        return valid, retvals

    def getCountTime(self):
        for par in self.pars:
            if par.getName() == "count-time":
                return par.getValue()
        else:
            return None

    def getNumberPoints(self):
        return self.total_points

    def setBusy(self, flag):
        if flag:
            self.busy = True
        else:
            self.busy = False
from PySide6.QtCore import QTimer

class ScanWidget(QWidget):

    def __init__(self, *args):
        QWidget.__init__(self, *args)
        self.cmdstr = None
        self.widgets = {}
        self.cmd = None
        self.motormnes = None
        self.aliases = None

        self.scanStartTime = 0
        self.elapsed = -1
        self.total_points = 0

        self.datasource_ref = None
        self.hklChecked = False

        self.currentScanW = None
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer_tick)
        self.is_running = False
        self.current_point = 0
        self.initWidget()

    def initWidget(self):
        self.createPars()

        self.scanLayout = QVBoxLayout()
        self.scanLayout.setSpacing(1)
        self.scanLayout.setContentsMargins(1, 1, 1, 1)

        # === Command selection row ===
        self.commandLayout = QHBoxLayout()
        self.commandLayout.setContentsMargins(1, 1, 1, 1)
        self.commandLayout.setSpacing(3)

        self.commandLabel = QLabel("Command:")
        font = self.commandLabel.font()
        font.setBold(True)
        self.commandLabel.setFont(font)

        self.commandCombo = QComboBox()
        self.commandCombo.addItems(scanList)
        self.scanList = scanList
        self.commandCombo.currentIndexChanged.connect(self.setCommandNumber)

        sspacer = QWidget()
        sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.commandLayout.addWidget(self.commandLabel)
        self.commandLayout.addWidget(self.commandCombo)
        self.commandLayout.addWidget(sspacer)

        # === Command display + Go button ===
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setSpacing(3)
        self.bottomLayout.setContentsMargins(1, 1, 1, 1)

        self.scanCommand = QLabel()
        # self.scanCommand.setStyleSheet("background-color: #ececdd")
        self.scanCommand.setTextInteractionFlags(Qt.TextSelectableByMouse)

        sspacer2 = QWidget()
        sspacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.goButton = QPushButton('Go')
        self.goButton.setFixedWidth(50)
        self.goButton.clicked.connect(self.go)

        self.bottomLayout.addWidget(self.scanCommand)
        self.bottomLayout.addWidget(self.goButton)
        self.bottomLayout.addWidget(sspacer2)

        # === Thin progress bar ===
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setFixedHeight(6)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                background: #f3f4f6;
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background-color: #3b82f6;
            }
        """)

        # === Time row ===
        self.timeRemainingLabel = QLabel("—")
        self.timeRemainingLabel.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.timeRemainingLabel.setStyleSheet("font-family: 'IBM Plex Sans', 'Segoe UI'; font-size: 9pt; color: #374151;")

        self.finishTimeLabel = QLabel("—")
        self.finishTimeLabel.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.finishTimeLabel.setStyleSheet("font-family: 'IBM Plex Sans', 'Segoe UI'; font-size: 9pt; color: #374151;")

        timeRow = QHBoxLayout()
        timeRow.setContentsMargins(1, 0, 1, 0)
        timeRow.addWidget(self.timeRemainingLabel, 1)
        timeRow.addWidget(self.finishTimeLabel, 1)

        # Keep old reference name for compatibility
        self.estimatedEnd = self.finishTimeLabel

        # === Assemble ===
        self.scanLayout.addLayout(self.commandLayout)
        self.scanLayout.addLayout(self.bottomLayout)
        # self.scanLayout.addWidget(self.progressBar)
        self.scanLayout.addLayout(timeRow)
        self.setLayout(self.scanLayout)

    def createPars(self):
        self.scanPars = {
            'ascan':    [_ScanW, [MotorPar('mot1'), IntervalPar('intervals'), TimePar('count-time')]],
            'a2scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), IntervalPar('intervals'), TimePar('count-time')]],
            'a3scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'),
                                  IntervalPar('intervals'), TimePar('count-time')]],
            'a4scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
                                  IntervalPar('intervals'), TimePar('count-time')]],
            'a5scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
                                  MotorPar('mot5'), IntervalPar('intervals'), TimePar('count-time')]],
            'vscan':    [_ScanW, [VscanMotorPar('mot1'), IntervalPar('intervals'), TimePar('count-time'), 
                                  FloatPar('minstep', null=True, default="", optional=True), 
                                  FloatPar('exponent',null=True, default="", optional=True)]],
            'v2scan':   [_ScanW, [VscanMotorPar('mot1'),  VscanMotorPar('mot2'), 
                                  IntervalPar('intervals'), TimePar('count-time'), 
                                  FloatPar('minstep', null=True, default="", optional=True), 
                                  FloatPar('exponent',null=True, default="", optional=True)]],
            'fscan':    [_ScanW, [FilePar('filename'), FloatPar('count-time', default="", null=True, optional=True)]],
            'mesh':     [_ScanW, [MotorPar('mot1'), IntervalPar('intervals1'), MotorPar('mot2'),
                                  IntervalPar('intervals2'), TimePar('count-time')]],
            'cscan':    [_ScanW, [MotorPar('mot1'),  TimePar('scantime'), TimePar('sleeptime', default=0, optional=True)]],
            'c2scan':   [_ScanW, [MotorPar('mot1'),  MotorPar('mot2'), TimePar('scantime'), TimePar('sleeptime', default=0, optional=True)]],
            'c3scan':   [_ScanW, [MotorPar('mot1'),  MotorPar('mot2'), MotorPar('mot3'),
                                  TimePar('scantime'), TimePar('sleeptime', default=0, optional=True)]],
            'c4scan':   [_ScanW, [MotorPar('mot1'),  MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
                                  TimePar('scantime'), TimePar('sleeptime', default=0, optional=True)]],
            'cmesh':   [_ScanW, [MotorPar('mot1'),  TimePar('scantime'), MotorPar('mot2'), 
                                  IntervalPar('intervals'), TimePar('sleeptime', default=0, optional=True)]],

            'dscan':    [_ScanW, [MotorPar('mot1', vnames=["mot1", "relat.start", "relat.end"]), 
                                 IntervalPar('intervals'), TimePar('count-time')]],
            'd2scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), 
                                  IntervalPar('intervals'), TimePar('count-time')]],
            'd3scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
                                  IntervalPar('intervals'), TimePar('count-time')]],
            'd4scan':   [_ScanW, [MotorPar('mot1'), MotorPar('mot2'), MotorPar('mot3'), MotorPar('mot4'),
                                  IntervalPar('intervals'), TimePar('count-time')]],
            'timescan': [_ScanW, [TimePar('count-time', optional=True), 
                                  TimePar('sleep-time', default="", null=True, optional=True)]],
            'loopscan': [_ScanW, [IntervalPar('nb-points'), TimePar('count-time', optional=True), 
                                  TimePar('sleep-time', default="", null=True, optional=True)]],
            'tscan':    [_ScanW, [FloatPar('start'), FloatPar('finish'), 
                                  IntervalPar('intervals'), TimePar('time'), 
                                  TimePar('sleep', default="", null=True, optional=True)]],
            'hscan':    [_ScanW, [HKLPar('H'), IntervalPar('intervals'), TimePar('count-time')]],
            'kscan':    [_ScanW, [HKLPar('K'), IntervalPar('intervals'), TimePar('count-time')]],
            'lscan':    [_ScanW, [HKLPar('L'), IntervalPar('intervals'), TimePar('count-time')]],
            'hklscan':  [_ScanW, [HKLPar('H'), HKLPar('K'), HKLPar('L'), 
                                  IntervalPar('intervals'), TimePar('count-time')]],
            'aziscan':  [_ScanW, [HKLPar('azi'), IntervalPar('intervals'), TimePar('count-time')]],
            'Escan':    [_ScanW, [MotorPar('mot1'), IntervalPar('intervals'), 
                                  TimePar('count-time')]],

        }

    def setCommandNumber(self, cmdno):
        cmd = self.scanList[cmdno]
        self.setCommandWidget(cmd)

    def setCommandWidget(self, cmd):

        cmd = str(cmd)

        if self.cmd == cmd:
            return

        self.checkHKL()

        if self.currentScanW:
            self.scanLayout.removeWidget(self.currentScanW)
            self.currentScanW.hide()

        self.currentScanW = self.getWidget(cmd)
        self.currentScanW.show()
        self.scanLayout.insertWidget(1, self.currentScanW)
        self.cmd = cmd

        if self.motormnes and self.currentScanW:
            self.currentScanW.setMotors(self.motormnes,self.aliases)

        try:
            cmdidx = self.scanList.index(cmd)
            self.commandCombo.setCurrentIndex(cmdidx)
        except IndexError:
            pass
        except ValueError:
            pass

        self.updateCommand()

    def setDataSource(self, datasource):
        self.datasource_ref = datasource

    def newScan(self, cmdstr):
        self.setCommand(cmdstr)
        self.scanStartTime = time.time()
        self.elapsed = 0
        self.estTotalTime = 0
        self.total_points = self.currentScanW.getNumberPoints()

        if self.total_points:
            self.progressBar.setRange(0, self.total_points - 1)
            self.progressBar.setValue(0)
        else:
            self.progressBar.setRange(0, 1)
            self.progressBar.setValue(0)

        self.timeRemainingLabel.setText("—")
        self.finishTimeLabel.setText("—")

        # start ticking
        self.is_running = True
        self.timer.start(1000)


    def setCommand(self, cmdstr):

        self.cmdstr = cmdstr
        self.cmdparts = self.cmdstr.split()
        if not len(self.cmdparts):
            return
        cmd = self.cmdparts[0]

        self.scanCommand.setText(self.cmdstr)
        self.checkHKL()

        self.setCommandWidget(cmd)

        try:
            self.currentScanW.setValues(self.cmdparts[1:])
        except:
            pass

        self.updateCommand()

    def getWidget(self, cmd):
        if cmd not in self.widgets:
            self.createWidget(cmd)
            #Qt.QObject.connect( self.widgets[cmd], Qt.SIGNAL("edited"), self.updateCommand )
            self.widgets[cmd].edited.connect(self.updateCommand)
        return self.widgets[cmd]

    def getCommand(self):
        return self.cmdstr

    def checkHKL(self):
        # Add HKL commands if necessary
        if (not self.hklChecked) and self.datasource_ref:
            hasHKL = self.datasource_ref().hasHKL()

            if hasHKL > -1:
                if hasHKL > 0:
                    self.commandCombo.addItems(hklList)
                    self.scanList.extend(hklList)
                self.hklChecked = True

    def updateCommand(self):

        # Read values and prepare command string
        valid, gopars = self.currentScanW.getValues()
        cmd = self.cmd + " " + " ".join([str(par) for par in gopars])
        self.scanCommand.setText(cmd)
        self.estimatedEnd.setText("")

        if not valid:
            self.goButton.setDisabled(True)
        else:
            self.goButton.setDisabled(False)

    def setMotors(self, motormnes, aliases):
        self.motormnes = motormnes
        self.aliases = aliases

        if self.currentScanW:
            self.currentScanW.setMotors(self.motormnes, self.aliases)
            if self.cmdstr:
                self.setCommand(self.cmdstr)

    def createWidget(self, scantype):
        if scantype not in self.scanPars:
            log.log(3,"scantype of name %s not recognized", scantype)
            self.widgets[scantype] = _ScanW("No scan")
            return
        scanclass, scanpars = self.scanPars[scantype]
        self.widgets[scantype] = scanclass(scantype, scanpars)

    def setMotorInterval(self, motor, begin, end):
        ct_time = self.currentScanW.getCountTime() 
        if ct_time is None:
            ct_time = 1
        self.setCommand("ascan %s %3.3s %3.3s %s" % (motor,begin,end, ct_time))

    def newPoint(self, ptno):
        self.current_point = ptno
        if not self.currentScanW or ptno == 0:
            return

        self.elapsed = time.time() - self.scanStartTime

        if self.total_points:
            self.progressBar.setValue(ptno)
            self.estTotalTime = (self.total_points - 1) * self.elapsed / ptno
            eta_epoch = self.scanStartTime + self.estTotalTime
            remain = max(0, self.estTotalTime - self.elapsed)

            self.timeRemainingLabel.setText(f"{self._fmt_duration(remain)} left")
            self.finishTimeLabel.setText(time.strftime("%H:%M", time.localtime(eta_epoch)))
        else:
            self.timeRemainingLabel.setText(f"{self._fmt_duration(self.elapsed)} elapsed")

    def setBusy(self, flag):
        if self.currentScanW:
            self.currentScanW.setBusy(flag)

        if not flag:
            self.is_running = False
            self.timer.stop()
            self.progressBar.setValue(self.progressBar.maximum())
            self.timeRemainingLabel.setText("Done")
        else:
            self.is_running = True
            self.timer.start(1000)
            self.timeRemainingLabel.setText("Running…")

    def go(self):
        try:
            # should validate values here
            valid, gopars = self.currentScanW.getValues()
            cmd = self.cmd + " " + " ".join([str(par) for par in gopars])

            if self.datasource_ref:
                self.datasource_ref().sendCommandA(cmd)

            self.currentScanW.resetEdited()
        except:
            log.log(3,"Cannot decode parameters. Check boxes")

    def _fmt_duration(self, seconds):
        seconds = max(0, int(seconds))
        h, m = divmod(seconds, 3600)
        m, s = divmod(m, 60)
        return (f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}")
        
    def update_progress_time(self, fraction, eta_epoch=None, seconds_left=None):
        """
        fraction: 0..1
        eta_epoch: Unix timestamp (float) for estimated finish (optional)
        seconds_left: remaining seconds (optional)
        """
        self.progressBar.setValue(int(max(0.0, min(1.0, fraction)) * 100))

        eta_txt = "—"
        if eta_epoch is not None:
            eta_txt = time.strftime("%H:%M", time.localtime(eta_epoch))

        left_txt = "—"
        if seconds_left is not None:
            left_txt = self._fmt_duration(seconds_left)

        # update the two labels that actually exist
        self.timeRemainingLabel.setText(f"{left_txt} left" if seconds_left is not None else "—")
        self.finishTimeLabel.setText(eta_txt if eta_epoch is not None else "—")

    def _update_timer_tick(self):
        if not self.is_running:
            return

        # Update elapsed time
        self.elapsed = time.time() - self.scanStartTime

        if self.total_points:
            # ETA calculation
            if self.current_point > 0:
                self.estTotalTime = (self.total_points - 1) * self.elapsed / self.current_point
                eta_epoch = self.scanStartTime + self.estTotalTime
                remain = max(0, self.estTotalTime - self.elapsed)
                self.timeRemainingLabel.setText(f"{self._fmt_duration(remain)} left")
                self.finishTimeLabel.setText(time.strftime("%H:%M", time.localtime(eta_epoch)))
        else:
            # If no total points, just show elapsed time
            self.timeRemainingLabel.setText(f"{self._fmt_duration(self.elapsed)} elapsed")



def test():
    import sys
    app = QApplication([])
    win = QMainWindow()
    scan = ScanWidget()
    scan.setMotors(['th', 'chi', 'tth', 'phi'], ['Theta','Chi','Two Theta','Phi'])
    scan.setCommand("ascan th 3 10 20 0.1")
    scan.setCommand("a2scan chi 3 10 tth 5 5.5 10 0.1")
    scan.setCommand("fscan toto")
    scan.setCommand("mesh th 3 7 20 chi 5 10 3 0.1")
    #scan.setCommand("timescan 0.1 0.3")

    win.setCentralWidget(scan)
    win.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    test()
