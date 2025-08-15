# #******************************************************************************
# #
# #  @(#)ServerPanel.py	3.9  01/09/24 CSS
# #
# #  "splot" Release 3
# #
# #  Copyright (c) 2013,2014,2015,2016,2017,2020,2021,2023,2024
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


# # from pyspec.graphics.QVariant import *
# # from pyspec.css_logger import log
# # from Constants import *

# # from MotorWidget import MotorWidget
# # from ScanWidget import ScanWidget

# # import weakref

# # class MoveWidget(QWidget):
# #     def __init__(self, *args):

# #         self.datablock = None
# #         self.select_mode = 'DEFAULT'

# #         self.motormnes = []
# #         self.aliases = {}

# #         self.stats_column = None
# #         self.stats_peak = ""
# #         self.stats_com = ""
# #         self.stats_cfwhm = ""

# #         self.current_motor = ""
# #         self.selected_motor = None

# #         QWidget.__init__(self, *args)
# #         self.moveLayout = QVBoxLayout()
# #         self.setLayout(self.moveLayout)

# #         headerLayout = QHBoxLayout()
# #         headerLayout.setSpacing(2)
# #         headerLayout.setContentsMargins(1, 1, 1, 1)
# #         headerLayout.setAlignment(
# #             Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

# #         # Try to create motorWidget
# #         try:
# #             self.motorWidget = MotorWidget()
# #         except Exception as e:
# #             print("⚠ Failed to create MotorWidget:", e)
# #             self.motorWidget = None

# #         statsLayout = QHBoxLayout()
# #         statsLayout.setSpacing(2)
# #         statsLayout.setContentsMargins(1, 1, 1, 1)
# #         statsLayout.setAlignment(
# #             Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

# #         self.moveLayout.addLayout(headerLayout)

# #         # Only add motorWidget if it was created successfully
# #         if self.motorWidget is not None:
# #             self.moveLayout.addWidget(self.motorWidget)

# #         self.moveLayout.addLayout(statsLayout)


# #         self.motorHeadL = QLabel("Motor:")
# #         self.motorCombo = QComboBox()
# #         self.motorCombo.currentIndexChanged.connect(self._motorChanged)

# #         headerLayout.addWidget(self.motorHeadL)
# #         headerLayout.addWidget(self.motorCombo)

# #         self.peakButton = QPushButton("PEAK")
# #         self.peakButton.setFixedWidth(55)
# #         self.peakButton.clicked.connect(self.selectPeak)

# #         self.comButton = QPushButton("COM")
# #         self.comButton.setFixedWidth(55)
# #         self.comButton.clicked.connect(self.selectCOM)

# #         self.fwhmButton = QPushButton("CFWHM")
# #         self.fwhmButton.setFixedWidth(65)
# #         self.fwhmButton.clicked.connect(self.selectFWHM)

# #         self.detLabel = QLabel("")

# #         self.sspacer = QWidget()
# #         self.sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

# #         statsLayout.addWidget(self.peakButton)
# #         statsLayout.addWidget(self.comButton)
# #         statsLayout.addWidget(self.fwhmButton)
# #         statsLayout.addWidget(self.detLabel)
# #         statsLayout.addWidget(self.sspacer)

# #         font = self.peakButton.font()
# #         font.setBold(True)
# #         font.setPointSize(10)
# #         self.peakButton.setFont(font)
# #         self.comButton.setFont(font)
# #         self.fwhmButton.setFont(font)

# #         # Connections and actions
# #         self.disableStatsButtons()

# #     def setDataSource(self,datasource):
# #         self.datasource_ref = datasource

# #     def setDataBlock(self,datablock):
# #         self.datablock = datablock 
# #         self.datablock.subscribe(self,STATS_UPDATED, self._statsChanged)
# #         self.datablock.subscribe(self,X_SELECTION_CHANGED, self._xSelectionChanged)

# #     def setMotors(self, motormnes, aliases):

# #         self.motormnes = motormnes
# #         self.aliases = aliases

# #         self.motorCombo.clear()
# #         self.motorCombo.addItems(["-select motor-", ] + motormnes)

# #         self._columnSelectionChanged(self.current_motor)

# #     def newScan(self, cmd):
# #         # this is just a trick to update aliases and mnes. I should think of something better
# #         self._columnSelectionChanged(self.current_motor)

# #     def _motorChanged(self, motorno):

# #         if self.selected_motor is None or motorno == 0:
# #             # only at startup. before a selection comes from the application
# #             pass 

# #         self.select_mode = 'DEFAULT'

# #         if motorno >= 1 and motorno <= len(self.motormnes):
# #             motmne = self.motormnes[motorno - 1]
# #             self.setSelectedMotor(motmne)
# #         else:
# #             self.setSelectedMotor("")

# #     def setPointSelection(self, xlabel, x):
# #         if xlabel not in self.motormnes:
# #             xlabel = self.datablock.getAlias(xlabel)

# #         if xlabel == self.selected_motor:
# #             self.setPosition(x)

# #     def setPosition(self, value):
# #         if value == "":
# #             self.motorWidget.setTargetPosition("")
# #         else:
# #             self.motorWidget.setTargetPosition("%.5g" % value)

# #     def setSelectedMotor(self, motor):

# #         self.blockSignals(True)
# #         if self.motorWidget is not None:
# #             self.motorWidget.hide()
# #             self.moveLayout.removeWidget(self.motorWidget)

# #         idx = -1
# #         motidx = 0
# #         self.motorWidget = self.emptyMotorWidget
# #         motormne = None

# #         if motor not in self.motormnes:  # it is maybe an alias
# #             motor = self.datablock.getCanonic(motor)

# #         if motor in self.motormnes:
# #             idx = self.motormnes.index(motor)
# #             motormne = motor

# #         #if motormne is None:
# #              #log.log(3,"Cannot find motor mnemonic for %s" % motor)

# #         if idx >= 0:
# #             motidx = idx + 1
# #             self.motorWidget = self.datasource_ref().getMotorWidget(motormne)
# #             # self.motorWidget = None
# #             if self.motorWidget:
# #                 self.motorWidget.setDisabled(False)
# #                 self.motorWidget.show()
# #                 self.select_mode = 'DEFAULT'
# #             else:
# #                 motidx = 0

# #         self.motorCombo.setCurrentIndex(motidx)
# #         self.moveLayout.insertWidget(1, self.motorWidget)

# #         if motidx == 0:
# #             self.motorWidget.hide()

# #         self.selected_motor = motormne
# #         self._update()
# #         self.blockSignals(False)

