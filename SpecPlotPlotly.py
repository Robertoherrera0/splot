# spec_plot_plotly.py
# Qt + Plotly replacement for SpecPlotMatplotlib
# Requires: PySide6 (Qt WebEngine + WebChannel), plotly
# Note: Loads Plotly from CDN. If you need offline, swap CDN for a local copy.


from __future__ import annotations
import json
import weakref
import numpy as np
import os
# force software paths for GL/Chromium in QtWebEngine
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
# disable GPU and compositing in Chromium
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS",
                      "--disable-gpu --disable-gpu-compositing --disable-zero-copy --no-sandbox")
# optional (helps on some builds):
os.environ.setdefault("QT_QUICK_BACKEND", "software")


from PySide6.QtCore import Qt, Signal, Slot, QObject, QTimer
from PySide6.QtWidgets import QWidget, QGridLayout, QSizePolicy
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

import plotly.graph_objects as go

# Your existing infrastructure:
from SpecPlotBaseClass import SpecPlotBaseClass, SpecPlotCurve, SpecPlotMarker
from Constants import *  # expects X_AXIS, Y1_AXIS, Y2_AXIS, etc.


# ------------------------- Qt⇄JS Bridge -------------------------

class _PlotlyBridge(QObject):
    """Bridge that JS calls into; emits Qt signals compatible with SpecPlotBaseClass usage."""
    pointSelected = Signal(str, float)             # (xlabel, x)
    regionSelected = Signal(str, float, float)     # (xlabel, x0, x1)

    @Slot(str, float)
    def emitPointSelected(self, xlabel: str, x: float):
        self.pointSelected.emit(xlabel, x)

    @Slot(str, float, float)
    def emitRegionSelected(self, xlabel: str, x0: float, x1: float):
        # Normalize so x0 <= x1
        lo, hi = (x0, x1) if x0 <= x1 else (x1, x0)
        self.regionSelected.emit(xlabel, lo, hi)


# ------------------------- Legend placement map -------------------------

# Map your existing legend keywords to Plotly anchors
_PLOTLY_LEGEND_POS = {
    "auto":       ("right", "top",   1.0, 1.0),
    "top_right":  ("right", "top",   1.0, 1.0),
    "top_left":   ("left",  "top",   0.0, 1.0),
    "bottom_right": ("right","bottom",1.0, 0.0),
    "bottom_left":  ("left","bottom", 0.0, 0.0),
    "top_center": ("center","top",   0.5, 1.0),
    "bottom_center": ("center","bottom",0.5,0.0),
}

def _legend_layout_from_key(key: str):
    xanchor, yanchor, x, y = _PLOTLY_LEGEND_POS.get(key, ("right","top",1.0,1.0))
    return dict(x=x, y=y, xanchor=xanchor, yanchor=yanchor, bgcolor="rgba(255,255,255,0.6)", bordercolor="rgba(0,0,0,0.15)")


# ------------------------- Plotly “Canvas” -------------------------

from PySide6.QtCore import QUrl

