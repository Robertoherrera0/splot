#******************************************************************************
#
#  @(#)Colormap.py	3.4  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2020,2021,2023,2024
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


from pyspec.graphics import qt_variant
from pyspec.graphics.QVariant import *
from pyspec.graphics.matplotlib_import import mpl_backend

from pyspec.css_logger import log

import numpy as np

# if qt_variant() in ["PySide6", "PyQt6", "PyQt5", "PySide2"]:
#    import matplotlib.backends.backend_qt5agg as mpl_backend
# else:
#    import matplotlib.backends.backend_qt4agg as mpl_backend

FigureCanvas = mpl_backend.FigureCanvasQTAgg

from matplotlib.figure import Figure
from matplotlib.colors import Normalize, LogNorm

class Colormap(QObject):

    default_cmap = 'hot'
    default_cmaplist = ["hot", "cool", "ocean", 
                        "terrain", "Spectral", "coolwarm", 
                        "binary","gray", "twilight", "hsv", 
                        "spring", "summer", "autumn", "winter", 
                        "nipy_spectral","gist_rainbow", "gist_ncar",
                        ]

    colormapChanged = pyqtSignal()

    def __init__(self, **values):

        super(Colormap,self).__init__()
        if values is None:
            values = {}

        _high_limit = values.get('high_limit', None)
        _low_limit = values.get('low_limit', None)

        _min_value = values.get('minval', None)
        _max_value = values.get('maxval', None)

        # init properties
        self._colormap = values.get('colormap', self.default_cmap)
        self._cmaplist = values.get('colormaps', self.default_cmaplist)
        self._limits = (_low_limit, _high_limit)
        self._range = (_min_value, _max_value)
        self._autoscale = values.get('autoscale', True)
        self._logarithmic = values.get('logarithmic', False)

        if self._autoscale is False:
            if None in self._limits: 
                log.log(1, "Colormap.py. Disabling autoscale requires limits to be provided")

        self._update_norm()

    @property
    def cmaplist(self):
        return self._cmaplist

    @cmaplist.setter
    def cmaplist(self, cmaplist):
        self._cmaplist = cmaplist
        self._changed()

    @property
    def autoscale(self):
        return self._autoscale

    @autoscale.setter
    def autoscale(self, autoscale):
        if isinstance(autoscale, bool) and \
             autoscale != self._autoscale:
                self._autoscale = autoscale
                self._update_norm()

    @property
    def logarithmic(self):
        return self._logarithmic

    @logarithmic.setter
    def logarithmic(self, logarithmic):
        if isinstance(logarithmic, bool) and \
             logarithmic != self._logarithmic:
                 self._logarithmic = logarithmic
                 self._update_norm()

    @property
    def colormap(self):
        return self._colormap

    @colormap.setter
    def colormap(self, colormap):
        if colormap in self.cmaplist and colormap != self._colormap:
            self._colormap = colormap
            self._changed()
        else:
            log.log(2,"unknown colormap name %s" % colormap)

    @property
    def datarange(self):
        return self._range

    @datarange.setter
    def datarange(self, *args):
        minval, maxval = args[0]
        if (minval,maxval) != self._range:
            self._range = (minval, maxval)
           
            if self._autoscale:
                self._update_norm()

    @property
    def limits(self):
        return self._limits

    @limits.setter
    def limits(self, *args):
        low, high = args[0]
        if (low,high) != self._limits:
            self._limits = (low, high)
            if self._limits != self._range:
                self.autoscale = False
            self._update_norm()

    @property
    def norm(self):
        return self._norm

    def _update_norm(self):
        if self._autoscale:
            self._limits = tuple(self._range)

        nmin, nmax = self._limits

        if self._logarithmic and (nmin > 0) and (nmax > 0):
            self._norm = LogNorm(vmin=nmin, vmax=nmax)
        else:
            self._norm = Normalize(vmin=nmin, vmax=nmax)

        self._changed()

    def copy_from(self, colormap):
        self._limits = tuple(colormap.limits)
        self._range = tuple(colormap.datarange)
        self._colormap = colormap.colormap
        self._autoscale = colormap.autoscale
        self._cmaplist = colormap.cmaplist
        self._logarithmic = colormap.logarithmic
        self._update_norm()

    def update(self, autoscale=None, limits=None, datarange=None, colormap=None):
        changed = False
        
        if autoscale is not None and autoscale != self._autoscale:
            self._autoscale = autoscale
            changed = True

        if datarange is not None and datarange != (self._range):
            self._range = tuple(datarange)
            if self._autoscale:
                changed = True

        if limits is not None and limits != (self._limits):
            self._limits = tuple(limits)
            if not self._autoscale:
                changed = True

        if colormap is not None and colormap != self._colormap:
            self._colormap = colormap
            changed = True

        if changed:
            self._changed()

    def _changed(self):
        self.colormapChanged.emit()