# #     def _statsChanged(self, stats):
# #         try:
# #             self.stats_xcolumn = stats["xcolumn"]
# #             self.stats_column = stats["column"]
# #             self.stats_peak = stats["peak"][0]
# #             self.stats_com = stats["com"]
# #             self.stats_cfwhm = stats["fwhm"][1]
# #             self._update()
# #         except:
# #             log.log(3,"Cannot understand starts for server panel. %s" % stats)

# #     def _xSelectionChanged(self,xsel):
# #         if len(xsel) > 0:
# #             self._columnSelectionChanged(xsel[0])

# #     def _columnSelectionChanged(self, xcol):

# #         if xcol not in self.motormnes:
# #             curr = self.datablock.getCanonic(xcol)
# #         else:
# #             curr = xcol

# #         self.current_motor = curr

# #         # update selection if never selected or if it is the one selected
# #         if self.current_motor == self.selected_motor or (not self.selected_motor):
# #             self.setSelectedMotor(xcol)

# #     def disableStatsButtons(self):
# #         self.peakButton.setDown(False)
# #         self.peakButton.setEnabled(False)
# #         self.comButton.setDown(False)
# #         self.comButton.setEnabled(False)
# #         self.fwhmButton.setDown(False)
# #         self.fwhmButton.setEnabled(False)

# #     def enableStatsButtons(self):
# #         if self.stats_peak is None:
# #             self.peakButton.setDown(False)
# #             self.peakButton.setEnabled(False)
# #         else:
# #             self.peakButton.setEnabled(True)

# #         if self.stats_com is None:
# #             self.comButton.setDown(False)
# #             self.comButton.setEnabled(False)
# #         else:
# #             self.comButton.setEnabled(True)

# #         if self.stats_cfwhm is None:
# #             self.fwhmButton.setDown(False)
# #             self.fwhmButton.setEnabled(False)
# #         else:
# #             self.fwhmButton.setEnabled(True)

# #     def selectPeak(self):
# #         if self.select_mode == 'PEAK':
# #             self.select_mode = 'DEFAULT'
# #         else:
# #             self.select_mode = 'PEAK'
# #         self._update()

# #     def selectCOM(self):
# #         if self.select_mode == 'COM':
# #             self.select_mode = 'DEFAULT'
# #         else:
# #             self.select_mode = 'COM'
# #         self._update()

# #     def selectFWHM(self):
# #         if self.select_mode == 'FWHM':
# #             self.select_mode = 'DEFAULT'
# #         else:
# #             self.select_mode = 'FWHM'
# #         self._update()

# #     def _update(self):

# #         if self.selected_motor == self.current_motor:
# #             self.enableStatsButtons()
# #         else:
# #             self.disableStatsButtons()

# #         # update position value
# #         self.comButton.setDown(False)
# #         self.peakButton.setDown(False)
# #         self.fwhmButton.setDown(False)

# #         if self.select_mode == 'PEAK':
# #             self.setPosition(self.stats_peak)
# #             self.peakButton.setDown(True)
# #         elif self.select_mode == 'COM':
# #             self.setPosition(self.stats_com)
# #             self.comButton.setDown(True)
# #         elif self.select_mode == 'FWHM':
# #             self.setPosition(self.stats_cfwhm)
# #             self.fwhmButton.setDown(True)
# #         elif self.select_mode == 'DEFAULT':
# #             pass
# #             #self.motorWidget.cancelMove()
# #         elif self.select_mode == 'USER':
# #             pass

# #         self.detLabel.setText("on %s" % self.stats_column)


# # class ServerPanel(QWidget):

# #     def __init__(self, *args):

# #         # Initialize data
# #         self.datasource_ref = None
# #         self.datablock = None
# #         self.conn = None

# #         # Draw widget
# #         QWidget.__init__(self, *args)
# #         self.setMinimumWidth(270)

# #         layout = QVBoxLayout()
# #         self.setLayout(layout)

# #         layout.setAlignment(Qt.AlignTop)
# #         layout.setContentsMargins(1, 1, 1, 1)
# #         layout.setSpacing(2)

# #         moveGroup = QGroupBox("Move")
# #         scanGroup = QGroupBox("Scan")

# #         layout.addWidget(moveGroup)
# #         layout.addWidget(scanGroup)

# #         # Move group
# #         moveLayout = QVBoxLayout()
# #         moveGroup.setLayout(moveLayout)
# #         moveGroup.setFlat(False)

# #         self.moveWidget = MoveWidget()
# #         moveLayout.addWidget(self.moveWidget)

# #         moveLayout.setSpacing(0)
# #         moveLayout.setContentsMargins(1, 1, 1, 1)

# #         # --- Raw SPEC Command Input ---
# #         cmdGroup = QGroupBox("Command")
# #         cmdGroup.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
# #         cmdGroup.setMaximumHeight(50)  # or 50
# #         layout.addWidget(cmdGroup)

# #         cmdLayout = QHBoxLayout()
# #         cmdLayout.setContentsMargins(1, 1, 1, 1)
# #         cmdLayout.setSpacing(2)
# #         cmdGroup.setLayout(cmdLayout)
# #         cmdGroup.setFlat(False)

# #         self.cmd_input = QLineEdit()
# #         self.cmd_input.setPlaceholderText("Enter SPEC command...")
# #         self.cmd_send_btn = QPushButton("Send")
# #         self.cmd_send_btn.setFixedWidth(50)
# #         self.cmd_send_btn.clicked.connect(self._send_command)

# #         cmdLayout.addWidget(self.cmd_input)
# #         cmdLayout.addWidget(self.cmd_send_btn)

# #         # Scan group
# #         scanLayout = QVBoxLayout()
# #         scanGroup.setLayout(scanLayout)
# #         scanGroup.setFlat(False)

# #         self.scanWidget = ScanWidget()
# #         scanLayout.addWidget(self.scanWidget)

# #         scanLayout.setSpacing(0)
# #         scanLayout.setContentsMargins(1, 1, 1, 1)

# #     def set_connection(self, conn):
# #         self.conn = conn

# #     def setDataSource(self, datasource):
# #         self.datasource_ref = datasource
# #         self.moveWidget.setDataSource(self.datasource_ref)
# #         self.scanWidget.setDataSource(self.datasource_ref)

# #     def setDataBlock(self,datablock):
# #         self.moveWidget.setDataBlock(datablock)
# #         self.datablock = datablock

# #     def setConnected(self):
# #         self.connected = True

# #     def setBusy(self, flag):
# #         self.setDisabled(flag)
# #         self.scanWidget.setBusy(flag)

# #     def newScan(self, metadata):
# #         scancmd = metadata['command']
# #         self.scanWidget.newScan(scancmd)
# #         self.moveWidget.newScan(scancmd)