class _PlotlyCanvas:
    """Lightweight scene manager for a Plotly Figure living inside a QWebEngineView."""
    def __init__(self, web: QWebEngineView, bridge: _PlotlyBridge):
        self.web = web
        self.bridge = bridge

        self._fig = go.Figure()
        self._shapes = []
        self._annotations = []
        self._config = dict(
            displaylogo=False,
            responsive=True,
            modeBarButtonsToAdd=["select2d","lasso2d","zoom2d","pan2d","toImage"],
        )

        self._ready = False
        self._pending = None

        # connect BEFORE setHtml so we don't miss the signal
        self.web.loadFinished.connect(self._on_load_finished)
        self._init_html()

        # poke periodically until JS side is ready
        QTimer.singleShot(50, self._flush_if_ready)

    def _on_load_finished(self, ok: bool):
        print(f"[PLOT] loadFinished ok={ok}")
        self._ready = True
        self._flush_if_ready()

    def _flush_if_ready(self):
        """If renderFigure exists and we have a pending payload, push it.
           Otherwise, re-check soon (keeps trying)."""
        if not self._pending:
            # still useful to see if the JS is alive
            self.web.page().runJavaScript(
                "console.log('probe: typeof window.renderFigure =', typeof window.renderFigure);"
            )
            return

        def _cb(has_fn):
            if has_fn:
                figJSON, cfgJSON = self._pending
                print("[PLOT] renderFigure present; flushing payload")
                # clear AFTER success path
                self._pending = None
                self.web.page().runJavaScript(
                    f"window.renderFigure({json.dumps(figJSON)}, {json.dumps(cfgJSON)});"
                )
            else:
                # try again shortly; we also log this fact
                print("[PLOT] renderFigure not ready; will retry…")
                QTimer.singleShot(80, self._flush_if_ready)

        self.web.page().runJavaScript("typeof window.renderFigure === 'function'", _cb)

    def _init_html(self):
        # Inline plotly if possible; otherwise use CDN
        try:
            from plotly.offline import get_plotlyjs
            plotly_js = get_plotlyjs()
            plotly_tag = f"<script>{plotly_js}</script>"
            print("[PLOT] Using inline Plotly bundle")
        except Exception as e:
            print(f"[PLOT] Inline Plotly unavailable: {e}; falling back to CDN")
            plotly_tag = '<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>'

        html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
{plotly_tag}
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<style>
  html, body, #plot {{ height:100%; width:100%; margin:0; padding:0; background:#fff; }}
  #plot {{ border:1px dashed #999; }}
