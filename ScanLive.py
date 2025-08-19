from typing import Optional, List, Tuple, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer

# Import the class, not the module
try:
    from pyspec.client.SpecConnection import SpecConnection
except Exception:
    from pyspec.client import SpecConnection  # fallback if re-exported


class LiveScanTable(QWidget):
    def __init__(self, parent: Optional[QWidget] = None,
                 specname: str = "twoc",
                 conn: Optional["SpecConnection"] = None):
        super().__init__(parent)
        self.conn = conn if conn is not None else SpecConnection(specname)

        self._visible_columns: List[str] = []
        self._column_indices: List[int] = []
        self._last_npts: int = 0
        self._scan_id: Optional[Tuple[Any, Any]] = None

        self._init_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_data)
        self._timer.start(250)

    def set_connection(self, conn) -> None:
        self.conn = conn
        self._reset_table([], [])
        if not self._timer.isActive():
            self._timer.start(250)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setShowGrid(True)
        self.table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(True)

        layout.addWidget(self.table)
        self.setMinimumHeight(140)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)

    def _extract_payload(self, scan: dict) -> Tuple[List[str], List[list], dict]:
        payload = scan.get("scan_data") if isinstance(scan, dict) else None
        if payload is None and isinstance(scan, dict):
            payload = scan
        cols = payload.get("columns") or payload.get("cols") or []
        data = payload.get("data") or payload.get("points") or []
        return list(cols), data, payload

    def _refresh_data(self) -> None:
        if not self.conn:
            return
        try:
            scan = self.conn.get_scan()
            if not scan:
                return

            full_columns, data, payload = self._extract_payload(scan)
            if not full_columns or not isinstance(data, list):
                return

            npts = len(data)

            visible_columns = [c for c in full_columns if c not in {"H", "K", "epoch"}]
            if "sec" in visible_columns and "det" in visible_columns:
                i, j = visible_columns.index("sec"), visible_columns.index("det")
                visible_columns[i], visible_columns[j] = visible_columns[j], visible_columns[i]

            indices = [full_columns.index(c) for c in visible_columns]

            scan_id = (
                payload.get("number") or payload.get("scanno"),
                payload.get("timestamp") or payload.get("date")
            )

            if (
                self._scan_id != scan_id
                or visible_columns != self._visible_columns
                or (self._last_npts and npts < self._last_npts)
            ):
                self._scan_id = scan_id
                self._reset_table(visible_columns, indices)

            if npts > self._last_npts:
                for i in range(self._last_npts, npts):
                    row = [data[i][j] for j in self._column_indices]
                    self._insert_row(row, i)
                self._last_npts = npts

        except Exception as e:
            print(f"[LiveScanTable] refresh failed: {e}")

    def _reset_table(self, visible_columns: List[str], indices: List[int]) -> None:
        self._visible_columns = visible_columns
        self._column_indices = indices
        self.table.clear()
        self.table.setColumnCount(len(visible_columns))
        if visible_columns:
            self.table.setHorizontalHeaderLabels(visible_columns)
        self.table.setRowCount(0)
        self._last_npts = 0
        self.table.resizeColumnsToContents()

    def _insert_row(self, values: list, row_number: int) -> None:
        self.table.insertRow(row_number)
        for col_idx, val in enumerate(values):
            if isinstance(val, (int, float)):
                text = f"{val:.6g}"
            else:
                text = "" if val is None else str(val)
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_number, col_idx, item)

        hdr = QTableWidgetItem(str(row_number + 1))
        hdr.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setVerticalHeaderItem(row_number, hdr)