# #     def newPoint(self, ptidx):
# #         self.scanWidget.newPoint(ptidx)

# #     def setMotors(self, motormnes):
# #         if self.datablock is None:
# #             return
# #         aliases = self.datablock.getAliases()
# #         self.scanWidget.setMotors(motormnes, aliases)
# #         self.moveWidget.setMotors(motormnes, aliases)

# #     def setPointSelection(self, xlabel, x):
# #         self.moveWidget.setPointSelection(xlabel,x)

# #     def setRegionSelection(self, xlabel, x1, x2):
# #         self.scanWidget.setMotorInterval(xlabel, x1, x2)

# #     def _send_command(self):
# #         if self.conn:
# #             cmd = self.cmd_input.text().strip()
# #             if cmd:
# #                 self.conn.sendCommand(cmd)

# # def test():
# #     import sys
# #     from SpecDataConnection import SpecDataConnection

# #     app = QApplication([])
# #     win = QMainWindow()

# #     spec_c  = SpecDataConnection(sys.argv[1])

# #     panel = ServerPanel()
# #     panel.set_connection(spec_c)

# #     panel.setMotors(['th', 'chi', 'phi'])

# #     win.setCentralWidget(panel)
# #     win.show()

# #     sys.exit(app.exec_())


# # if __name__ == '__main__':
# #     test()
# #******************************************************************************
# #
# #  @(#)ServerPanel.py	3.10  08/09/25 GANS
# #
# #******************************************************************************

# from pyspec.graphics.QVariant import *
# from pyspec.css_logger import log
# from Constants import *

# from MotorWidget import MotorWidget
# from ScanWidget import ScanWidget

# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
#     QPushButton, QComboBox, QSizePolicy, QMainWindow, QApplication
# )
# from PySide6.QtCore import Qt

# import weakref


# class MoveWidget(QWidget):
#     def __init__(self, *args):

#         self.conn = None
#         self.datasource_ref = None
#         self.datablock = None
#         self.select_mode = 'DEFAULT'

#         self.motormnes = []
#         self.aliases = {}

#         self.stats_column = None
#         self.stats_peak = ""
#         self.stats_com = ""
#         self.stats_cfwhm = ""

#         self.current_motor = ""
#         self.selected_motor = None

#         QWidget.__init__(self, *args)
#         self.moveLayout = QVBoxLayout()
#         self.setLayout(self.moveLayout)

#         headerLayout = QHBoxLayout()
#         headerLayout.setSpacing(2)
#         headerLayout.setContentsMargins(1, 1, 1, 1)
#         headerLayout.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

#         # Try to create motorWidget
#         try:
#             self.motorWidget = MotorWidget()
#         except Exception as e:
#             print("⚠ Failed to create MotorWidget:", e)
#             self.motorWidget = None

#         # New move row (replaces PEAK/COM/CFWHM)
#         moveRow = QHBoxLayout()
#         moveRow.setSpacing(4)
#         moveRow.setContentsMargins(1, 1, 1, 1)

#         self.moveLayout.addLayout(headerLayout)
#         if self.motorWidget is not None:
#             self.moveLayout.addWidget(self.motorWidget)
#         self.moveLayout.addLayout(moveRow)

#         self.motorHeadL = QLabel("Motor:")
#         self.motorCombo = QComboBox()
#         self.motorCombo.currentIndexChanged.connect(self._motorChanged)

#         headerLayout.addWidget(self.motorHeadL)
#         headerLayout.addWidget(self.motorCombo)

#         # Input + Move button
#         self.posInput = QLineEdit()
#         self.posInput.setPlaceholderText("Target position")
#         self.posInput.setFixedHeight(24)
#         self.posInput.returnPressed.connect(self._moveCurrentMotor)

#         self.moveBtn = QPushButton("Move")
#         self.moveBtn.setFixedWidth(60)
#         self.moveBtn.clicked.connect(self._moveCurrentMotor)

#         self.detLabel = QLabel("")
#         self.detLabel.setMinimumWidth(0)

#         spacer = QWidget()
#         spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         moveRow.addWidget(QLabel("to:"))
#         moveRow.addWidget(self.posInput)
#         moveRow.addWidget(self.moveBtn)
#         moveRow.addWidget(spacer)

#     def set_connection(self, conn):
#         self.conn = conn

#     def setDataSource(self, datasource):
#         self.datasource_ref = datasource

#     def setDataBlock(self, datablock):
#         self.datablock = datablock
#         self.datablock.subscribe(self, STATS_UPDATED, self._statsChanged)
#         self.datablock.subscribe(self, X_SELECTION_CHANGED, self._xSelectionChanged)

#     def setMotors(self, motormnes, aliases):
#         self.motormnes = motormnes
#         self.aliases = aliases
#         self.motorCombo.clear()
#         self.motorCombo.addItems(["-select motor-", ] + motormnes)
#         self._columnSelectionChanged(self.current_motor)

#     def newScan(self, cmd):
#         self._columnSelectionChanged(self.current_motor)

#     def _motorChanged(self, motorno):
#         if self.selected_motor is None or motorno == 0:
#             pass
#         self.select_mode = 'DEFAULT'
#         if 1 <= motorno <= len(self.motormnes):
#             motmne = self.motormnes[motorno - 1]
#             self.setSelectedMotor(motmne)
#         else:
#             self.setSelectedMotor("")

#     def setPointSelection(self, xlabel, x):
#         if xlabel not in self.motormnes:
#             xlabel = self.datablock.getAlias(xlabel)
#         if xlabel == self.selected_motor:
#             self.setPosition(x)

#     def setPosition(self, value):
#         if value == "":
#             self.posInput.setText("")
#             if self.motorWidget is not None:
#                 self.motorWidget.setTargetPosition("")
#         else:
#             txt = "%.5g" % value
#             self.posInput.setText(txt)
#             if self.motorWidget is not None:
#                 self.motorWidget.setTargetPosition(txt)

#     def setSelectedMotor(self, motor):
#         self.blockSignals(True)
#         if self.motorWidget is not None:
#             self.motorWidget.hide()
#             self.moveLayout.removeWidget(self.motorWidget)

#         idx = -1
#         motidx = 0
#         self.motorWidget = getattr(self, "emptyMotorWidget", None)
#         motormne = None

#         if motor not in self.motormnes:
#             motor = self.datablock.getCanonic(motor)

#         if motor in self.motormnes:
#             idx = self.motormnes.index(motor)
#             motormne = motor