</style>
</head>
<body>
<div id="plot"></div>
<script>
(function() {{
  // (A) Define renderFigure FIRST, globally.
  window.renderFigure = function(figJSON, configJSON) {{
    try {{
      const fig = JSON.parse(figJSON);
      const cfg = JSON.parse(configJSON);
      if (typeof Plotly === 'undefined') {{
        console.error('Plotly missing');
        return;
      }}
      console.log('renderFigure: calling Plotly.react…');
      Plotly.react('plot', fig.data, fig.layout, cfg);

      const plot = document.getElementById('plot');
      if (plot && plot.removeAllListeners) plot.removeAllListeners();

      function getXLabel(f) {{
        try {{
          return (f && f.layout && f.layout.xaxis && f.layout.xaxis.title && f.layout.xaxis.title.text)
                 ? f.layout.xaxis.title.text : '';
        }} catch (e) {{ return ''; }}
      }}

      plot.on('plotly_click', function(e) {{
        if (!window.qt_bridge || !e || !e.points || !e.points.length) return;
        const p = e.points[0];
        const x = (typeof p.x === 'number') ? p.x : parseFloat(p.x);
        if (!isNaN(x)) window.qt_bridge.emitPointSelected(getXLabel(fig), x);
      }});

      plot.on('plotly_selected', function(e) {{
        if (!window.qt_bridge || !e || !e.range || !e.range.x) return;
        const x0 = parseFloat(e.range.x[0]), x1 = parseFloat(e.range.x[1]);
        if (!isNaN(x0) && !isNaN(x1)) window.qt_bridge.emitRegionSelected(getXLabel(fig), x0, x1);
      }});
      console.log('renderFigure: done.');
    }} catch (err) {{
      console.error('renderFigure error:', err);
    }}
  }};

  // (B) Init QWebChannel AFTER defining renderFigure (so Python can call it any time)
  window.qt_bridge = null;

  function waitFor(check, done) {{
    if (check()) return done();
    setTimeout(function() {{ waitFor(check, done); }}, 40);
  }}

  waitFor(
    function() {{ return !!(window.qt && window.qt.webChannelTransport && window.QWebChannel); }},
    function() {{
      try {{
        new QWebChannel(qt.webChannelTransport, function(channel) {{
          window.qt_bridge = channel.objects.qt_bridge || null;
          console.log('qt webchannel ready');
        }});
      }} catch (e) {{
        console.error('QWebChannel init failed:', e);
      }}
    }}
  );

  console.log('page bootstrap complete; typeof Plotly =', typeof Plotly);
}})();
</script>
</body>
</html>
"""
        # IMPORTANT: give a baseUrl so the qrc:/// script always resolves
        self.web.setHtml(html, baseUrl=QUrl("qrc:///"))

    def render(self, fig: go.Figure, config: dict | None = None):
        # strip 'meta' (invalid for shapes/annotations)
        clean_shapes = [{k: v for k, v in s.items() if k != "meta"} for s in self._shapes]
        clean_ann   = [{k: v for k, v in a.items() if k != "meta"} for a in self._annotations]

        if clean_shapes: fig.update_layout(shapes=clean_shapes)
        else:            fig.layout.shapes = ()
        if clean_ann:    fig.update_layout(annotations=clean_ann)
        else:            fig.layout.annotations = ()

        figJSON = fig.to_json()
        cfgJSON = json.dumps(config if config is not None else self._config)

        # always store latest; flush when JS is ready
        self._pending = (figJSON, cfgJSON)
        if not self._ready:
            print("[PLOT] page not ready; queued payload")
            return
        self._flush_if_ready()

    # ---- Shapes / annotations management ----
    def add_shape(self, shape: dict): self._shapes.append(shape)
    def remove_shapes_with_meta(self, meta_id: str):
        self._shapes = [s for s in self._shapes if s.get("meta") != meta_id]
    def add_annotation(self, ann: dict): self._annotations.append(ann)
    def remove_annotations_with_meta(self, meta_id: str):
        self._annotations = [a for a in self._annotations if a.get("meta") != meta_id]

# ------------------------- Curve (trace) wrapper -------------------------

class SpecPlotCurvePlotly(SpecPlotCurve):
    """Plotly implementation of a curve tied to y1 or y2."""
    def __init__(self, colname: str, plot: 'SpecPlotPlotly'):
        super().__init__(colname)
        self._plot_ref = weakref.ref(plot)
        self.yaxis = Y1_AXIS
        self.attached = False
        self.selected = False

        # style/flags mirrored from your Matplotlib version
        self.usedots = False
        self.uselines = True
        self.dotsize = 6
        self.linethick = 2

    def isAttached(self):
        return self.attached

    def attach(self):
        self.attached = True

    def detach(self):
        self.attached = False

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def setYAxis(self, axis):
        self.yaxis = axis

    def getLimits(self):
        if self._x.any() and self._y.size:
            xdata = self._x
            ydata = self._y
            minx, maxx = float(np.min(xdata)), float(np.max(xdata))
            miny, maxy = float(np.min(ydata)), float(np.max(ydata))
            minposy = float(np.min(ydata[ydata > 0])) if np.any(ydata > 0) else None
            return (minx, maxx, miny, maxy), minposy, self.yaxis
        else:
            return (None, None, None, None), None, self.yaxis

    # Convert this curve to a Plotly trace dict
    def to_trace(self):
        if not (self._x.any() and self._y.size):
            return None

        yaxis_name = "y" if self.yaxis == Y1_AXIS else "y2"

        mode = "lines+markers" if (self.uselines and self.usedots) else \
               ("lines" if self.uselines else "markers")

        trace = go.Scatter(
            x=self._x.tolist(),
            y=self._y.tolist(),
            name=self.mne,
            mode=mode,
            yaxis=yaxis_name,
            marker=dict(size=self.dotsize),
            line=dict(width=self.linethick),
        )
        # color in your app is often a QColor or str; cast to str
        if self.color is not None:
            trace.marker.color = str(self.color)
            trace.line.color = str(self.color)

        if self.selected:
            trace.update(legendrank=0)  # float to top
        return trace


# ------------------------- Marker wrappers (Plotly shapes/annotations) -------------------------

class _MarkerPlotlyBase(SpecPlotMarker):
    """Base for Plotly markers; manages meta ids for removal."""
    def __init__(self, label, **kwargs):
        super().__init__(label, **kwargs)
        self._attached = False
        self._meta_id = f"marker::{id(self)}"
        self._canvas = None  # _PlotlyCanvas

    def attach(self, plot: 'SpecPlotPlotly'):
        self._canvas = plot._canvas
        self._attached = True

    def detach(self):
        if not self._attached or self._canvas is None:
            return
        self._canvas.remove_shapes_with_meta(self._meta_id)
        self._canvas.remove_annotations_with_meta(self._meta_id)
        self._attached = False

    def isAttached(self):
        return self._attached

    def _color(self):
        return str(self.color) if self.color else "#1f77b4"


class SpecPlotVerticalMarkerPlotly(_MarkerPlotlyBase):
    marker_type = MARKER_VERTICAL
    def setLabelPosition(self, position):
        self.setYValue(position)
    def setCoordinates(self, posinfo):
        self.setXValue(posinfo[0])

    def draw(self):
        if not self.isAttached():
            return
        x = self.getXValue()
        label = self.getLabel()
        y = self.getYValue() or 0.95  # relative (paper) coords via annotation 'yref'
        col = self._color()

        # Remove old
        self._canvas.remove_shapes_with_meta(self._meta_id)
        self._canvas.remove_annotations_with_meta(self._meta_id)

        # Vertical line shape
        self._canvas.add_shape(dict(
            type="line", x0=x, x1=x, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color=col, width=1),
            meta=self._meta_id
        ))
        # Label near top
        self._canvas.add_annotation(dict(
            x=x, y=y, xref="x", yref="paper",
            text=label, showarrow=True, arrowhead=2,
            ax=0, ay=-20, font=dict(color=col),
            meta=self._meta_id
        ))


class SpecPlotTextMarkerPlotly(_MarkerPlotlyBase):
    marker_type = MARKER_TEXT
    def setCoordinates(self, posinfo):
        self.x, self.y = posinfo
    def getCoordinates(self):
        return self.x, self.y
    def draw(self):
        if not self.isAttached():
            return
        label = self.getLabel()
        x, y = self.getCoordinates()
        col = self._color()
        self._canvas.remove_annotations_with_meta(self._meta_id)
        self._canvas.add_annotation(dict(
            x=x, y=y, xref="x", yref="y",
            text=label, showarrow=False,
            font=dict(color=col),
            meta=self._meta_id
        ))


class SpecPlotSegmentMarkerPlotly(_MarkerPlotlyBase):
    marker_type = MARKER_SEGMENT
    def setCoordinates(self, coords):
        self.x0, self.y0, self.x1, self.y1 = coords
    def getCoordinates(self):
        return self.x0, self.y0, self.x1, self.y1
    def getXValue(self):
        return (self.x0 + self.x1) / 2.0
    def getYValue(self):
        return (self.y0 + self.y1) / 2.0
    def draw(self):
        if not self.isAttached():
            return
        x0, y0, x1, y1 = self.getCoordinates()
        label = self.getLabel()
        lx, ly = self.getXValue(), self.getYValue()
        col = self._color()

        self._canvas.remove_shapes_with_meta(self._meta_id)
        self._canvas.remove_annotations_with_meta(self._meta_id)

        self._canvas.add_shape(dict(
            type="line", x0=x0, y0=y0, x1=x1, y1=y1,
            xref="x", yref="y",
            line=dict(color=col, width=2),
            meta=self._meta_id
        ))
        self._canvas.add_annotation(dict(
            x=lx, y=ly, xref="x", yref="y",
            text=label, showarrow=False,
            font=dict(color=col),
            meta=self._meta_id
        ))


# ------------------------- Main Widget -------------------------
# put this near your marker classes, before SpecPlotPlotly
class _NullMarker:
    def attach(self, *a, **k): pass
    def detach(self): pass
    def draw(self): pass
    def isAttached(self): return False
    def setLabelPosition(self, *a, **k): pass
    def setCoordinates(self, *a, **k): pass

class _NullZoomer:
    def __init__(self, *_):
        self._enabled = False
        self._selecting = False
    def setEnabled(self, flag: bool): self._enabled = bool(flag)
    def isEnabled(self): return self._enabled
    def setZoomBase(self): pass
    def isZoomed(self): return False
    def rescale(self): pass
    def begin(self, *_): self._selecting = self._enabled
    def end(self, *_): self._selecting = False
    def isSelecting(self): return self._enabled and self._selecting
    def mouse_move(self, *_): pass
    def scrollIt(self, *_): pass
    def resetZoom(self): pass

class _NullRegionZoom:
    def __init__(self, *_):
        self._enabled = False
        self._selecting = False
    def setEnabled(self, flag: bool): self._enabled = bool(flag)
    def isEnabled(self): return self._enabled
    def begin(self, *_): self._selecting = self._enabled
    def end(self, *_): self._selecting = False
    def isSelecting(self): return self._enabled and self._selecting
    def mouse_move(self, *_): pass

class _NullCrossHairs:
    def __init__(self, *_):
        self._enabled = False
    def setEnabled(self, flag: bool): self._enabled = bool(flag)
    def isEnabled(self): return self._enabled
    def mouse_move(self, *_): pass

from PySide6.QtWebEngineCore import QWebEnginePage

class _DebugPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # level is a QWebEnginePage.JavaScriptConsoleMessageLevel enum
        try:
            name = {
                QWebEnginePage.InfoMessageLevel:    "INFO",
                QWebEnginePage.WarningMessageLevel: "WARN",
                QWebEnginePage.ErrorMessageLevel:   "ERROR",
            }.get(level, str(level))
        except Exception:
            name = str(level)
        print(f"[JS {name}] {message}  ({sourceID}:{lineNumber})")

class SpecPlotPlotly(QWidget, SpecPlotBaseClass):
    # Signals (match your Matplotlib version)
    pointSelected = Signal(str, float)
    regionSelected = Signal(str, float, float)
    configurationChanged = Signal()

    _vertical_marker_class = SpecPlotVerticalMarkerPlotly
    _text_marker_class = SpecPlotTextMarkerPlotly
    _segment_marker_class = SpecPlotSegmentMarkerPlotly

    def __init__(self, parent=None, *args, **kwargs):
        self.parent = parent

        # axis/data bounds cache
        self.x_min = self.x_max = None
        self.y1_min = self.y1_max = None
        self.y2_min = self.y2_max = None

        # Legacy attrs expected by SpecPlotWidget
        self.legendY1 = None
        self.legendY2 = None


        # axes control
        self.axes_auto = {}
        self.axes_limits = {}

        SpecPlotBaseClass.__init__(self, **kwargs)
        QWidget.__init__(self, parent, *args)

        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setRowStretch(0, 1)        # <-- add
        self._layout.setColumnStretch(0, 1)     # <-- add


        # Web view + channel + bridge
        self._web = QWebEngineView(self)
        self._web.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._page = _DebugPage(self)       # <<— debug page
        self._web.setPage(self._page)       # <<— install page BEFORE making channel

        self._channel = QWebChannel(self._web.page())
        self._bridge  = _PlotlyBridge()
        self._channel.registerObject("qt_bridge", self._bridge)
        self._web.page().setWebChannel(self._channel)

        # Canvas (Plotly scene manager)
        self._canvas = _PlotlyCanvas(self._web, self._bridge)

        # Signals to outside
        self._bridge.pointSelected.connect(self._emit_point_selected)
        self._bridge.regionSelected.connect(self._emit_region_selected)

        self._layout.addWidget(self._web, 0, 0)

        # Initial state
        self.setDataStatus(DATA_STATIC)

        # must come before loadPreferences()
        self.initMarkers()

        # seed placeholders so any base call won't crash
        self.lineMotPos = _NullMarker()
        self.lineMotVal = _NullMarker()
        # tools the base class expects
        self.crosshairs = _NullCrossHairs()
        self.zoomer = _NullZoomer(weakref.ref(self))
        self.regionzoom = _NullRegionZoom(weakref.ref(self))


        self.loadPreferences()
        self.initColorTable()
        self._setShowLegend()
        self._setLegendPosition()
        self.replot()



    # --- add this helper inside SpecPlotPlotly ---
    def redrawCurves(self):
        self.queue_replot()

    def redrawAxes(self):
        self.queue_replot()


    def _ensure_required_markers(self):
        """Make sure motor-position markers exist so base toggles don't explode."""
        if not hasattr(self, "lineMotPos") or self.lineMotPos is None:
            m = self.addVerticalMarker("Motor pos")
            try:
                m.attach(self)
            except Exception:
                pass
            self.lineMotPos = m
        # If your base class also uses a text label for motor pos, keep this too:
        if not hasattr(self, "lineMotVal"):
            t = self.addTextMarker("")
            try:
                t.attach(self)
            except Exception:
                pass
            self.lineMotVal = t

    # ------------- Bridge re-emission -------------
    def _emit_point_selected(self, xlabel: str, xpos: float):
        # xlabel should be self.first_x to match your API
        if not xlabel:
            xlabel = getattr(self, "first_x", "")
        self.pointSelected.emit(xlabel, xpos)

    def _emit_region_selected(self, xlabel: str, x0: float, x1: float):
        if not xlabel:
            xlabel = getattr(self, "first_x", "")
        self.regionSelected.emit(xlabel, x0, x1)

    # ------------- Public API compatibility -------------

    def addCurve(self, colname):
        curve = SpecPlotCurvePlotly(colname, self)
        self.curves[colname] = curve

        # styling (mirrors your Matplotlib setup)
        color = self.colorTable.getColor(colname)
        curve.setColor(color)
        curve.showErrorBars(self.showbars)
        curve.setUseLines(self.uselines)
        curve.setLineThickness(self.linethick)
        curve.setUseDots(self.usedots)
        curve.setDotSize(self.dotsize)
        curve.attach()

        self.setAxisTitles()
        self.queue_replot()

    def addVerticalMarker(self, label, **kwargs):
        m = SpecPlotVerticalMarkerPlotly(label, **kwargs)
        return m

    def addTextMarker(self, label, **kwargs):
        m = SpecPlotTextMarkerPlotly(label, **kwargs)
        return m

    def addSegmentMarker(self, label, **kwargs):
        m = SpecPlotSegmentMarkerPlotly(label, **kwargs)
        return m

    def _showCurve(self, colname, axis=Y1_AXIS):
        if colname in self.curves:
            self.curves[colname].setYAxis(axis)
            self.curves[colname].attach()
            self.queue_replot()

    def _hideCurve(self, colname):
        if colname in self.curves:
            self.curves[colname].detach()
            self.queue_replot()

    def _useY1Axis(self, flag=True):
        self.using_y1 = flag
        self.queue_replot()

    def _useY2Axis(self, flag=True):
        self.using_y2 = flag
        self.queue_replot()

    def _changeCurveColor(self, mne, color):
        mne = str(mne)
        if mne in self.curves:
            self.curves[mne].setColor(color)
        self.setAxisTitles()
        self.queue_replot()

    def _setXLog(self, flag):
        self.xlog = flag
        self.queue_replot()

    def _setY1Log(self, flag):
        self.y1log = flag
        self.queue_replot()

    def _setY2Log(self, flag):
        self.y2log = flag
        self.queue_replot()

    def _setShowLegend(self):
        # handled in layout at render time via self.showlegend
        self.queue_replot()

    def _setLegendPosition(self):
        # handled in layout at render time via self.legend_position
        self.queue_replot()

    def _showGrid(self):
        self.queue_replot()

    def _hideGrid(self):
        self.queue_replot()

    # ---- Titles ----
    def _updateTitles(self):
        # Plotly layout text is set in replot() from self.xlabel, y1label, y2label
        pass

    # ---- Axis auto/limits API compatibility ----
    def setXAxisAuto(self): self._setAxisAuto(X_AXIS, True)
    def setY1AxisAuto(self): self._setAxisAuto(Y1_AXIS, True)
    def setY2AxisAuto(self): self._setAxisAuto(Y2_AXIS, True)

    def _setAxisAuto(self, axis, flag):
        if (axis not in self.axes_auto) or (flag != self.axes_auto[axis]):
            self.axes_auto[axis] = flag
            self.queue_replot()

    def _setAxisLimits(self, axis, axmin, axmax):
        self._setAxisAuto(axis, False)
        if (axis not in self.axes_limits) or (axmin, axmax) != self.axes_limits[axis]:
            self.axes_limits[axis] = (axmin, axmax)
            self.queue_replot()

    # ---- Limits computation (same logic as before, simplified) ----
    def check_limits(self):
        x_min = x_max = None
        y1_min = y1_max = None
        y2_min = y2_max = None
        minpos_y1 = minpos_y2 = None

        x_fixed = False
        if self.isScanRunning() and not self.x_range_auto:
            x_min, x_max = self.x_range_beg, self.x_range_end
            if None not in [x_min, x_max]:
                x_fixed = True

        for curve in self.curves.values():
            if not curve.isAttached():
                continue
            lims, minposy, yaxis = curve.getLimits()
            if None in lims:
                continue
            minx, maxx, miny, maxy = lims

            if not x_fixed:
                x_min = minx if x_min is None else min(x_min, minx)
                x_max = maxx if x_max is None else max(x_max, maxx)

            if yaxis is Y2_AXIS:
                y2_min = miny if y2_min is None else min(y2_min, miny)
                y2_max = maxy if y2_max is None else max(y2_max, maxy)
                if minpos_y2 is None or (minposy is not None and minposy < minpos_y2):
                    minpos_y2 = minposy
            else:
                y1_min = miny if y1_min is None else min(y1_min, miny)
                y1_max = maxy if y1_max is None else max(y1_max, maxy)
                if minpos_y1 is None or (minposy is not None and minposy < minpos_y1):
                    minpos_y1 = minposy

        self.x_min, self.x_max = x_min, x_max
        self.y1_min, self.y1_max = y1_min, y1_max
        self.y2_min, self.y2_max = y2_min, y2_max
        self.y1min_pos = minpos_y1 or 0
        self.y2min_pos = minpos_y2 or 0

        return True, True, True  # we don't micro-track changes here

    # ---- Main render/update ----
    def replot(self):
        traces = []
        for c in self.curves.values():
            if not c.isAttached():
                continue
            tr = c.to_trace()
            if tr:
                traces.append(tr)

        # If there are no curves yet, add an invisible trace so axes appear
        # --- in SpecPlotPlotly.replot(), when no real traces are present ---
        if not traces:
            traces = [go.Scatter(
                x=[0, 1], y=[0, 1], mode="lines",
                line=dict(width=0), showlegend=False, hoverinfo="skip", name=""
            )]

        fig = go.Figure(data=traces)
        fig.update_xaxes(range=[0, 1])
        fig.update_yaxes(range=[0, 1])

        # 2) layout: axes, labels, scales, legend, grid
        # Titles
        x_title = getattr(self, "xlabel", "X")
        y1_title = getattr(self, "y1label", "")
        y2_title = getattr(self, "y2label", "")

        # Scales
        x_type = "log" if getattr(self, "xlog", False) else "linear"
        y1_type = "log" if getattr(self, "y1log", False) else "linear"
        y2_type = "log" if getattr(self, "y2log", False) else "linear"

        # Grid
        show_grid = bool(getattr(self, "showing_grid", False))

        # Legend
        legend = dict(orientation="v", traceorder="normal", font=dict(size=10), bgcolor="rgba(255,255,255,0.6)")
        legend.update(_legend_layout_from_key(getattr(self, "legend_position", "auto")))
        legend["visible"] = bool(getattr(self, "showlegend", True))

        # Dual y-axes
        fig.update_layout(
            xaxis=dict(title=dict(text=x_title), type=x_type, showgrid=show_grid, zeroline=False),
            yaxis=dict(title=y1_title, type=y1_type, showgrid=show_grid, zeroline=False),
            yaxis2=dict(title=y2_title, type=y2_type, overlaying="y", side="right", showgrid=False, zeroline=False),
            legend=legend,
            margin=dict(l=60, r=60, t=30, b=45),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        # 3) limits (auto or manual)
        self.check_limits()

        # X
        if not self.axes_auto.get(X_AXIS, True) and X_AXIS in self.axes_limits:
            xmin, xmax = self.axes_limits[X_AXIS]
        else:
            xmin, xmax = self.x_min, self.x_max
        if None not in (xmin, xmax):
            fig.update_xaxes(range=[xmin, xmax])

        # Y1
        if getattr(self, "using_y1", True):
            if not self.axes_auto.get(Y1_AXIS, True) and Y1_AXIS in self.axes_limits:
                ymin, ymax = self.axes_limits[Y1_AXIS]
            else:
                ymin, ymax = self.y1_min, self.y1_max
                if getattr(self, "y1log", False) and ymin is not None and ymin <= 0:
                    ymin = max(self.y1min_pos, 1e-6)
            if None not in (ymin, ymax):
                fig.update_yaxes(range=[ymin, ymax], matches=None)
        else:
            fig.update_yaxes(showticklabels=False)

        # Y2
        if getattr(self, "using_y2", True):
            if not self.axes_auto.get(Y2_AXIS, True) and Y2_AXIS in self.axes_limits:
                ymin2, ymax2 = self.axes_limits[Y2_AXIS]
            else:
                ymin2, ymax2 = self.y2_min, self.y2_max
                if getattr(self, "y2log", False) and ymin2 is not None and ymin2 <= 0:
                    ymin2 = max(self.y2min_pos, 1e-6)
            if None not in (ymin2, ymax2):
                fig.update_layout(yaxis2=dict(range=[ymin2, ymax2], overlaying="y", side="right"))
        else:
            # hide y2 completely
            fig.update_layout(yaxis2=dict(visible=False))

        # 4) markers (they already add shapes/annotations to canvas object)
        # draw any attached markers
        for m in self.markers.values():
            if not m.isAttached():
                m.attach(self)
            m.draw()

        # 5) render
        self._canvas.render(fig)
        # notify
        self.configurationChanged.emit()

    def queue_replot(self):
        # Keep it simple: coalesce rapid updates
        QTimer.singleShot(0, self.replot)

    # ---- Printing / saving ----
    def saveAsImage(self, filename: str, title: str = ""):
        # Fallback: grab the rendered web view (PNG)
        pix = self._web.grab()
        pix.save(filename)

    def printPlot(self, title, printer, filename):
        # Basic fallback to image save
        self.saveAsImage(filename, title)

    # ---- Convenience for external calls (aligns with your old canvas API) ----
    def setXAxisLimits(self, x0, x1):
        self._setAxisLimits(X_AXIS, x0, x1)

    def setY1Limits(self, y0, y1):
        self._setAxisLimits(Y1_AXIS, y0, y1)

    def setY2Limits(self, y0, y1):
        self._setAxisLimits(Y2_AXIS, y0, y1)


# ------------------------- Local test -------------------------

def _demo():
    """Quick manual demo."""
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow
    from DataBlock import DataBlock

    app = QApplication(sys.argv)
    win = QMainWindow()
    wid = SpecPlotPlotly(theme="classic")
    win.setCentralWidget(wid)

    # Fake data
    data = np.array([
        [1,  2,  4,  3],
        [3,  5,  4,  2],
        [4,  6,  1,  7],
        [5,  3,  3,  1],
        [0,  4,  3,  2],
        [6, 19, 18, 13]
    ])
    colnames = ["x", "sec", "mon", "det"]

    dblock = DataBlock()
    wid.setDataBlock(dblock)
    dblock.setData(data)
    dblock.setColumnNames(colnames)
    dblock.setXSelection("x")
    dblock.setY1Selection(["mon"])
    dblock.setY2Selection(["det"])

    wid.updateColumnSelection()
    win.resize(900, 600)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    _demo()
