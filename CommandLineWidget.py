# gui/widgets/CommandLineWidget.py
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QToolButton, QMenu, QLabel, QFrame
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QEvent

from pyspec.css_logger import log


class CommandLineWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.conn = None
        self._history = []
        self._hist_idx = -1

        self.setObjectName("SpecCommandLine")
        self.setStyleSheet("""
        QFrame#SpecCommandLine {
            background: #f7f7f9;
            border: 1px solid #cfcfd4;
            border-radius: 8px;
        }
        QLabel#Prompt {
            color:#666;
            padding-right:6px;
            font-size: 10pt;
        }
        QLineEdit#CmdInput {
            border: none;
            padding: 3px 6px;     /* was 6px 8px */
            background: transparent;
            font-size: 10pt;      /* keep readable but compact */
        }
        QPushButton#SendBtn, QToolButton#HistBtn {
            border: none;
            border-left: 1px solid #d9d9de;
            padding: 4px 8px;      /* was 6px 12px */
            font-size: 10pt;
        }
        QPushButton#SendBtn:hover, QToolButton#HistBtn:hover {
            background: #ececf1;
        }
        """)
        self.setMaximumHeight(34)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 2, 8, 2)  # was (8,4,8,4)
        row.setSpacing(0)

        self.prompt = QLabel("")
        self.prompt.setStyleSheet("color:#666; padding-right:8px;")
        # row.addWidget(self.prompt, 0, Qt.AlignVCenter)

        self.input = QLineEdit()
        self.input.setObjectName("CmdInput")
        self.input.setPlaceholderText("Enter SPEC command ...")
        self.input.returnPressed.connect(self._send_current)
        row.addWidget(self.input, 1)

        self.hist_btn = QToolButton()
        self.hist_btn.setObjectName("HistBtn")
        self.hist_btn.setText("History")
        self.hist_btn.setPopupMode(QToolButton.InstantPopup)
        self.hist_menu = QMenu(self.hist_btn)
        self.hist_btn.setMenu(self.hist_menu)
        # row.addWidget(self.hist_btn, 0)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("SendBtn")
        self.send_btn.clicked.connect(self._send_current)
        row.addWidget(self.send_btn, 0)

        self.input.installEventFilter(self)

    # Public API
    def set_connection(self, conn):
        self.conn = conn

    # Core send path (no GUI controller)
    def _send(self, cmd: str):
        try:
            if self.conn is not None and hasattr(self.conn, "sendCommand"):
                self.conn.sendCommand(cmd)
            elif self.conn is not None and hasattr(self.conn, "send"):
                self.conn.send(cmd)
            else:
                from gans_control.backend.session.spec_session import spec_controller
                spec_controller.send(cmd)
        except Exception as e:
            log.log(2, f"Command send failed: {e}")

    # UI helpers
    def _send_current(self):
        cmd = self.input.text().strip()
        if not cmd:
            return
        self._remember(cmd)
        self._send(cmd)
        self.input.clear()
        self._hist_idx = -1

    def _remember(self, cmd: str):
        if not self._history or self._history[-1] != cmd:
            self._history.append(cmd)
        self._rebuild_history_menu()

    def _rebuild_history_menu(self):
        self.hist_menu.clear()
        # Most recent first
        for txt in reversed(self._history[-25:]):
            act = QAction(txt, self.hist_menu)
            act.triggered.connect(lambda _=False, t=txt: self._select_history(t))
            self.hist_menu.addAction(act)

    def _select_history(self, text: str):
        self.input.setText(text)
        self.input.setCursorPosition(len(text))
        self.input.setFocus()

    # Up/Down to traverse history
    def eventFilter(self, obj, ev):
        if obj is self.input and ev.type() == QEvent.KeyPress:
            key = ev.key()
            if key in (Qt.Key_Up, Qt.Key_Down):
                if not self._history:
                    return False
                if key == Qt.Key_Up:
                    if self._hist_idx == -1:
                        self._hist_idx = len(self._history) - 1
                    else:
                        self._hist_idx = max(0, self._hist_idx - 1)
                else:
                    if self._hist_idx == -1:
                        return True
                    self._hist_idx += 1
                    if self._hist_idx >= len(self._history):
                        self._hist_idx = -1
                        self.input.clear()
                        return True
                if self._hist_idx != -1:
                    self.input.setText(self._history[self._hist_idx])
                    self.input.setCursorPosition(len(self.input.text()))
                return True
        return super().eventFilter(obj, ev)