#         if idx >= 0:
#             motidx = idx + 1
#             self.motorWidget = self.datasource_ref().getMotorWidget(motormne)
#             if self.motorWidget:
#                 self.motorWidget.setDisabled(False)
#                 self.motorWidget.show()
#                 self.select_mode = 'DEFAULT'
#             else:
#                 motidx = 0

#         self.motorCombo.setCurrentIndex(motidx)
#         if self.motorWidget is not None:
#             self.moveLayout.insertWidget(1, self.motorWidget)
#             if motidx == 0:
#                 self.motorWidget.hide()

#         self.selected_motor = motormne
#         self._update()
#         self.blockSignals(False)

#     def _statsChanged(self, stats):
#         try:
#             self.stats_xcolumn = stats["xcolumn"]
#             self.stats_column = stats["column"]
#             self.stats_peak = stats["peak"][0]
#             self.stats_com = stats["com"]
#             self.stats_cfwhm = stats["fwhm"][1]
#             self._update()
#         except:
#             log.log(3, "Cannot understand stats for server panel. %s" % stats)

#     def _xSelectionChanged(self, xsel):
#         if len(xsel) > 0:
#             self._columnSelectionChanged(xsel[0])

#     def _columnSelectionChanged(self, xcol):
#         if xcol not in self.motormnes:
#             curr = self.datablock.getCanonic(xcol)
#         else:
#             curr = xcol
#         self.current_motor = curr
#         if self.current_motor == self.selected_motor or (not self.selected_motor):
#             self.setSelectedMotor(xcol)

#     def _moveCurrentMotor(self):
#         if not self.conn:
#             return
#         motor = self.selected_motor
#         if not motor:
#             return
#         val = self.posInput.text().strip()
#         if not val:
#             return
#         cmd = f"mv {motor} {val}"
#         try:
#             self.conn.sendCommand(cmd)
#         except Exception as e:
#             log.log(2, "Move failed: %s" % e)

#     def _update(self):
#         self.detLabel.setText("on %s" % (self.stats_column if self.stats_column else ""))


# class ServerPanel(QWidget):

#     def __init__(self, *args):

#         self.datasource_ref = None
#         self.datablock = None
#         self.conn = None

#         QWidget.__init__(self, *args)
#         self.setMinimumWidth(270)

#         layout = QVBoxLayout()
#         self.setLayout(layout)

#         layout.setAlignment(Qt.AlignTop)
#         layout.setContentsMargins(1, 1, 1, 1)
#         layout.setSpacing(2)

#         moveGroup = QGroupBox("Move")
#         scanGroup = QGroupBox("Scan")

#         layout.addWidget(moveGroup)
#         layout.addWidget(scanGroup)

#         # Move group
#         moveLayout = QVBoxLayout()
#         moveGroup.setLayout(moveLayout)
#         moveGroup.setFlat(False)

#         self.moveWidget = MoveWidget()
#         moveLayout.addWidget(self.moveWidget)

#         moveLayout.setSpacing(0)
#         moveLayout.setContentsMargins(1, 1, 1, 1)

#         # --- Raw SPEC Command Input ---
#         cmdGroup = QGroupBox("Command")
#         cmdGroup.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
#         cmdGroup.setMaximumHeight(50)
#         layout.addWidget(cmdGroup)

#         cmdLayout = QHBoxLayout()
#         cmdLayout.setContentsMargins(1, 1, 1, 1)
#         cmdLayout.setSpacing(2)
#         cmdGroup.setLayout(cmdLayout)
#         cmdGroup.setFlat(False)

#         self.cmd_input = QLineEdit()
#         self.cmd_input.setPlaceholderText("Enter SPEC command...")
#         self.cmd_send_btn = QPushButton("Send")
#         self.cmd_send_btn.setFixedWidth(50)
#         self.cmd_send_btn.clicked.connect(self._send_command)
#         self.cmd_input.returnPressed.connect(self._send_command)

#         cmdLayout.addWidget(self.cmd_input)
#         cmdLayout.addWidget(self.cmd_send_btn)

#         # Scan group
#         scanLayout = QVBoxLayout()
#         scanGroup.setLayout(scanLayout)
#         scanGroup.setFlat(False)

#         self.scanWidget = ScanWidget()
#         scanLayout.addWidget(self.scanWidget)

#         scanLayout.setSpacing(0)
#         scanLayout.setContentsMargins(1, 1, 1, 1)

#     def set_connection(self, conn):
#         self.conn = conn
#         self.moveWidget.set_connection(conn)

#     def setDataSource(self, datasource):
#         self.datasource_ref = datasource
#         self.moveWidget.setDataSource(self.datasource_ref)
#         self.scanWidget.setDataSource(self.datasource_ref)

#     def setDataBlock(self, datablock):
#         self.moveWidget.setDataBlock(datablock)
#         self.datablock = datablock

#     def setConnected(self):
#         self.connected = True

#     def setBusy(self, flag):
#         self.setDisabled(flag)
#         self.scanWidget.setBusy(flag)

#     def newScan(self, metadata):
#         scancmd = metadata['command']
#         self.scanWidget.newScan(scancmd)
#         self.moveWidget.newScan(scancmd)

#     def newPoint(self, ptidx):
#         self.scanWidget.newPoint(ptidx)

#     def setMotors(self, motormnes):
#         if self.datablock is None:
#             return
#         aliases = self.datablock.getAliases()
#         self.scanWidget.setMotors(motormnes, aliases)
#         self.moveWidget.setMotors(motormnes, aliases)

#     def setPointSelection(self, xlabel, x):
#         self.moveWidget.setPointSelection(xlabel, x)

#     def setRegionSelection(self, xlabel, x1, x2):
#         self.scanWidget.setMotorInterval(xlabel, x1, x2)

#     def _send_command(self):
#         if self.conn:
#             cmd = self.cmd_input.text().strip()
#             if cmd:
#                 self.conn.sendCommand(cmd)
#                 self.cmd_input.clear()


# def test():
#     import sys
#     from SpecDataConnection import SpecDataConnection

#     app = QApplication([])
#     win = QMainWindow()

#     spec_c = SpecDataConnection(sys.argv[1])

#     panel = ServerPanel()
#     panel.set_connection(spec_c)

#     panel.setMotors(['th', 'chi', 'phi'])

#     win.setCentralWidget(panel)
#     win.show()

#     sys.exit(app.exec_())


# if __name__ == '__main__':
#     test()

#******************************************************************************
#
#  @(#)ServerPanel.py	3.9  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2020,2021,2023,2024
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


# from pyspec.graphics.QVariant import *
# from pyspec.css_logger import log
# from Constants import *

# from MotorWidget import MotorWidget
# from ScanWidget import ScanWidget

