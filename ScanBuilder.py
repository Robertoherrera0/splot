# File: /usr/local/lib/spec.d/splot/ScanBuilderDialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QWidget, QLineEdit, QPushButton,
    QListView, QFileDialog, QLabel, QToolButton, QMessageBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QItemSelectionModel, QDateTime

import os
import tempfile
import pathlib

# Import SPlot's ScanWidget directly
from ScanWidget import ScanWidget


class CommandListModel(QStandardItemModel):
    def flags(self, index):
        base = super().flags(index)
        if not index.isValid():
            return Qt.ItemIsEnabled | Qt.ItemIsDropEnabled
        return base | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled


class ScanBuilderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Builder")
        self.setMinimumSize(980, 580)

        self._conn = None
        self._header = {
            "title": "untitled_experiment",
            "guest": "",
            "group": "",
            "comment": "",
        }

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # --- Top bar ---
        top = QHBoxLayout()
        top.setSpacing(8)
        self.title_edit = QLineEdit(self._header["title"])
        self.guest_edit = QLineEdit()
        self.group_edit = QLineEdit()
        self.comment_edit = QLineEdit()
        self.save_btn = QPushButton("Save .scn")
        self.run_btn = QPushButton("Run Sequence")

        for lbl_text, widget in [
            ("Title:", self.title_edit),
            ("Guest:", self.guest_edit),
            ("Group:", self.group_edit),
            ("Comment:", self.comment_edit),
        ]:
            top.addWidget(QLabel(lbl_text))
            top.addWidget(widget, 1)

        top.addWidget(self.save_btn)
        top.addWidget(self.run_btn)
        root.addLayout(top)

        # --- Splitter ---
        split = QSplitter(Qt.Horizontal)
        root.addWidget(split, 1)

        # --- Left panel: Scan widget + adders ---
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.scan_widget = ScanWidget()
        left_layout.addWidget(self.scan_widget, 1)

        cmd_row = QHBoxLayout()
        self.raw_cmd = QLineEdit()
        self.raw_cmd.setPlaceholderText("Raw SPEC command")
        self.add_cmd_btn = QPushButton("Add")
        cmd_row.addWidget(self.raw_cmd, 1)
        cmd_row.addWidget(self.add_cmd_btn)
        left_layout.addLayout(cmd_row)

        cmt_row = QHBoxLayout()
        self.inline_comment = QLineEdit()
        self.inline_comment.setPlaceholderText("Inline comment (#### ...)")
        self.add_cmt_btn = QToolButton()
        self.add_cmt_btn.setText("Insert")
        cmt_row.addWidget(self.inline_comment, 1)
        cmt_row.addWidget(self.add_cmt_btn)
        left_layout.addLayout(cmt_row)

        split.addWidget(left)

        # --- Right panel: sequence list ---
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Sequence"), 1)
        self.up_btn = QToolButton(); self.up_btn.setText("Up")
        self.down_btn = QToolButton(); self.down_btn.setText("Down")
        self.del_btn = QToolButton(); self.del_btn.setText("Delete")
        self.clear_btn = QToolButton(); self.clear_btn.setText("Clear")
        for btn in (self.up_btn, self.down_btn, self.del_btn, self.clear_btn):
            header_row.addWidget(btn)
        right_layout.addLayout(header_row)

        self.list_view = QListView()
        self.list_view.setEditTriggers(QListView.DoubleClicked | QListView.EditKeyPressed)
        self.list_view.setDragDropMode(QListView.InternalMove)
        self.list_view.setDefaultDropAction(Qt.MoveAction)
        self.list_view.setSelectionMode(QListView.ExtendedSelection)

        self.model = CommandListModel()
        self.list_view.setModel(self.model)
        right_layout.addWidget(self.list_view, 1)

        bottom = QHBoxLayout()
        self.close_btn = QPushButton("Close")
        bottom.addStretch(1)
        bottom.addWidget(self.close_btn)
        right_layout.addLayout(bottom)

        split.addWidget(right)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)

        # --- Wire up ---
        self.add_cmd_btn.clicked.connect(self._add_raw_command)
        self.add_cmt_btn.clicked.connect(self._insert_inline_comment)
        self.up_btn.clicked.connect(self._move_up)
        self.down_btn.clicked.connect(self._move_down)
        self.del_btn.clicked.connect(self._delete_selected)
        self.clear_btn.clicked.connect(self._clear_all)
        self.save_btn.clicked.connect(self._save_to_file_dialog)
        self.run_btn.clicked.connect(self._run_sequence)
        self.close_btn.clicked.connect(self.accept)

    def set_connection(self, spec_connection):
        self._conn = spec_connection
        try:
            self.scan_widget.set_connection(spec_connection)
        except Exception:
            pass

    def _append_line(self, text):
        if text:
            it = QStandardItem(text)
            it.setEditable(True)
            self.model.appendRow(it)

    def _insert_inline_comment(self):
        txt = self.inline_comment.text().strip()
        if txt:
            if not txt.startswith("####"):
                txt = "#### " + txt
            self._append_line(txt)
            self.inline_comment.clear()

    def _add_raw_command(self):
        cmd = self.raw_cmd.text().strip()
        if cmd:
            cmt = self.inline_comment.text().strip()
            if cmt:
                if not cmt.startswith("####"):
                    cmt = "#### " + cmt
                self._append_line(cmt)
                self.inline_comment.clear()
            self._append_line(cmd)
            self.raw_cmd.clear()

    def _collect_lines(self):
        return [self.model.item(r, 0).text().rstrip()
                for r in range(self.model.rowCount()) if self.model.item(r, 0).text().strip()]

    def _write_scn(self, path):
        header = self._render_header_block()
        body = "\n".join(self._collect_lines())
        text = header + ("\n" if body else "") + body + "\n"
        pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def _render_header_block(self):
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        lines = [
            "#### =========================================",
            f"#### Title: {self._header['title']}",
        ]
        if self._header.get("guest"):
            lines.append(f"#### Guest: {self._header['guest']}")
        if self._header.get("group"):
            lines.append(f"#### Group: {self._header['group']}")
        if self._header.get("comment"):
            lines.append(f"#### Comment: {self._header['comment']}")
        lines.append(f"#### Created: {now}")
        lines.append("#### =========================================")
        return "\n".join(lines)

    def _save_to_file_dialog(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Scan Sequence", "", "SPEC scan files (*.scn)")
        if path:
            if not path.lower().endswith(".scn"):
                path += ".scn"
            self._write_scn(path)
            QMessageBox.information(self, "Saved", f"Saved sequence:\n{path}")

    def _run_sequence(self):
        if not self._conn:
            QMessageBox.warning(self, "No Connection", "No SPEC connection is set.")
            return
        try:
            tmpdir = tempfile.mkdtemp(prefix="scanbuilder_")
            tmppath = os.path.join(tmpdir, "sequence.scn")
            self._write_scn(tmppath)
            self._conn.sendCommand(f'qdo "{tmppath}"')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run sequence:\n{e}")

    def _move_up(self):
        rows = sorted([i.row() for i in self.list_view.selectionModel().selectedRows()])
        for r in rows:
            if r > 0:
                self.model.insertRow(r - 1, self.model.takeRow(r))

    def _move_down(self):
        rows = sorted([i.row() for i in self.list_view.selectionModel().selectedRows()], reverse=True)
        for r in rows:
            if r < self.model.rowCount() - 1:
                self.model.insertRow(r + 1, self.model.takeRow(r))

    def _delete_selected(self):
        for r in sorted([i.row() for i in self.list_view.selectionModel().selectedRows()], reverse=True):
            self.model.removeRow(r)

    def _clear_all(self):
        self.model.clear()
