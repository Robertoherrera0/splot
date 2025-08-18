#******************************************************************************
#
#  @(#)MotorWidget.py	3.5  12/13/20 CSS
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

from pyspec.graphics.QVariant import *

from pyspec.client import SpecMotor 
from pyspec.css_logger import log

from StopButton import StopButton


# class MotorWidget(QWidget):

#     def __init__(self, motmne=None, spec=None, *args):

#         self.motor = None # added
#         self.modified = False
#         self._position = None
#         self.motmne = motmne

#         self.state = SpecMotor.NOTINITIALIZED

#         self.is_shown = False

#         QWidget.__init__(self)

#         motorLayout = QHBoxLayout()
#         motorLayout.setSpacing(3)
#         motorLayout.setContentsMargins(1, 1, 1, 1)
#         motorLayout.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

#         # self.setLayout(motorLayout)

#         # Create widgets unconditionally so they always exist
#         self.motorLabel = QLabel()
#         font = self.motorLabel.font()
#         font.setBold(True)
#         self.motorLabel.setFont(font)

#         if not self.motmne or not spec:
#             return

#         cb = {'motorPositionChanged': self.motor_position_changed,
#               'motorStateChanged': self.motor_state_changed}

#         if None not in (motmne, spec):
#             self.motor = SpecMotor.SpecMotorA(spec, motmne, callbacks=cb)
#         else:
#             self.motor = None

#         motorLayout = QHBoxLayout()
#         motorLayout.setSpacing(3)
#         motorLayout.setContentsMargins(1, 1, 1, 1)
#         motorLayout.setAlignment(
#             Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

#         self.setLayout(motorLayout)

#         self.motorLabel = QLabel()
#         font = self.motorLabel.font()
#         font.setBold(True)
#         self.motorLabel.setFont(font)

#         self.currentLabel = QLabel()
#         self.currentLabel.setFixedWidth(70)

#         self.moveValue = QLineEdit()
#         self.moveValue.setFixedWidth(70)
#         self.moveValue.returnPressed.connect(self.doMove)
#         self.moveValue.textEdited.connect(self.positionEdited)

#         self.goButton = QPushButton("Go")
#         self.goButton.setFixedWidth(50)
#         self.goButton.clicked.connect(self.doMove)

#         self.cancelButton = QPushButton("Cancel")
#         self.cancelButton.setFixedWidth(50)
#         self.cancelButton.clicked.connect(self.cancelMove)
#         self.cancelButton.setEnabled(False)

#         self.stopButton = StopButton()
#         self.stopButton.setFixedWidth(50)
#         self.stopButton.clicked.connect(self.stop)

#         self.mspacer = QWidget()
#         self.mspacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         motorLayout.addWidget(self.motorLabel)
#         motorLayout.addWidget(self.moveValue)
#         motorLayout.addWidget(self.goButton)
#         motorLayout.addWidget(self.cancelButton)
#         #motorLayout.addWidget(self.stopButton)
#         motorLayout.addWidget(self.mspacer)