# import weakref

# class MoveWidget(QWidget):
#     def __init__(self, *args):

#         self.datablock = None
#         self.select_mode = 'DEFAULT'

#         self.motormnes = []
#         self.aliases = {}

#         self.stats_column = None
#         self.stats_peak = ""
#         self.stats_com = ""
#         self.stats_cfwhm = ""

#         self.current_motor = ""
#         self.selected_motor = None

#         QWidget.__init__(self, *args)
#         self.moveLayout = QVBoxLayout()
#         self.setLayout(self.moveLayout)

#         headerLayout = QHBoxLayout()
#         headerLayout.setSpacing(2)
#         headerLayout.setContentsMargins(1, 1, 1, 1)
#         headerLayout.setAlignment(
#             Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

#         # Try to create motorWidget
#         try:
#             self.motorWidget = MotorWidget()
#         except Exception as e:
#             print("⚠ Failed to create MotorWidget:", e)
#             self.motorWidget = None

#         statsLayout = QHBoxLayout()
#         statsLayout.setSpacing(2)
#         statsLayout.setContentsMargins(1, 1, 1, 1)
#         statsLayout.setAlignment(
#             Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

#         self.moveLayout.addLayout(headerLayout)

#         # Only add motorWidget if it was created successfully
#         if self.motorWidget is not None:
#             self.moveLayout.addWidget(self.motorWidget)

#         self.moveLayout.addLayout(statsLayout)


#         self.motorHeadL = QLabel("Motor:")
#         self.motorCombo = QComboBox()
#         self.motorCombo.currentIndexChanged.connect(self._motorChanged)

#         headerLayout.addWidget(self.motorHeadL)
#         headerLayout.addWidget(self.motorCombo)

#         self.peakButton = QPushButton("PEAK")
#         self.peakButton.setFixedWidth(55)
#         self.peakButton.clicked.connect(self.selectPeak)

#         self.comButton = QPushButton("COM")
#         self.comButton.setFixedWidth(55)
#         self.comButton.clicked.connect(self.selectCOM)

#         self.fwhmButton = QPushButton("CFWHM")
#         self.fwhmButton.setFixedWidth(65)
#         self.fwhmButton.clicked.connect(self.selectFWHM)

#         self.detLabel = QLabel("")

#         self.sspacer = QWidget()
#         self.sspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         statsLayout.addWidget(self.peakButton)
#         statsLayout.addWidget(self.comButton)
#         statsLayout.addWidget(self.fwhmButton)
#         statsLayout.addWidget(self.detLabel)
#         statsLayout.addWidget(self.sspacer)

#         font = self.peakButton.font()
#         font.setBold(True)
#         font.setPointSize(10)
#         self.peakButton.setFont(font)
#         self.comButton.setFont(font)
#         self.fwhmButton.setFont(font)

#         # Connections and actions
#         self.disableStatsButtons()

#     def setDataSource(self,datasource):
#         self.datasource_ref = datasource

#     def setDataBlock(self,datablock):
#         self.datablock = datablock 
#         self.datablock.subscribe(self,STATS_UPDATED, self._statsChanged)
#         self.datablock.subscribe(self,X_SELECTION_CHANGED, self._xSelectionChanged)

#     def setMotors(self, motormnes, aliases):

#         self.motormnes = motormnes
#         self.aliases = aliases

#         self.motorCombo.clear()
#         self.motorCombo.addItems(["-select motor-", ] + motormnes)

#         self._columnSelectionChanged(self.current_motor)

#     def newScan(self, cmd):
#         # this is just a trick to update aliases and mnes. I should think of something better
#         self._columnSelectionChanged(self.current_motor)

#     def _motorChanged(self, motorno):

#         if self.selected_motor is None or motorno == 0:
#             # only at startup. before a selection comes from the application
#             pass 

#         self.select_mode = 'DEFAULT'

#         if motorno >= 1 and motorno <= len(self.motormnes):
#             motmne = self.motormnes[motorno - 1]
#             self.setSelectedMotor(motmne)
#         else:
#             self.setSelectedMotor("")

#     def setPointSelection(self, xlabel, x):
#         if xlabel not in self.motormnes:
#             xlabel = self.datablock.getAlias(xlabel)

#         if xlabel == self.selected_motor:
#             self.setPosition(x)

#     def setPosition(self, value):
#         if value == "":
#             self.motorWidget.setTargetPosition("")
#         else:
#             self.motorWidget.setTargetPosition("%.5g" % value)

#     def setSelectedMotor(self, motor):

#         self.blockSignals(True)
#         if self.motorWidget is not None:
#             self.motorWidget.hide()
#             self.moveLayout.removeWidget(self.motorWidget)

#         idx = -1
#         motidx = 0
#         self.motorWidget = self.emptyMotorWidget
#         motormne = None

#         if motor not in self.motormnes:  # it is maybe an alias
#             motor = self.datablock.getCanonic(motor)

#         if motor in self.motormnes:
#             idx = self.motormnes.index(motor)
#             motormne = motor

#         #if motormne is None:
#              #log.log(3,"Cannot find motor mnemonic for %s" % motor)

#         if idx >= 0:
#             motidx = idx + 1
#             self.motorWidget = self.datasource_ref().getMotorWidget(motormne)
#             # self.motorWidget = None
#             if self.motorWidget:
#                 self.motorWidget.setDisabled(False)
#                 self.motorWidget.show()
#                 self.select_mode = 'DEFAULT'
#             else:
#                 motidx = 0

#         self.motorCombo.setCurrentIndex(motidx)
#         self.moveLayout.insertWidget(1, self.motorWidget)

#         if motidx == 0:
#             self.motorWidget.hide()

#         self.selected_motor = motormne
#         self._update()
#         self.blockSignals(False)

#     def _statsChanged(self, stats):
#         try:
#             self.stats_xcolumn = stats["xcolumn"]
#             self.stats_column = stats["column"]
#             self.stats_peak = stats["peak"][0]
#             self.stats_com = stats["com"]
#             self.stats_cfwhm = stats["fwhm"][1]
#             self._update()
#         except:
#             log.log(3,"Cannot understand starts for server panel. %s" % stats)

#     def _xSelectionChanged(self,xsel):
#         if len(xsel) > 0:
#             self._columnSelectionChanged(xsel[0])

#     def _columnSelectionChanged(self, xcol):

#         if xcol not in self.motormnes:
#             curr = self.datablock.getCanonic(xcol)
#         else:
#             curr = xcol

#         self.current_motor = curr

#         # update selection if never selected or if it is the one selected
#         if self.current_motor == self.selected_motor or (not self.selected_motor):
#             self.setSelectedMotor(xcol)

