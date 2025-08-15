# gui/widgets/ScanRunnerWidget.py
from __future__ import annotations

import os
import sys
import subprocess

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QComboBox, QPushButton, QToolButton, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from pyspec.css_logger import log
import icons


from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QComboBox, QPushButton, QToolButton, QFrame as QSeparator, QWidget
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QDesktopServices
import os, sys, subprocess

import icons
from pyspec.css_logger import log


class ScanRunnerWidget(QFrame):
    def __init__(self, parent: QWidget | None = None, scan_dir: str | None = None):
        super().__init__(parent)

        self.conn = None
        self._scan_dir = scan_dir or os.path.expanduser("~/.gans-control/generated_spec/last_run")

        self.setObjectName("ScanRunnerLine")
        self.setStyleSheet("""
        QFrame#ScanRunnerLine {
            background: #f7f7f9;
            border: 1px solid #cfcfd4;
            border-radius: 8px;
        }
        QComboBox#FileCombo {
            border: none;
            padding: 3px 6px;
            background: transparent;
            font-size: 10pt;
        }
        QPushButton#BuilderBtn, QPushButton#RunBtn, QToolButton#FolderBtn {
            border: none;
            padding: 4px 8px;
            font-size: 10pt;
        }
        QPushButton#RunBtn, QToolButton#FolderBtn {
            border-left: 1px solid #d9d9de;
        }
        QPushButton#BuilderBtn {
            border-right: 1px solid #d9d9de; /* separator after builder */
        }
        QPushButton#BuilderBtn:hover, QPushButton#RunBtn:hover, QToolButton#FolderBtn:hover {
            background: #ececf1;
        }
        """)
        self.setMaximumHeight(34)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 2, 8, 2)
        row.setSpacing(0)

        # Builder button
        self.builder_btn = QPushButton("Open Scan Builder")
        self.builder_btn.setObjectName("BuilderBtn")
        self.builder_btn.clicked.connect(self._open_builder)
        row.addWidget(self.builder_btn, 0)

        # File selector
        self.scn_selector = QComboBox()
        self.scn_selector.setObjectName("FileCombo")
        row.addWidget(self.scn_selector, 1, Qt.AlignVCenter)

        # Run button
        self.run_btn = QPushButton("Run")
        self.run_btn.setObjectName("RunBtn")
        self.run_btn.clicked.connect(self.run_selected)
        row.addWidget(self.run_btn, 0, Qt.AlignVCenter)

        # Folder button
        self.folder_btn = QToolButton()
        self.folder_btn.setObjectName("FolderBtn")
        self.folder_btn.setIcon(icons.get_icon('folder'))
        self.folder_btn.setToolTip("Open scan directory")
        self.folder_btn.clicked.connect(self._open_dir)
        row.addWidget(self.folder_btn, 0, Qt.AlignVCenter)

        self.refresh_files()


    def set_connection(self, conn):
        self.conn = conn

    def set_scan_dir(self, path: str):
        self._scan_dir = path
        self.refresh_files()

    def refresh_files(self):
        self.scn_selector.clear()
        if not os.path.isdir(self._scan_dir):
            self.scn_selector.addItem("(no .scn file)", None)
            return
        files = [f for f in os.listdir(self._scan_dir) if f.lower().endswith(".scn")]
        if not files:
            self.scn_selector.addItem("(no .scn file)", None)
            return
        files.sort(key=lambda f: os.path.getmtime(os.path.join(self._scan_dir, f)), reverse=True)
        for f in files:
            full = os.path.join(self._scan_dir, f)
            self.scn_selector.addItem(f, full)
        self.scn_selector.setCurrentIndex(0)

    def run_selected(self):
        path = self.scn_selector.currentData()
        if not path:
            log.log(2, "No .scn file selected")
            return
        self._send(f'qdo "{path}"')

    def _open_builder(self):
        p = self.parent()
        while p is not None:
            if hasattr(p, "_open_scan_builder"):
                try:
                    p._open_scan_builder()
                    return
                except Exception as e:
                    log.log(2, f"Open builder failed: {e}")
                    return
            p = p.parent()
            
    def _open_dir(self):
        # bubble up until we find parent's _open_scan_builder()
        p = self.parent()
        while p is not None:
            if hasattr(p, "_open_scan_builder"):
                try:
                    p._open_scan_builder()
                except Exception as e:
                    log.log(2, f"Open builder failed: {e}")
                return


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
            log.log(2, f"ScanRunner send failed: {e}")
