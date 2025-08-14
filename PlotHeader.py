# PlotHeader.py — two-tier centered header with detector dropdown

import re, copy
from pyspec.graphics.QVariant import (
    QWidget, Qt, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QComboBox,
    QApplication, QMainWindow
)
from Preferences import Preferences
from Constants import *
import themes


def _font(w, size=10, bold=False):
    f = w.font()
    f.setFamily("IBM Plex Sans")
    f.setPointSize(size)
    f.setBold(bold)
    w.setFont(f)


class Token(QWidget):
    def __init__(self, key, color="#1E1E1E"):
        super().__init__()
        lo = QHBoxLayout(self)
        lo.setContentsMargins(8, 2, 8, 2)
        lo.setSpacing(6)
        self.k = QLabel(key)
        self.v = QLabel("")
        _font(self.k, 10, False)
        _font(self.v, 10, False)
        self.k.setStyleSheet("color:#667085;")
        self.v.setStyleSheet(f"color:{color};")
        lo.addWidget(self.k)
        lo.addWidget(self.v)

    def set_value(self, text):
        self.v.setText(text)


class PlotHeader(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)

        self.dataBlock = None
        self.title = ""
        self.hkl_text = ""
        self.stats_text = ""
        self.columns = []
        self.selected_column = None
        self.prefs = Preferences()

        theme = themes.get_theme(self.prefs["theme"]) or object()
        peak_c = getattr(theme, "marker_color_peak", "#1E1E1E")
        com_c  = getattr(theme, "marker_color_com",  "#1E1E1E")
        fwhm_c = getattr(theme, "marker_color_fwhm", "#1E1E1E")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # Top row (centered): scan number | command (10pt, same as tokens)
        self.top_num = QLabel("")
        self.top_sep = QLabel("|")
        self.top_cmd = QLabel("")
        _font(self.top_num, 10, False)
        _font(self.top_sep, 10, False)
        _font(self.top_cmd, 10, False)
        self.top_cmd.setTextInteractionFlags(Qt.TextSelectableByMouse)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)
        top_row.addStretch(1)
        top_row.addWidget(self.top_num, 0, Qt.AlignCenter)
        top_row.addWidget(self.top_sep, 0, Qt.AlignCenter)
        top_row.addWidget(self.top_cmd, 0, Qt.AlignCenter)
        top_row.addStretch(1)
        root.addLayout(top_row)

        # Horizontal divider
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setStyleSheet("color:#ECEEF0;")
        root.addWidget(hline)

        # Bottom row (centered):  HKL block | vline | stats block … [detector combo]
        self.t_hkl  = Token("HKL")
        self.t_peak = Token("Peak", peak_c)
        self.t_com  = Token("COM",  com_c)
        self.t_fwhm = Token("FWHM", fwhm_c)

        self.left_block = QHBoxLayout()
        self.left_block.setContentsMargins(0, 0, 0, 0)
        self.left_block.setSpacing(10)
        self.left_block.addWidget(self.t_hkl)

        self.right_block = QHBoxLayout()
        self.right_block.setContentsMargins(0, 0, 0, 0)
        self.right_block.setSpacing(10)
        self.right_block.addWidget(self.t_peak)
        self.right_block.addWidget(self.t_com)
        self.right_block.addWidget(self.t_fwhm)

        self.vline = QFrame()
        self.vline.setFrameShape(QFrame.VLine)
        self.vline.setStyleSheet("color:#ECEEF0;")

        # Detector dropdown (appears only when >1 Y columns)
        self.columnCombo = QComboBox()
        _font(self.columnCombo, 10, False)
        self.columnCombo.hide()
        self.columnCombo.currentIndexChanged.connect(self._column_changed)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(12)
        bottom_row.addStretch(1)
        bottom_row.addLayout(self.left_block)
        bottom_row.addWidget(self.vline)
        bottom_row.addLayout(self.right_block)
        bottom_row.addSpacing(8)
        bottom_row.addWidget(self.columnCombo)
        bottom_row.addStretch(1)
        root.addLayout(bottom_row)

        # Initial visibility
        self.t_hkl.hide()
        self.t_peak.hide()
        self.t_com.hide()
        self.t_fwhm.hide()
        self._update_vdivider()

    # ===== SPEC hooks =====
    def setDataBlock(self, datablock):
        if not datablock:
            return
        if self.dataBlock and (self.dataBlock is not datablock):
            self.dataBlock.unsubscribe(self)
        self.dataBlock = datablock
        self.dataBlock.subscribe(self, STATS_UPDATED, self._updateStats)
        self.dataBlock.subscribe(self, Y_SELECTION_CHANGED, self._updateColumns)
        self.dataBlock.subscribe(self, TITLE_CHANGED, self.setTitle)

    def setStatistics(self, stats):
        self._updateStats(stats)

    def getSelectedColumn(self):
        return self.selected_column

    def selectColumn(self, column):
        if not self.columns:
            return
        self._selectColumn(column)
        if column in self.columns:
            self.columnCombo.setCurrentIndex(self.columns.index(column))

    def getTitle(self):
        ret = self.title
        if self.hkl_text:
            ret += "\n" + self.hkl_text
        if self.stats_text:
            ret += "\n" + self.stats_text
        return ret

    # ===== Internals =====
    def _parse_title(self, title):
        m = re.match(r"\s*Scan\s+(\d+)\s*-\s*(.*)$", title)
        return (m.group(1), m.group(2)) if m else ("", title)

    def setTitle(self, title):
        self.title = title
        num, cmd = self._parse_title(title)
        self.top_num.setText(num)
        self._set_cmd(cmd)

        hkl_value = self.dataBlock.getMetaData("HKL") if self.dataBlock else None
        if hkl_value:
            vals = "   ".join(["%g" % v for v in map(float, hkl_value.split())])
            self.t_hkl.set_value(vals)
            self.t_hkl.show()
            self.hkl_text = f"HKL: {vals}"
        else:
            self.t_hkl.hide()
            self.hkl_text = ""

        self._update_vdivider()
        self._elide_top_cmd()

    def _updateColumns(self, columns):
        # Called when Y selection changes; show combo if multiple columns.
        columns = columns or []
        if columns == self.columns:
            return
        self.columns = copy.copy(columns)
        self.columnCombo.clear()
        if len(self.columns) > 1:
            self.columnCombo.addItems(self.columns)
            self.columnCombo.show()
            # Keep or set a valid selection
            if self.selected_column not in self.columns:
                self._selectColumn(self.columns[0])
            # Reflect in combo box
            try:
                self.columnCombo.setCurrentIndex(self.columns.index(self.selected_column))
            except Exception:
                pass
        else:
            self.columnCombo.hide()
            if self.columns:
                self._selectColumn(self.columns[0])

    def _selectColumn(self, column):
        self.selected_column = column
        if self.dataBlock and column in (self.columns or []):
            self.dataBlock.setActiveColumn(column)

    def _column_changed(self, idx):
        if 0 <= idx < len(self.columns):
            self.selectColumn(self.columns[idx])

    def _updateStats(self, s):
        # Hide all tokens by default; show only available
        self.t_peak.hide()
        self.t_com.hide()
        self.t_fwhm.hide()
        self.stats_text = ""

        if not s:
            self._update_vdivider()
            return

        if s.get("2d", False):
            # 2D mode: show Max and Sum
            peak_val = s.get("peak", "")
            if isinstance(peak_val, (int, float)):
                self.t_peak.k.setText("Max")
                self.t_peak.set_value(f"{peak_val:.4g}")
                self.t_peak.show()
            if "sum" in s:
                self.t_fwhm.k.setText("Sum")
                self.t_fwhm.set_value(f"{s['sum']:.2g}")
                self.t_fwhm.show()
            self.stats_text = f"2D: max {peak_val}; sum {s.get('sum','')}"
            self._update_vdivider()
            return

        if s.get("column") != self.selected_column:
            self._update_vdivider()
            return

        pk_pos, pk_val = s['peak'][0], s['peak'][1]
        fw, fw_pos     = s['fwhm'][0], s['fwhm'][1]
        com            = s['com']

        self.t_peak.k.setText("Peak"); self.t_peak.set_value(f"{pk_val:.5g} @ {pk_pos:.5g}"); self.t_peak.show()
        self.t_com.k.setText("COM");   self.t_com.set_value(f"{com:.5g}");                      self.t_com.show()
        self.t_fwhm.k.setText("FWHM"); self.t_fwhm.set_value(f"{fw:.5g} @ {fw_pos:.5g}");       self.t_fwhm.show()

        self.stats_text = f"{self.selected_column}: peak {pk_val:.5g}@{pk_pos:.5g}; COM {com:.5g}; FWHM {fw:.5g}@{fw_pos:.5g}"
        self._update_vdivider()

    def _update_vdivider(self):
        left_visible  = self.t_hkl.isVisible()
        right_visible = any(w.isVisible() for w in (self.t_peak, self.t_com, self.t_fwhm))
        self.vline.setVisible(left_visible and right_visible)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._elide_top_cmd()

    def _set_cmd(self, raw):
        self.top_cmd.setProperty("_raw", raw)
        self.top_cmd.setText(raw)

    def _elide_top_cmd(self):
        raw = self.top_cmd.property("_raw") or self.top_cmd.text()
        fm = self.top_cmd.fontMetrics()
        outer_w = max(0, self.width() - 40)
        num_w = self.top_num.sizeHint().width()
        sep_w = self.top_sep.sizeHint().width()
        max_cmd_w = max(60, int(0.9 * outer_w) - num_w - sep_w)
        elided = fm.elidedText(raw, Qt.ElideMiddle, max_cmd_w)
        self.top_cmd.setText(elided)


# Local test harness
if __name__ == "__main__":
    app = QApplication([])
    w = QMainWindow()
    ph = PlotHeader()
    ph.setTitle("Scan 154 - a2scan mch 1 1 Pth 1 3 10 1 with a very long command that should elide in the middle")
    # Simulate columns arriving
    ph._updateColumns(["det", "mon", "sec"])
    # Simulate stats
    ph._updateStats({'column': 'det', '2d': False, 'peak': (1.23456, 789.01), 'fwhm': (0.012345, 0.98765), 'com': 1.00001})
    ph.t_hkl.show(); ph.t_hkl.set_value("0.0836   0.0506   0.0000")
    w.setCentralWidget(ph)
    w.resize(900, 88)
    w.show()
    app.exec()