#     def disableStatsButtons(self):
#         self.peakButton.setDown(False)
#         self.peakButton.setEnabled(False)
#         self.comButton.setDown(False)
#         self.comButton.setEnabled(False)
#         self.fwhmButton.setDown(False)
#         self.fwhmButton.setEnabled(False)

#     def enableStatsButtons(self):
#         if self.stats_peak is None:
#             self.peakButton.setDown(False)
#             self.peakButton.setEnabled(False)
#         else:
#             self.peakButton.setEnabled(True)

#         if self.stats_com is None:
#             self.comButton.setDown(False)
#             self.comButton.setEnabled(False)
#         else:
#             self.comButton.setEnabled(True)

#         if self.stats_cfwhm is None:
#             self.fwhmButton.setDown(False)
#             self.fwhmButton.setEnabled(False)
#         else:
#             self.fwhmButton.setEnabled(True)

#     def selectPeak(self):
#         if self.select_mode == 'PEAK':
#             self.select_mode = 'DEFAULT'
#         else:
#             self.select_mode = 'PEAK'
#         self._update()

#     def selectCOM(self):
#         if self.select_mode == 'COM':
#             self.select_mode = 'DEFAULT'
#         else:
#             self.select_mode = 'COM'
#         self._update()

#     def selectFWHM(self):
#         if self.select_mode == 'FWHM':
#             self.select_mode = 'DEFAULT'
#         else:
#             self.select_mode = 'FWHM'
#         self._update()

#     def _update(self):

#         if self.selected_motor == self.current_motor:
#             self.enableStatsButtons()
#         else:
#             self.disableStatsButtons()

#         # update position value
#         self.comButton.setDown(False)
#         self.peakButton.setDown(False)
#         self.fwhmButton.setDown(False)

#         if self.select_mode == 'PEAK':
#             self.setPosition(self.stats_peak)
#             self.peakButton.setDown(True)
#         elif self.select_mode == 'COM':
#             self.setPosition(self.stats_com)
#             self.comButton.setDown(True)
#         elif self.select_mode == 'FWHM':
#             self.setPosition(self.stats_cfwhm)
#             self.fwhmButton.setDown(True)
#         elif self.select_mode == 'DEFAULT':
#             pass
#             #self.motorWidget.cancelMove()
#         elif self.select_mode == 'USER':
#             pass

#         self.detLabel.setText("on %s" % self.stats_column)


# class ServerPanel(QWidget):

#     def __init__(self, *args):

#         # Initialize data
#         self.datasource_ref = None
#         self.datablock = None
#         self.conn = None

#         # Draw widget
#         QWidget.__init__(self, *args)
#         self.setMinimumWidth(270)

#         layout = QVBoxLayout()
#         self.setLayout(layout)

#         layout.setAlignment(Qt.AlignTop)
#         layout.setContentsMargins(1, 1, 1, 1)
#         layout.setSpacing(2)

#         moveGroup = QGroupBox("Move")
#         scanGroup = QGroupBox("Scan")

#         layout.addWidget(moveGroup)
#         layout.addWidget(scanGroup)

#         # Move group
#         moveLayout = QVBoxLayout()
#         moveGroup.setLayout(moveLayout)
#         moveGroup.setFlat(False)

#         self.moveWidget = MoveWidget()
#         moveLayout.addWidget(self.moveWidget)

#         moveLayout.setSpacing(0)
#         moveLayout.setContentsMargins(1, 1, 1, 1)

#         # --- Raw SPEC Command Input ---
#         cmdGroup = QGroupBox("Command")
#         cmdGroup.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
#         cmdGroup.setMaximumHeight(50)  # or 50
#         layout.addWidget(cmdGroup)

#         cmdLayout = QHBoxLayout()
#         cmdLayout.setContentsMargins(1, 1, 1, 1)
#         cmdLayout.setSpacing(2)
#         cmdGroup.setLayout(cmdLayout)
#         cmdGroup.setFlat(False)

#         self.cmd_input = QLineEdit()
#         self.cmd_input.setPlaceholderText("Enter SPEC command...")
#         self.cmd_send_btn = QPushButton("Send")
#         self.cmd_send_btn.setFixedWidth(50)
#         self.cmd_send_btn.clicked.connect(self._send_command)

#         cmdLayout.addWidget(self.cmd_input)
#         cmdLayout.addWidget(self.cmd_send_btn)

#         # Scan group
#         scanLayout = QVBoxLayout()
#         scanGroup.setLayout(scanLayout)
#         scanGroup.setFlat(False)

#         self.scanWidget = ScanWidget()
#         scanLayout.addWidget(self.scanWidget)

#         scanLayout.setSpacing(0)
#         scanLayout.setContentsMargins(1, 1, 1, 1)

#     def set_connection(self, conn):
#         self.conn = conn

#     def setDataSource(self, datasource):
#         self.datasource_ref = datasource
#         self.moveWidget.setDataSource(self.datasource_ref)
#         self.scanWidget.setDataSource(self.datasource_ref)

#     def setDataBlock(self,datablock):
#         self.moveWidget.setDataBlock(datablock)
#         self.datablock = datablock

#     def setConnected(self):
#         self.connected = True

#     def setBusy(self, flag):
#         self.setDisabled(flag)
#         self.scanWidget.setBusy(flag)

#     def newScan(self, metadata):
#         scancmd = metadata['command']
#         self.scanWidget.newScan(scancmd)
#         self.moveWidget.newScan(scancmd)

#     def newPoint(self, ptidx):
#         self.scanWidget.newPoint(ptidx)

#     def setMotors(self, motormnes):
#         if self.datablock is None:
#             return
#         aliases = self.datablock.getAliases()
#         self.scanWidget.setMotors(motormnes, aliases)
#         self.moveWidget.setMotors(motormnes, aliases)

#     def setPointSelection(self, xlabel, x):
#         self.moveWidget.setPointSelection(xlabel,x)

#     def setRegionSelection(self, xlabel, x1, x2):
#         self.scanWidget.setMotorInterval(xlabel, x1, x2)

#     def _send_command(self):
#         if self.conn:
#             cmd = self.cmd_input.text().strip()
#             if cmd:
#                 self.conn.sendCommand(cmd)

# def test():
#     import sys
#     from SpecDataConnection import SpecDataConnection

#     app = QApplication([])
#     win = QMainWindow()

#     spec_c  = SpecDataConnection(sys.argv[1])

#     panel = ServerPanel()
#     panel.set_connection(spec_c)

#     panel.setMotors(['th', 'chi', 'phi'])

#     win.setCentralWidget(panel)
#     win.show()