#         self.update()
class MotorWidget(QWidget):
    def __init__(self, motmne=None, spec=None, *args):
        super().__init__()

        self.motor = None
        self.modified = False
        self._position = None
        self.motmne = motmne
        self.state = SpecMotor.NOTINITIALIZED
        self.is_shown = False
        self.move_mode = "absolute"  # default

        self.setStyleSheet("""
            QLabel { font-family: 'IBM Plex Sans','Segoe UI',sans-serif; font-size:10pt; color:#2b2b2b; }
            QLineEdit { font-size:10pt; font-family:'IBM Plex Sans','Segoe UI',sans-serif; border:1px solid #dcdfe3; border-radius:4px; padding:2px 4px; background-color:#ffffff; }
            QPushButton { font-size:9.5pt; font-family:'IBM Plex Sans','Segoe UI',sans-serif; padding:2px 8px; border:1px solid #c0c0c0; border-radius:4px; background-color:#f5f5f5; }
            QPushButton:hover { background-color:#e6e6e6; }
        """)

        motorLayout = QHBoxLayout()
        motorLayout.setSpacing(6)
        motorLayout.setContentsMargins(4, 2, 4, 2)
        motorLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setLayout(motorLayout)

        # Motor label
        self.motorLabel = QLabel()
        font = self.motorLabel.font()
        font.setBold(True)
        self.motorLabel.setFont(font)

        self.currentLabel = QLabel()
        self.currentLabel.setFixedWidth(70)

        # --- NEW: mode dropdown (Abs/Rel) ---
        self.modeCombo = QComboBox()
        self.modeCombo.addItem("Absolute", userData="absolute")
        self.modeCombo.addItem("Relative", userData="relative")
        self.modeCombo.currentIndexChanged.connect(self._modeChanged)

        self.moveValue = QLineEdit()
        self.moveValue.setFixedWidth(70)
        self.moveValue.returnPressed.connect(self.doMove)
        self.moveValue.textEdited.connect(self.positionEdited)

        self.goButton = QPushButton("Move")
        self.goButton.setFixedWidth(50)
        self.goButton.clicked.connect(self.doMove)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.setFixedWidth(60)
        self.cancelButton.clicked.connect(self.cancelMove)
        self.cancelButton.setEnabled(False)

        self.stopButton = StopButton()
        self.stopButton.setFixedWidth(50)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Layout: (Label) (Curr?) (Mode dropdown) (Input) (Go) (Cancel) ......
        motorLayout.addWidget(self.motorLabel)
        motorLayout.addWidget(self.currentLabel)
        motorLayout.addWidget(self.modeCombo)
        motorLayout.addWidget(self.moveValue)
        motorLayout.addWidget(self.goButton)
        motorLayout.addWidget(self.cancelButton)
        motorLayout.addWidget(spacer)

        if motmne and spec:
            cb = {
                'motorPositionChanged': self.motor_position_changed,
                'motorStateChanged': self.motor_state_changed
            }
            self.motor = SpecMotor.SpecMotorA(spec, motmne, callbacks=cb)

        self.update()

    # --- Mode handling ---
    def _modeChanged(self, idx: int):
        self.setMoveMode(self.modeCombo.itemData(idx) or "absolute")

    def setMoveMode(self, mode: str):
        self.move_mode = "relative" if (mode or "").lower().startswith("rel") else "absolute"

    # --- The rest is unchanged except doMove() ---
    def stop(self):
        if self.motor is not None:
            self.motor.stop()

    def positionEdited(self, value):
        try:
            float(value)
            self.goButton.setDisabled(False)
        except:
            self.goButton.setDisabled(True)
        self.setModified(True)

    def setModified(self, flag):
        self.modified = flag
        self.cancelButton.setEnabled(flag)
        self.moveValue.setStyleSheet("background-color: #ccccff;")
        self.update()

    def setTargetPosition(self, position, modified=True):
        self.moveValue.setText("%0.4g" % float(position))
        if modified:
            self.positionEdited(position)

    def setCurrentPosition(self, position):
        self._position = position
        self.update()

    def update(self):
        if not self.is_shown:
            return

        self.motorLabel.setText(self.motmne)

        self.blockSignals(True)

        if self.modified:
            return

        if self.motor is None:
            self.blockSignals(False)
            return

        if self._position is None:
            self._position = self.motor.get_position()

        # show current absolute position in the input
        self.moveValue.setText("%0.4g" % self._position)
        # optionally also mirror in the label if you want:
        # self.currentLabel.setText("%0.4g" % self._position)

        if self.state in [SpecMotor.MOVING, SpecMotor.MOVESTARTED]:
            self.moveValue.setStyleSheet("background-color: #f0f033;")
            self.disable()
        elif self.state in [SpecMotor.UNUSABLE, SpecMotor.NOTINITIALIZED]:
            self.moveValue.setStyleSheet("background-color: #f033f0;")
            self.disable()
        elif self.state in [SpecMotor.READY, SpecMotor.ONLIMIT]:
            self.moveValue.setStyleSheet("background-color: #ffffff;")
            self.enable()
        self.blockSignals(False)

    def motor_position_changed(self, newpos):
        self.setCurrentPosition(newpos)
        self.update()

    def motor_state_changed(self, state):
        self.state = state
        self.update()

    def hideEvent(self, ev):
        self.is_shown = False
        QWidget.hideEvent(self, ev)

    def showEvent(self, event):
        self.is_shown = True
        self.update()
        QWidget.showEvent(self, event)

    def enable(self):
        self.goButton.setDisabled(False)
        self.stopButton.setActive(False)

    def disable(self):
        self.goButton.setDisabled(True)
        self.stopButton.setActive(True)

    def stopMotor(self):
        log.log(3, "Stopping from motorWidget")
        self.motor.abort()

    def doMove(self):
        try:
            delta_or_abs = float(self.moveValue.text())
            if self.move_mode == "relative":
                # Safer than SpecMotor.move_relative in your version:
                target = self.motor.get_position() + delta_or_abs
                self.motor.move(target)
            else:
                self.motor.move(delta_or_abs)
            self.setModified(False)
        except BaseException:
            import traceback
            log.log(2, "cannot do move. %s" % traceback.format_exc())

    def cancelMove(self):
        self.setModified(False)
