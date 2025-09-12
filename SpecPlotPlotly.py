# spec_plot_plotly.py
# Qt + Plotly replacement for SpecPlotMatplotlib
# Requires: PySide6 (Qt WebEngine + WebChannel), plotly
# Note: Loads Plotly from CDN. If you need offline, swap CDN for a local copy.


from __future__ import annotations
import json
import weakref
import numpy as np
import os
import tempfile, pathlib
from PySide6.QtCore import QUrl


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
            displayModeBar=True,     
            scrollZoom=True,         
            doubleClick="reset",     
            modeBarButtonsToRemove=["toImage"],  
            modeBarButtonsToAdd=[      
                "zoomIn2d", "zoomOut2d",
                "hoverCompareCartesian",
            ],
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
        Safe against re-entrancy / multiple callbacks."""
        if not self._pending:
            # still useful to probe JS side
            self.web.page().runJavaScript("typeof window.renderFigure === 'function'", lambda *_: None)
            return

        def _cb(has_fn):
            # another run may have flushed while we waited
            payload = self._pending
            if not payload:
                return
            if has_fn:
                figJSON, cfgJSON = payload
                # clear after we've copied the payload
                self._pending = None
                self.web.page().runJavaScript(
                    f"window.renderFigure({json.dumps(figJSON)}, {json.dumps(cfgJSON)})"
                )
            else:
                # try again shortly
                QTimer.singleShot(80, self._flush_if_ready)

        self.web.page().runJavaScript("typeof window.renderFigure === 'function'", _cb)

    def _init_html(self):
        # Keep a temp dir alive for the life of the view
        self._tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="splot_plotly_"))

        # Prefer a bundled file if you ship one alongside this module:
        bundle_path = pathlib.Path(__file__).with_name("plotly.min.js")
        try:
            if bundle_path.exists():
                js_text = bundle_path.read_text(encoding="utf-8")
                print("[PLOT] Using bundled plotly.min.js")
            else:
                # Last resort: generate from plotly (still offline)
                from plotly.offline import get_plotlyjs
                js_text = get_plotlyjs()
                print("[PLOT] Using plotly.offline.get_plotlyjs() output")
            (self._tmpdir / "plotly.min.js").write_text(js_text, encoding="utf-8")
        except Exception as e:
            print(f"[PLOT] Could not materialize plotly.min.js: {e}")
        plotly_tag = '<script src="plotly.min.js"></script>'

        html = f"""<!doctype html>
    <html>
    <head>
    <meta charset="utf-8"/>
    {plotly_tag}
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
    html,body{{height:100%;width:100%;margin:0;background:transparent;}}
    #plot{{height:100%;width:100%;background:transparent;}}

    /* Hover-to-show modebar */
    #plot .modebar{{
    opacity:0;
    pointer-events:none;            /* don’t intercept clicks while hidden */
    transition:opacity .12s ease;
    top:8px !important;
    right:8px !important;
    background:rgba(255,255,255,0.65);
    border-radius:6px;
    padding:2px;
    }}
    #plot:hover .modebar,
    #plot.modebar-show .modebar{{     /* programmatic “flash” (below) */
    opacity:1;
    pointer-events:auto;
    }}

    #plot .modebar-btn{{ opacity:0.85; }}
    #plot .modebar-btn:hover{{opacity:1; }}
    </style>
    </head>
    <body>
    <div id="plot"></div>
    <script>
    // Define renderFigure first so Python can call it at any time
    window.renderFigure = function(figJSON, cfgJSON) {{
    try {{
        const fig = JSON.parse(figJSON);
        const cfg = JSON.parse(cfgJSON);

        const plot = document.getElementById('plot');
        if (plot && plot.removeAllListeners) plot.removeAllListeners();

        // Render/update the figure, then tint only the axes area
        Plotly.react('plot', fig.data, fig.layout, cfg).then(() => {{
        const paper  = (fig.layout && fig.layout.paper_bgcolor) || 'transparent';
        const plotbg = (fig.layout && fig.layout.plot_bgcolor)  || 'transparent';

        // keep the outer page neutral; don't tint #plot itself
        document.documentElement.style.background = paper;
        document.body.style.background = paper;

        const applyBg = () => {{
            // For each subplot, set the background rect fill + a subtle frame
            const rects = plot.querySelectorAll('.bglayer rect.bg');
            rects.forEach(r => {{
            r.setAttribute('fill', plotbg);
            r.setAttribute('stroke', 'rgba(0,0,0,0.18)');
            r.setAttribute('stroke-width', '1');
            }});
        }};
        // run now and on redraw/resize
        requestAnimationFrame(applyBg);
        plot.on('plotly_afterplot', applyBg);
        window.addEventListener('resize', applyBg, {{ passive: true }});
        }});

        function xLabel(f) {{
        return f?.layout?.xaxis?.title?.text || '';
        }}

        plot.on('plotly_click', (e) => {{
        if (!window.qt_bridge || !e?.points?.length) return;
        const x = parseFloat(e.points[0].x);
        if (!Number.isNaN(x)) window.qt_bridge.emitPointSelected(xLabel(fig), x);
        }});
        plot.on('plotly_selected', (e) => {{
        if (!window.qt_bridge || !e?.range?.x) return;
        const [x0, x1] = e.range.x.map(parseFloat);
        if (!Number.isNaN(x0) && !Number.isNaN(x1))
            window.qt_bridge.emitRegionSelected(xLabel(fig), x0, x1);
        }});

        console.log('renderFigure: done');
    }} catch (err) {{
        console.error('renderFigure error:', err);
    }}
    }};

    // WebChannel after defining renderFigure
    new QWebChannel(qt.webChannelTransport, (channel) => {{
    window.qt_bridge = channel.objects.qt_bridge || null;
    console.log('qt webchannel ready');
    }});
    </script>
    </body>
    </html>"""

        index_path = self._tmpdir / "index.html"
        index_path.write_text(html, encoding="utf-8")
        self.web.load(QUrl.fromLocalFile(str(index_path)))


    # ---- Shapes / annotations management ----
    def add_shape(self, shape: dict):
        self._shapes.append(shape)

    def remove_shapes_with_meta(self, meta_id: str):
        self._shapes = [s for s in self._shapes if s.get("meta") != meta_id]

    def add_annotation(self, ann: dict):
        self._annotations.append(ann)

    def remove_annotations_with_meta(self, meta_id: str):
        self._annotations = [a for a in self._annotations if a.get("meta") != meta_id]

    # ---- Push a figure into the page ----
    def render(self, fig, config=None):
        # merge any queued shapes/annotations
        clean_shapes = [{k: v for k, v in s.items() if k != "meta"} for s in self._shapes]
        clean_ann    = [{k: v for k, v in a.items() if k != "meta"} for a in self._annotations]

        if clean_shapes:
            fig.update_layout(shapes=clean_shapes)
        else:
            fig.layout.shapes = ()

        if clean_ann:
            fig.update_layout(annotations=clean_ann)
        else:
            fig.layout.annotations = ()

        figJSON = fig.to_json()
        cfgJSON = json.dumps(config if config is not None else self._config)

        # store latest payload; flush when JS is ready
        self._pending = (figJSON, cfgJSON)
        if not self._ready:
            print("[PLOT] page not ready; queued payload")
            return
        self._flush_if_ready()

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
    pointSelected = Signal(str, float)
    regionSelected = Signal(str, float, float)
    configurationChanged = Signal()
    fitResultsReady = Signal(dict)

    _vertical_marker_class = SpecPlotVerticalMarkerPlotly
    _text_marker_class = SpecPlotTextMarkerPlotly
    _segment_marker_class = SpecPlotSegmentMarkerPlotly

    def __init__(self, parent=None, *args, **kwargs):
        self.parent = parent
        self.theme = "dim"   # "light" | "dim" | "dark"
        self.show_frame = True        # draw a 1px frame around the plot area
        self.live_tint  = True        # tint background while scanning
        self._last_fit = {}  

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

        self.showing_grid = True 


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

        self._overlays = []          # extra traces (fits, etc.)
        self._last_region = None     # (x0, x1) from drag selection
        self.stats_visible = True
        self._last_stats = {}
        self._last_fit = None       # store last fit result (for peak/FWHM export)


        self.loadPreferences()
        self.initColorTable()
        self._setShowLegend()
        self._setLegendPosition()
        self.replot()


    def _theme_colors(self):
        t = getattr(self, "theme", "light")

        if t == "dim":
            return dict(
                paper="#F8FAFC", plot="#F3F4F6",
                paper_live="#EEF2FF", plot_live="#E5E7EB",   # live tint
                grid="rgba(0,0,0,0.10)", axis="#6B7280", tick="#111827",
                legend_bg="rgba(255,255,255,0.85)", frame="#CBD5E1"
            )
        if t == "dark":
            return dict(
                paper="#0B1220", plot="#111827",
                paper_live="#0D1726", plot_live="#0F1B2D",
                grid="rgba(255,255,255,0.12)", axis="#C7D2FE", tick="#E5E7EB",
                legend_bg="rgba(17,24,39,0.8)", frame="#334155"
            )
        # light
        return dict(
            paper="#FFFFFF", plot="#FFFFFF",
            paper_live="#FFF8E1", plot_live="#FFF2C2",
            grid="rgba(0,0,0,0.08)", axis="#4B5563", tick="#111827",
            legend_bg="rgba(255,255,255,0.8)", frame="#D1D5DB"
        )

    def _is_live(self):
        try:
            return bool(self.isScanRunning())
        except Exception:
            return False

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
        lo, hi = (x0, x1) if x0 <= x1 else (x1, x0)
        self._last_region = (lo, hi)
        self.regionSelected.emit(xlabel, lo, hi)


    # ------------- Public API compatibility -------------
    def _active_curve(self):
        # Prefer a selected curve; else first attached on Y1; else any attached
        attached = [c for c in self.curves.values() if c.isAttached()]
        if not attached:
            return None
        sel = [c for c in attached if getattr(c, "selected", False)]
        if sel:
            return sel[0]
        y1 = [c for c in attached if c.yaxis == Y1_AXIS]
        return (y1[0] if y1 else attached[0])

    def _data_for_fit(self):
        c = self._active_curve()
        if not c or c._x.size < 3:
            return None, None, None
        x, y = np.asarray(c._x, float), np.asarray(c._y, float)
        if self._last_region:
            lo, hi = self._last_region
            m = (x >= lo) & (x <= hi)
            if np.any(m):
                x, y = x[m], y[m]
        return c, x, y

    def _clear_overlays(self, tag_prefix=None):
        if tag_prefix is None:
            self._overlays = []
        else:
            self._overlays = [t for t in self._overlays
                            if not (isinstance(t, dict) and str(t.get("meta","")).startswith(tag_prefix))]

    def _add_fit_overlay(self, xgrid, yfit, name, color=None, meta="overlay::fit"):
        tr = go.Scatter(
            x=xgrid, y=yfit, name=name, mode="lines",
            line=dict(width=2, dash="dash", color=(str(color) if color else None)),
            showlegend=True
        )
        # we store meta via to_plotly_json so we can filter later
        d = tr.to_plotly_json()
        d["meta"] = meta
        self._overlays.append(go.Scatter(**d))

    def fit_current(self, model: str = "gaussian"):
        from SpecPlotFitModels import fit_curve, gaussian, supergaussian, hill
        import plotly.graph_objects as go
        import numpy as np

        # 0) pull current curve data (or selected region)
        curve, x, y = self._data_for_fit()
        if curve is None or x.size < 3:
            print("[FIT] no curve to fit")
            self._clear_overlays(tag_prefix="overlay::fit")
            self._canvas.remove_annotations_with_meta("ann::fit")
            self.queue_replot()
            return {}

        # 1) run fit
        res = fit_curve(x, y, model)
        print(f"[FIT] {model}:", res)

        # 2) make a smooth grid across the data extents and compute yfit
        xmin = float(np.nanmin(x)); xmax = float(np.nanmax(x))
        xgrid = np.linspace(xmin, xmax, 400)

        if model == "gaussian":
            yfit = gaussian(xgrid, *res["popt"])
            name = f"{curve.mne} • Gaussian fit"
            try:
                self._set_vertical_marker("PEAK", res.get("x0"))
                if res.get("fwhm") is not None:
                    self._set_vertical_marker("FWHM", res.get("x0"))
            except Exception:
                pass
        elif model == "supergaussian":
            yfit = supergaussian(xgrid, *res["popt"])
            name = f"{curve.mne} • Super-Gaussian fit"
            try:
                self._set_vertical_marker("PEAK", res.get("x0"))
                if res.get("fwhm") is not None:
                    self._set_vertical_marker("FWHM", res.get("x0"))
            except Exception:
                pass
        else:  # hill
            yfit = hill(xgrid, *res["popt"])
            name = f"{curve.mne} • Hill fit"

        # 3) remove any prior fit overlays + annotation
        self._clear_overlays(tag_prefix="overlay::fit")
        self._canvas.remove_annotations_with_meta("ann::fit")

        # 4) add dashed red overlay for the fit
        red = self._fit_color()
        tr = go.Scatter(
            x=xgrid.tolist(), y=yfit.tolist(),
            name=name, mode="lines",
            line=dict(color=red, width=2, dash="dash"),
            showlegend=True, hoverinfo="skip",
            meta="overlay::fit",
        )
        self._add_overlay(tr, tag="overlay::fit")

        # 5) compact summary badge
        p = res.get("params", {})
        r2   = float(res.get("r2", float("nan")))
        x0   = float(res.get("x0", float("nan")))
        fwhm_raw = res.get("fwhm", None)
        fwhm = float(fwhm_raw) if fwhm_raw is not None else float("nan")

        if model == "gaussian":
            A = float(p.get("A", float("nan")))
            B = float(p.get("B", 0.0))
            yhat = A + B if np.isfinite(A) and np.isfinite(B) else float("nan")
        elif model == "supergaussian":
            # similar formula: peak at x0, ŷ = A + B
            A = float(p.get("A", float("nan")))
            B = float(p.get("B", 0.0))
            yhat = A + B if np.isfinite(A) and np.isfinite(B) else float("nan")
        else:  # hill
            i_max = int(np.nanargmax(yfit))
            x0 = float(xgrid[i_max])
            yhat = float(yfit[i_max])

        parts = [f"{model.upper()}", f"R²={r2:.3f}"]
        if np.isfinite(x0):   parts.append(f"Peak_x={x0:.3f}")
        if np.isfinite(yhat): parts.append(f"Peak_y={yhat:.3f}")
        if np.isfinite(fwhm): parts.append(f"FWHM={fwhm:.3f}")
        summary = "  ".join(parts)

        self._canvas.add_annotation(dict(
            x=0.01, y=0.99, xref="paper", yref="paper",
            text=summary, showarrow=False, font=dict(size=11), align="left",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.25)",
            borderwidth=1, borderpad=3,
            meta="ann::fit"
        ))

        self._last_fit = {
            "peak_fit_x": x0,
            "peak_fit_y": yhat,
            "fwhm": fwhm,
            "r2": r2,
        }
        self.fitResultsReady.emit(self._last_fit)

        # 7) redraw and return
        self.queue_replot()
        return self._last_fit

    def getFitResults(self) -> dict:
        """Return the last fit results dict (safe copy)."""
        return dict(self._last_fit or {})


    def get_last_fit_results(self):
            """Return dict with last fit results (peak_fit, fwhm, r2, peak_max, com)."""
            return dict(self._last_fit)

    def get_current_curve_data(self):
        """Return (x, y) arrays of the active curve (after region selection if set)."""
        c, x, y = self._data_for_fit()
        return (x.copy(), y.copy()) if x is not None else (None, None)

    def _set_vertical_marker(self, label_contains: str, x: float, color=None):
        for m in self.markers.values():
            if getattr(m, "marker_type", None) == MARKER_VERTICAL:
                lab = (m.getLabel() or "").upper()
                if label_contains.upper() in lab:
                    m.setXValue(float(x))
                    if color is not None:
                        m.setColor(color)
                    m.draw()

    def addCurve(self, colname):
        curve = SpecPlotCurvePlotly(colname, self)
        self.curves[colname] = curve

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
        if not traces:
            traces = [go.Scatter(
                x=[0, 1], y=[0, 1], mode="lines",
                line=dict(width=0), showlegend=False, hoverinfo="skip", name=""
            )]
        if self._overlays:
            traces.extend(self._overlays)

        fig = go.Figure(data=traces)   # <— add this line
        fig = go.Figure(data=traces)
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


        # --- Grid + theme colors ---
        cols = self._theme_colors()
        grid_on = bool(getattr(self, "showing_grid", True))

        # Live tint while scanning
        live = self.live_tint and self._is_live()
        paper_bg = cols["paper"]
        plot_bg  = cols["plot_live"]  if live else cols["plot"]

        # Legend
        legend = dict(orientation="v", traceorder="normal", font=dict(size=10),
                    bgcolor=cols["legend_bg"])
        legend.update(_legend_layout_from_key(getattr(self, "legend_position", "auto")))
        legend["visible"] = bool(getattr(self, "showlegend", True))

        # --- Frame: paper-relative rectangle (added as a canvas shape) ---
        self._canvas.remove_shapes_with_meta("decor::frame")
        if self.show_frame:
            self._canvas.add_shape(dict(
                type="rect", xref="paper", yref="paper",
                x0=0, y0=0, x1=1, y1=1,
                line=dict(color=cols["frame"], width=1),
                fillcolor="rgba(0,0,0,0)",
                layer="below",
                meta="decor::frame",
            ))

        # --- Axes + layout ---
        fig.update_layout(
            xaxis=dict(
                title=dict(text=x_title),
                type=x_type,
                showgrid=True,
                gridcolor=cols["grid"],
                gridwidth=1,
                tickfont=dict(color=cols["tick"]),
                linecolor=cols["axis"],
                showline=False,
                zeroline=False,
            ),
            yaxis=dict(
                title=y1_title,
                type=y1_type,
                showgrid=True,
                gridcolor=cols["grid"],
                gridwidth=1,
                tickfont=dict(color=cols["tick"]),
                linecolor=cols["axis"],
                showline=False,
                zeroline=False,
            ),
            yaxis2=dict(
                title=y2_title, type=y2_type, overlaying="y", side="right",
                showgrid=False, zeroline=False, tickfont=dict(color=cols["tick"])
            ),
            legend=legend,
            margin=dict(l=52, r=5, t=35, b=22),   # <-- smaller margins
            paper_bgcolor=paper_bg,
            plot_bgcolor=plot_bg,
        )

        # Let Plotly auto-shrink margins to fit ticks/titles
        fig.update_xaxes(automargin=True, title_standoff=4, ticks="outside", ticklen=6)
        fig.update_yaxes(automargin=True, title_standoff=6, ticks="outside", ticklen=6)


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
    
    def _fit_color(self) -> str:
        """Red for fits; if a data curve already uses that exact red, pick a nearby red."""
        FIT_RED = "#E11D48"   # rose-600
        ALT_RED = "#DC2626"   # red-600
        used = {str(c.color) for c in self.curves.values() if c.isAttached() and c.color}
        return FIT_RED if FIT_RED not in used else ALT_RED

    def _add_overlay(self, trace: go.Scatter, tag: str):
        """Add/replace a single-tag overlay trace."""
        # remove any existing with same tag
        self._overlays = [t for t in self._overlays if getattr(t, "meta", None) != tag]
        self._overlays.append(trace)
        self.queue_replot()

    def _clear_overlays(self, tag_prefix: str | None = None):
        """Clear overlays; if prefix given, clear only those with that prefix."""
        if tag_prefix is None:
            self._overlays.clear()
        else:
            self._overlays = [t for t in self._overlays
                            if not str(getattr(t, "meta", "")).startswith(tag_prefix)]
        # also remove any fit annotation
        self._canvas.remove_annotations_with_meta("ann::fit")
        self.queue_replot()

    # ------------------------- Printing / Export -------------------------
    def printOrExport(self, parent=None):
        """
        Save Plotly plot as PDF/PNG/SVG/JPEG.
        Always opens in the user's home directory.
        """
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from pathlib import Path
        import os

        # Start in user's home directory
        home_dir = str(Path.home())

        filters = "PDF (*.pdf);;PNG (*.png);;SVG (*.svg);;JPEG (*.jpg);;All files (*)"
        filename, selected_filter = QFileDialog.getSaveFileName(
            parent,
            "Save Plot",
            home_dir,   # <- start here
            filters
        )
        if not filename:
            return

        # Infer extension if missing
        ext = Path(filename).suffix.lower()
        if not ext:
            if "pdf" in selected_filter.lower():
                ext = ".pdf"
            elif "svg" in selected_filter.lower():
                ext = ".svg"
            elif "jpg" in selected_filter.lower() or "jpeg" in selected_filter.lower():
                ext = ".jpg"
            else:
                ext = ".png"
            filename += ext

        # Handle PDF via Qt printer (vector-safe)
        if ext == ".pdf":
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtGui import QPainter
            from PySide6.QtCore import QSize

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)

            pix = self._web.grab()
            painter = QPainter(printer)

            page_rect = printer.pageRect(QPrinter.DevicePixel)
            target_size = QSize(int(page_rect.width()), int(page_rect.height()))

            scaled = pix.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            x = (target_size.width() - scaled.width()) // 2
            y = (target_size.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

            painter.end()
            print(f"[EXPORT] Wrote PDF via Qt: {filename}")
            return

        # Other formats (PNG, SVG, JPG) via Plotly/kaleido
        try:
            self._export_current_plot(filename, format=ext.lstrip("."))
            print(f"[EXPORT] Wrote {filename} via kaleido")
        except Exception as e:
            print(f"[EXPORT] Kaleido export failed: {e}, fallback to raster grab")
            pix = self._web.grab()
            if not pix.save(filename):
                QMessageBox.warning(parent, "Save failed", f"Could not save to {filename}")


    def _export_current_plot(self, filename: str, format: str = "png"):
        import plotly.graph_objects as go
        import plotly.io as pio

        traces = []
        for c in self.curves.values():
            if c.isAttached():
                tr = c.to_trace()
                if tr:
                    traces.append(tr)
        if self._overlays:
            traces.extend(self._overlays)
        if not traces:
            traces = [go.Scatter(x=[0, 1], y=[0, 1], mode="lines",
                                line=dict(width=0), showlegend=False, hoverinfo="skip", name="")]

        fig = go.Figure(data=traces)
        cols = self._theme_colors()
        fig.update_layout(
            paper_bgcolor=cols["paper"],
            plot_bgcolor=cols["plot"],
            margin=dict(l=50, r=20, t=30, b=40),
        )
        if format == "pdf":
            pio.write_image(fig, filename, format="pdf", width=1920, height=1080, scale=2)
        else:
            pio.write_image(fig, filename, format=format, width=1280, height=720, scale=2)


    def printPlot(self, title="", printer=None, filename=None):
        # Legacy compatibility.
        if filename:
            self.printOrExport()
            return

        from PySide6.QtPrintSupport import QPrinter, QPrintDialog
        from PySide6.QtGui import QPainter

        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer)
        if dlg.exec() == QPrintDialog.Rejected:
            return

        pix = self._web.grab()
        painter = QPainter(printer)
        painter.drawPixmap(0, 0, pix)
        painter.end()
        print("[PRINT] Sent plot to printer")


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