#     sys.exit(app.exec_())


# if __name__ == '__main__':
#     test()

#******************************************************************************
#
#  @(#)ServerPanel.py	3.10  08/09/25 GANS
#
#******************************************************************************

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log
from Constants import *

from MotorWidget import MotorWidget
from ScanWidget import ScanWidget
from ScanBuilder import ScanBuilderDialog
from CommandLineWidget import CommandLineWidget
from ScanRunnerWidget import ScanRunnerWidget


from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QComboBox, QSizePolicy, QMainWindow, QApplication
)
from PySide6.QtCore import Qt

import weakref


class MoveWidget(QWidget):
    def __init__(self, *args):

        self.conn = None
        self.datasource_ref = None
        self.datablock = None
        self.select_mode = 'DEFAULT'

        self.motormnes = []
        self.aliases = {}

        self.stats_column = None
        self.stats_peak = ""
        self.stats_com = ""
        self.stats_cfwhm = ""

        self.current_motor = ""
        self.selected_motor = None

        self.detLabel = QLabel("")
        self.detLabel.setMinimumWidth(0)


        QWidget.__init__(self, *args)
        self.moveLayout = QVBoxLayout()
        self.setLayout(self.moveLayout)

        headerLayout = QHBoxLayout()
        headerLayout.setSpacing(2)
        headerLayout.setContentsMargins(1, 1, 1, 1)
        headerLayout.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

        # Try to create motorWidget
        try:
            self.motorWidget = MotorWidget()
        except Exception as e:
            print("⚠ Failed to create MotorWidget:", e)
            self.motorWidget = None

        # New move row (replaces PEAK/COM/CFWHM)
        # moveRow = QHBoxLayout()
        # moveRow.setSpacing(4)
        # moveRow.setContentsMargins(1, 1, 1, 1)
        # moveRow.addWidget(self.detLabel)


        self.moveLayout.addLayout(headerLayout)
        if self.motorWidget is not None:
            self.moveLayout.addWidget(self.motorWidget)
        # self.moveLayout.addLayout(moveRow)

        self.motorHeadL = QLabel("Motor:")
        self.motorCombo = QComboBox()
        self.motorCombo.currentIndexChanged.connect(self._motorChanged)

        headerLayout.addWidget(self.motorHeadL)
        headerLayout.addWidget(self.motorCombo)

        # # Input + Move button
        # self.posInput = QLineEdit()
        # self.posInput.setPlaceholderText("Target position")
        # self.posInput.setFixedHeight(24)
        # self.posInput.returnPressed.connect(self._moveCurrentMotor)

        # self.moveBtn = QPushButton("Move")
        # self.moveBtn.setFixedWidth(60)
        # self.moveBtn.clicked.connect(self._moveCurrentMotor)

        # self.detLabel = QLabel("")
        # self.detLabel.setMinimumWidth(0)

        # spacer = QWidget()
        # spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # moveRow.addWidget(QLabel("to:"))
        # moveRow.addWidget(self.posInput)
        # moveRow.addWidget(self.moveBtn)
        # moveRow.addWidget(spacer)

    def set_connection(self, conn):
        self.conn = conn

    def setDataSource(self, datasource):
        self.datasource_ref = datasource

    def setDataBlock(self, datablock):
        self.datablock = datablock
        self.datablock.subscribe(self, STATS_UPDATED, self._statsChanged)
        self.datablock.subscribe(self, X_SELECTION_CHANGED, self._xSelectionChanged)

    def setMotors(self, motormnes, aliases):
        self.motormnes = motormnes or []
        self.aliases = aliases or {}
        self.motorCombo.blockSignals(True)
        self.motorCombo.clear()
        self.motorCombo.addItems(["-select motor-"] + self.motormnes)
        self.motorCombo.blockSignals(False)

        # Only try to sync to column selection if a datablock exists
        if self.datablock:
            self._columnSelectionChanged(self.current_motor)
        else:
            # default to first motor if available to make the widget usable standalone
            if self.motormnes:
                self.setSelectedMotor(self.motormnes[0])

    def newScan(self, cmd):
        self._columnSelectionChanged(self.current_motor)

    def _motorChanged(self, motorno):
        # index 0 is the placeholder
        if motorno == 0:
            self.selected_motor = None
            return
        self.select_mode = 'DEFAULT'
        if 1 <= motorno <= len(self.motormnes):
            motmne = self.motormnes[motorno - 1]
            self.setSelectedMotor(motmne)

    def setPointSelection(self, xlabel, x):
        if xlabel not in self.motormnes:
            xlabel = self.datablock.getAlias(xlabel)
        if xlabel == self.selected_motor:
            self.setPosition(x)

    def setPosition(self, value):
        if value == "":
            self.posInput.setText("")
            if self.motorWidget is not None:
                self.motorWidget.setTargetPosition("")
        else:
            txt = "%.5g" % value
            self.posInput.setText(txt)
            if self.motorWidget is not None:
                self.motorWidget.setTargetPosition(txt)


    def setSelectedMotor(self, motor):
        self.blockSignals(True)

        # Don't assume datablock/datasource are present
        motormne = None
        if motor in self.motormnes:
            motormne = motor
        elif self.datablock:
            can = self.datablock.getCanonic(motor)
            if can in self.motormnes:
                motormne = can

        # Do not force the combo back to index 0 if we can't build a MotorWidget
        if motormne:
            idx = self.motormnes.index(motormne) + 1
            self.motorCombo.setCurrentIndex(idx)

            # Try to attach the detailed motor panel if a datasource was provided
            mw = None
            if callable(self.datasource_ref):
                try:
                    mw = self.datasource_ref().getMotorWidget(motormne)
                except Exception:
                    mw = None

            # Replace the inline widget, but don't break selection if unavailable
            if self.motorWidget is not None:
                self.motorWidget.hide()
                self.moveLayout.removeWidget(self.motorWidget)
            self.motorWidget = mw or getattr(self, "emptyMotorWidget", None)
            if self.motorWidget is not None:
                self.moveLayout.insertWidget(1, self.motorWidget)
                self.motorWidget.setDisabled(False)
                self.motorWidget.show()

        self.selected_motor = motormne
        self._update()
        self.blockSignals(False)

    def _statsChanged(self, stats):
        try:
            self.stats_xcolumn = stats["xcolumn"]
            self.stats_column = stats["column"]
            self.stats_peak = stats["peak"][0]
            self.stats_com = stats["com"]
            self.stats_cfwhm = stats["fwhm"][1]
            self._update()
        except:
            log.log(3, "Cannot understand stats for server panel. %s" % stats)

    def _xSelectionChanged(self, xsel):
        if len(xsel) > 0:
            self._columnSelectionChanged(xsel[0])

    def _columnSelectionChanged(self, xcol):
        if xcol not in self.motormnes:
            curr = self.datablock.getCanonic(xcol)
        else:
            curr = xcol
        self.current_motor = curr
        if self.current_motor == self.selected_motor or (not self.selected_motor):
            self.setSelectedMotor(xcol)


    def _moveCurrentMotor(self):
        if not self.selected_motor:
            return
        val = self.posInput.text().strip()
        if not val:
            return
        cmd = f"umv {self.selected_motor} {val}"
        self._send(cmd)

    def _send(self, cmd: str):
        try:
            if self.conn is not None and hasattr(self.conn, "sendCommand"):
                self.conn.sendCommand(cmd)
            elif self.conn is not None and hasattr(self.conn, "send"):
                self.conn.send(cmd)
            else:
                # wrong
                from gans_control.backend.session.spec_session import spec_controller
                spec_controller.send(cmd)
        except Exception as e:
            log.log(2, f"Move failed: {e}")

    def _update(self):
        self.detLabel.setText("on %s" % (self.stats_column if self.stats_column else ""))


