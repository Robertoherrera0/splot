from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QDialog, QAbstractScrollArea
from PySide6.QtCore import Qt, QTimer
from pyspec.client import SpecConnection

class LiveScanTable(QWidget):
    def __init__(self, specname="twoc", parent=None):
        super().__init__(parent)
        self.setObjectName("LiveScanTable")

        # direct connection to SPEC
        self.conn = SpecConnection(specname)

        self._visible_columns = []
        self._column_indices = []
        self._last_npts = 0
        self._scan_id = None

        self._init_ui()
        self._start_polling()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setShowGrid(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(True)
        layout.addWidget(self.table)

    def _start_polling(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_data)
        self._timer.start(250)

    def _refresh_data(self):
        try:
            scan = self.conn.get_scan()
            if not scan or "columns" not in scan or "data" not in scan:
                return

            full_columns = scan["columns"]
            data = scan["data"]
            npts = len(data)

            visible_columns = [c for c in full_columns if c not in {"H", "K", "epoch"}]
            if "sec" in visible_columns and "det" in visible_columns:
                sec_idx, det_idx = visible_columns.index("sec"), visible_columns.index("det")
                visible_columns[sec_idx], visible_columns[det_idx] = visible_columns[det_idx], visible_columns[sec_idx]

            indices = [full_columns.index(c) for c in visible_columns]
            scan_id = (scan.get("number"), scan.get("timestamp"))

            if self._scan_id != scan_id or visible_columns != self._visible_columns or (self._last_npts and npts < self._last_npts):
                self._scan_id = scan_id
                self._reset_table(visible_columns, indices)

            if npts > self._last_npts:
                for i in range(self._last_npts, npts):
                    row = [data[i][j] for j in self._column_indices]
                    self._insert_row(row, i)
                self._last_npts = npts

        except Exception as e:
            print(f"[LiveScanTable] refresh failed: {e}")

    def _reset_table(self, visible_columns, indices):
        self._visible_columns = visible_columns
        self._column_indices = indices
        self.table.clear()
        self.table.setColumnCount(len(visible_columns))
        self.table.setHorizontalHeaderLabels(visible_columns)
        self.table.setRowCount(0)
        self._last_npts = 0

    def _insert_row(self, values, row_number):
        self.table.insertRow(row_number)
        for col_idx, val in enumerate(values):
            text = f"{val:.3f}" if isinstance(val, (int, float)) else str(val)
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_number, col_idx, item)

        hdr = QTableWidgetItem(str(row_number + 1))
        hdr.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setVerticalHeaderItem(row_number, hdr)