class ColormapDialog(QDialog):

    def __init__(self,colormap,parent=None,data=None,*args):

        super(ColormapDialog, self).__init__(parent,*args)

        self.data = data
        self._lmin, self._lmax = [None,None]

        self.setModal(False)

        self.build_dialog()
        self.resize(200,420)

        self.block_update = True
        self.set_colormap(colormap)

        self.block_update = False
        self._update()

        # interaction
        self.moving_point = False

    def build_dialog(self):
        layout = QVBoxLayout()

        self.fig  = Figure()
        self.fig2  = Figure()

        self.cmap_canvas = FigureCanvas(self.fig2)
        self.cmap_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.cmap_ax = self.fig2.add_subplot(111)
        self.cmap_canvas.setFixedHeight(30)
        self.cmap_ax.axis("off")
        self.cmap_ax.margins(0)
        self.cmap_init = False

        self.graph_canvas = FigureCanvas(self.fig)
        self.graph_ax = self.fig.add_subplot(111)
        self.graph_ax.yaxis.set_visible(False)

        self.graph_canvas.mpl_connect('key_press_event', self.mouse_move)
        self.graph_canvas.mpl_connect('button_press_event', self.mouse_clicked)
        self.graph_canvas.mpl_connect('button_release_event', self.mouse_released)
        self.graph_canvas.mpl_connect('motion_notify_event', self.mouse_move)

        self.combo_layout = QHBoxLayout()
        self.cmap_cmap = QLabel("Colormap:")
        self.cmap_combo = QComboBox()

        self.cb_layout = QHBoxLayout()
        self.show_cbar_cb = QCheckBox("Show colorbar")
        self.autoscale_cb = QCheckBox("Autoscale")
        self.logarithmic_cb = QCheckBox("Logarithmic")

        self.autoscale_cb.toggled.connect(self.autoscale_changed)
        # self.cb_layout.addWidget(self.show_cbar_cb)
        self.cb_layout.addWidget(self.autoscale_cb)
        self.logarithmic_cb.toggled.connect(self.logarithmic_changed)
        self.cb_layout.addWidget(self.logarithmic_cb)

        self.button_layout = QHBoxLayout()
        self.reset_button = QPushButton("Reset")
        self.cancel_button = QPushButton("Cancel")
        self.apply_button = QPushButton("Apply")

        self.reset_button.clicked.connect(self.reset_cmap)
        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.apply_button.clicked.connect(self.apply_clicked)

        self.button_layout.addWidget(self.reset_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.apply_button)

        self.combo_layout.addWidget(self.cmap_cmap)
        self.combo_layout.addWidget(self.cmap_combo)

        self.cmap_combo.currentIndexChanged.connect(self.combo_changed)

        layout.addWidget(self.cmap_canvas)
        layout.addLayout(self.combo_layout)
        layout.addWidget(self.graph_canvas)
        layout.addLayout(self.cb_layout)
        layout.addLayout(self.button_layout)
        self.setLayout(layout)

    def set_data(self,data):
        self.data = data

    def set_colormap(self, colormap):
        self.cmap = colormap
        self.cmap_backup = Colormap()
        self.cmap_backup.copy_from(colormap)
        self.cmap_combo.clear()
        self.cmap_combo.addItems(self.cmap.cmaplist)
        self.cmap.colormapChanged.connect(self._update)

    def combo_changed(self, idx):
        if self.block_update:
            return

        self.cmap.colormap = self.cmap_combo.currentText()

    def mouse_clicked(self, ev):
        if not ev.inaxes:
            return

        # have we clicked near one of our points?
        xval = ev.xdata
        yval = ev.ydata

        self._lmin, self._lmax = self.cmap.limits

        if abs(yval - 1) < 0.15:
            self.moving_point = 'top'
            if xval > self._lmin:
                self._lmax = xval
            else:
                return
        elif abs(yval) < 0.15:
            self.moving_point = 'bottom'
            if xval < self._lmax:
                self._lmin = xval
            else:
                return
        else:
            return

        # if we get this far is because there was a change
        # self.cmap.limits = (lmin, lmax)

    def mouse_move(self, ev):
        if not self.moving_point:
            return

        if not ev.inaxes:
            return

        xval = ev.xdata

        self._lmin, self._lmax = self.cmap.limits
        _dmin, _dmax = self.cmap.datarange

        if self.moving_point == 'top':
            if xval > _dmax:
                self._lmax = _dmax
            elif xval > self._lmin:
                self._lmax = xval
            else:
                return
        elif self.moving_point == 'bottom':
            if xval < _dmin:
                self._lmin = _dmax
            elif xval < self._lmax:
                self._lmin = xval
            else:
                return
        else:
            return

    def mouse_released(self, ev):
        self.moving_point = False
        if None not in [self._lmin, self._lmax]:
            self.cmap.limits = (self._lmin, self._lmax)

    def key_pressed(self, ev):
        if ev.key == 'escape':
            self.cur_max = self.max_val
            self.cur_min = self.min_val
            self._update()

    def _update(self):
        if self.block_update:
            return

        self.autoscale_cb.setChecked(self.cmap.autoscale)
        self.update_cmap_canvas()
        self.update_graph_canvas()

    def autoscale_changed(self): 
        if self.block_update:
            return

        self.cmap.autoscale=self.autoscale_cb.isChecked()

    def logarithmic_changed(self): 
        if self.block_update:
            return

        self.cmap.logarithmic=self.logarithmic_cb.isChecked()

    def reset_cmap(self):
        self.cmap.copy_from(self.cmap_backup)

    def apply_clicked(self):
        self.accept()

    def cancel_clicked(self):
        self.reset_cmap()
        self.accept()

    def update_cmap_canvas(self):
        if not self.cmap_init:
            dmin, dmax = self.cmap.datarange
            stp = (dmax-dmin) / 250.0 # make 300 points 
            self.cmap_data = np.tile( np.arange(dmin, dmax, stp), (30,1))

        self.im = self.cmap_ax.imshow(self.cmap_data, cmap=self.cmap.colormap, \
                 norm=self.cmap.norm,interpolation='nearest')

        self.cmap_ax.set_aspect("auto")
        if not self.cmap_init:
            self.fig2.tight_layout(pad=0)
            self.cmap_init = True
        self.cmap_canvas.draw()

    def update_graph_canvas(self):
        dmin, dmax = self.cmap.datarange
        lmin, lmax = self.cmap.limits

        valrange = (dmax - dmin)
        side_d = valrange * 0.02

        x = [lmin, lmax]
        y = [0,1]

        xe = [dmin-side_d] + x + [dmax+side_d]
        ye = [0,0,1,1]

        self.graph_ax.clear()

        self.graph_ax.scatter(lmin,0,marker='>', color='red', alpha=1)
        self.graph_ax.scatter(lmax,1,marker='<', color='red', alpha=1)
        self.graph_ax.plot(xe,ye, color='#707070')

        if self.data is not None:
            nbins = 50
            rvl = self.data.ravel() # flatten values
            nhist = np.histogram(rvl,bins=nbins)[0]
            weights=np.ones(len(rvl))/nhist.max()
            self.graph_ax.hist(rvl, bins=nbins, weights=weights, fc='#6666cc')
            #self.hist_ax.hist(rvl, bins=nbins, weights=weights, range=(data.min(), data.max()), fc='#6666cc', ec='#6666cc')
            #self.graph_ax.hist(self.data.ravel()/self.data.max(), bins=100, range=(self.data.min(), self.data.max()), fc='#9999cc')

        midpos = dmin + valrange/2.9
        ecart = valrange/10.0

        xpos = (lmin < midpos) and (lmin+ecart) or (lmin-2*ecart)
        self.graph_ax.text(xpos, 0.07, "% 0.5g" % lmin, size=9,  \
                  bbox=dict(boxstyle='square,pad=0.1', fc='#c0c0f0'), color='black')

        xpos = (lmax < midpos) and (lmax+ecart) or (lmax-2*ecart)
        self.graph_ax.text(xpos, 0.9, "% 0.5g" % lmax, size=9, \
                  bbox=dict(boxstyle='square,pad=0.1', fc='#c0c0f0'), color='black')

        self.fig.subplots_adjust(left=0.01, bottom=0.1,top=0.99, right=0.99)
        self.graph_canvas.draw()


if __name__ == '__main__':
    from pyspec.client import spec_shm
    data = np.array(spec_shm.getdata('fourc','farr'))
    log.start()

    app = QApplication([])

    colormap = Colormap(minval=data.min(),maxval=data.max())
    #colormap.autoscale = True
    #colormap.limits = (40,120)

    #colormap.datarange = (20,400)


    diag = ColormapDialog(colormap, data=data)
    rvl = data.ravel()
    print(rvl.max(), data.max())
    redux = rvl / data.max()
    print( redux.shape, redux.max())
    diag.exec_()

    #app.exec_()