class ServerPanel(QWidget):

    def __init__(self, *args):

        self.datasource_ref = None
        self.datablock = None
        self.conn = None

        QWidget.__init__(self, *args)
        self.setMinimumWidth(270)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(2)

        moveGroup = QGroupBox("")
        scanGroup = QGroupBox("")

        layout.addWidget(moveGroup)
        layout.addWidget(scanGroup)

        # Move group
        moveLayout = QVBoxLayout()
        moveGroup.setLayout(moveLayout)
        moveGroup.setFlat(False)

        self.moveWidget = MoveWidget()
        moveLayout.addWidget(self.moveWidget)

        moveLayout.setSpacing(0)
        moveLayout.setContentsMargins(1, 1, 1, 1)

        # Scan group
        scanLayout = QVBoxLayout()
        scanGroup.setLayout(scanLayout)
        scanGroup.setFlat(False)

        self.scanWidget = ScanWidget()
        scanLayout.addWidget(self.scanWidget)

        scanLayout.setSpacing(0)
        scanLayout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(scanGroup)

        self.scanRunner = ScanRunnerWidget(self)
        self.scanRunner.set_connection(self.conn)
        layout.addWidget(self.scanRunner)

        # --- Raw SPEC Command Input ---
        self.cmdline = CommandLineWidget(self)
        layout.addWidget(self.cmdline)

        # tidy overall panel spacing
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(6)

    def set_connection(self, conn):
        self.conn = conn
        self.moveWidget.set_connection(conn)
        if hasattr(self.scanWidget, "set_connection"):
            self.scanWidget.set_connection(conn)
        if hasattr(self, "scanRunner"):
            self.scanRunner.set_connection(conn)



    def setDataSource(self, datasource):
        self.datasource_ref = datasource
        self.moveWidget.setDataSource(self.datasource_ref)
        self.scanWidget.setDataSource(self.datasource_ref)

    def setDataBlock(self, datablock):
        self.moveWidget.setDataBlock(datablock)
        self.datablock = datablock

    def setConnected(self):
        self.connected = True

    def setBusy(self, flag):
        self.setDisabled(flag)
        self.scanWidget.setBusy(flag)

    def newScan(self, metadata):
        scancmd = metadata['command']
        self.scanWidget.newScan(scancmd)
        self.moveWidget.newScan(scancmd)

    def newPoint(self, ptidx):
        self.scanWidget.newPoint(ptidx)

    def setMotors(self, motormnes):
        # Never early-return; allow the move widget to be usable without a datablock
        aliases = self.datablock.getAliases() if self.datablock else {}
        self.scanWidget.setMotors(motormnes, aliases) if hasattr(self.scanWidget, "setMotors") else None
        self.moveWidget.setMotors(motormnes, aliases)
    
    def setRegionSelection(self, xlabel, x1, x2):
        self.scanWidget.setMotorInterval(xlabel, x1, x2)

    def get_connection(self):
        if self.conn:
            return self.conn
        if hasattr(self.scanWidget, "_conn") and self.scanWidget._conn:
            return self.scanWidget._conn
        return None

    def _send_command(self):
        conn = self.get_connection()
        print("Current connection:", conn)
        if conn:
            cmd = self.cmd_input.text().strip()
            if cmd:
                try:
                    print(f"Sending command: {cmd}")
                    conn.sendCommand(cmd)
                except Exception as e:
                    print(f"Error sending command: {e}")
                self.cmd_input.clear()
        else:
            print("No connection available to send command")

    def _open_scan_builder(self):
        dlg = ScanBuilderDialog(self)
        dlg.set_connection(self.conn)
        if hasattr(self, "motormnes") and self.motormnes:
            try:
                dlg.scan_widget.setMotors(self.motormnes, self.datablock.getAliases())
            except Exception:
                pass
        dlg.exec()

    def _populate_scn_files(self):
        self.scn_selector.clear()
        scn_dir = os.path.expanduser("~/.gans-control/generated_spec/last_run")
        if not os.path.isdir(scn_dir):
            print(f"SCN directory not found: {scn_dir}")
            return
        files = [f for f in os.listdir(scn_dir) if f.lower().endswith(".scn")]
        for f in sorted(files):
            self.scn_selector.addItem(f, os.path.join(scn_dir, f))

    def _run_selected_scn(self):
        """Run the selected .scn file with 'do' command."""
        if not self.conn:
            print("No SPEC connection.")
            return
        path = self.scn_selector.currentData()
        if path and os.path.isfile(path):
            try:
                self.conn.sendCommand(f'do "{path}"')
                print(f"Running {path}")
            except Exception as e:
                print(f"Error running {path}: {e}")
        else:
            print("No valid .scn file selected.")

    def _open_scan_builder(self):
        dlg = ScanBuilderDialog(self)
        dlg.set_connection(self.conn)
        if hasattr(self, "motormnes") and self.motormnes:
            try:
                dlg.scan_widget.setMotors(self.motormnes, self.datablock.getAliases())
            except Exception:
                pass
        dlg.exec()
        # Refresh list after builder closes
        self._populate_scn_files()


def test():
    import sys
    from SpecDataConnection import SpecDataConnection

    app = QApplication([])
    win = QMainWindow()

    spec_c = SpecDataConnection(sys.argv[1])

    panel = ServerPanel()
    panel.set_connection(spec_c)

    panel.setMotors(['th', 'chi', 'phi'])

    win.setCentralWidget(panel)
    win.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    test()
