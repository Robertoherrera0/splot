#!/usr/bin/env python
#***********************************************************************
#
#  @(#)SpecPlot2D.py	3.11  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2016,2017,2018,2020,2023,2024
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


from pyspec.css_logger import log
from pyspec.graphics.QVariant import *
from pyspec.graphics import qt_variant, mpl_version_no

from Constants import *
import numpy as np
import math

from Features import features, setFeature
from Preferences import Preferences

from pyspec.graphics.QVariant import mpl_backend

#if qt_variant() in ["PyQt6", "PySide6"]:
    #import matplotlib.backends.backend_qtagg as backend
#elif qt_variant() in ["PyQt5", "PySide2"]:
    #import matplotlib.backends.backend_qt5agg as backend
#else:
    #import matplotlib.backends.backend_qt4agg as backend

try:
    # only matplotlib is supported
    FigureCanvas = mpl_backend.FigureCanvasQTAgg
    from matplotlib.figure import Figure
    #from matplotlib.gridspec import GridSpec
    import matplotlib.colorbar as colorbar
    from matplotlib import pyplot 
    from matplotlib.ticker import AutoLocator, MaxNLocator, LinearLocator, FormatStrFormatter, ScalarFormatter
    from matplotlib import patches
    try:
        from matplotlib import tri
        setFeature("2D_triangles", True)
    except:
        setFeature("2D_triangles", False)
    #from mpl_toolkits.mplot3d import Axes3D
    if mpl_version_no() < [2,0,0]:
        from matplotlib.mlab import griddata
    setFeature("2D", True) 
except ImportError:
    log.log(3,"Cannot import modules for 2D plotting. Feature inactive")
    import traceback
    log.log(3,"traceback is: %s" % traceback.format_exc())
    setFeature("2D", False) 

grid_interp_method = None

if mpl_version_no() >= [2,0,0]:
    grid_interp_method = 'tri'

if grid_interp_method is None:
    try:
        from mpl_toolkits import natgrid
        grid_interp_method = 'nn' 
    except ImportError:
        pass

if grid_interp_method is None:
   try:
       if mpl_version_no() < [1,4,0]: # delaunay deprecated after
           from matplotlib import delaunay
           grid_interp_method = 'nn'
   except ImportError:
        pass

# between matplotlib 1.4.0 and matplotlib 2.0.0 hopefully 'linear' works
if grid_interp_method is None:
    grid_interp_method = 'linear'

log.log(3,"INTERPOLATION method for irregular data:  %s" % grid_interp_method)

class SpecPlot2D(QWidget):

    def __init__(self,parent,*args):
        self.parent = parent
        QWidget.__init__(self,*args)

        self.datablock = None
        self.prefs = Preferences()

        self.zdata = None
        self.xdata = None
        self.ydata = None

        self.zlabel = None
        self.xlabel = None
        self.ylabel = None

        self.tolerance_factor = 0.498  # in percentage for scattered plots

        self.x_self_tol = 1.0
        self.y_self_tol = 1.0
        
        self.data_type = "scattered"
        self.style_2d = self.prefs.getValue("style_2d","scatter")

        self.double_clicked = False

        self._layout = QVBoxLayout()
        self.fig = Figure()

        #self.gs = GridSpec(3,3)
        #self.gs.update(wspace=0.5, hspace=0.5)


        # create a qt widget that contains the figure
        self.figcanvas = FigureCanvas(self.fig)
        self.figcanvas.setParent(self)
        self.figcanvas.setFocusPolicy(Qt.StrongFocus)
        self.figcanvas.setFocus()

        self.figcanvas.mpl_connect("motion_notify_event", self.mouse_moved)
        self.figcanvas.mpl_connect("button_press_event", self.mouse_clicked)
        self.figcanvas.mpl_connect("button_release_event", self.mouse_released)
        self.figcanvas.mpl_connect("key_press_event", self.key_pressed)

        self.coordlab = QLabel()
        self._layout.addWidget(self.figcanvas)
        self._layout.addWidget(self.coordlab)

        self.figcanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setLayout(self._layout)

        self._setShowGraphs(False, init=True)

        self.selecting = False

    def _format_axes(self):
        self.xx_locator = MaxNLocator(nbins=4)
        self.xy_locator = MaxNLocator(nbins=4)
        #self.xy_locator = LinearLocator(numticks=4)
        self.yx_locator = MaxNLocator(nbins=4)
        self.yy_locator = MaxNLocator(nbins=4)

        self.x2d_locator = MaxNLocator(nbins=6)
        self.y2d_locator = MaxNLocator(nbins=6)

        self.tick_formatter = FormatStrFormatter("%6.3g")

        self.axes_2d.xaxis.set_major_locator(self.x2d_locator)
        self.axes_2d.yaxis.set_major_locator(self.y2d_locator)

        #x2d_formatter = FormatStrFormatter("%6.3g")
        #y2d_formatter = FormatStrFormatter("%6.3g")
        x2d_formatter = ScalarFormatter(useOffset=False)
        y2d_formatter = ScalarFormatter(useOffset=False)

        self.axes_2d.xaxis.set_major_formatter(x2d_formatter)
        self.axes_2d.yaxis.set_major_formatter(y2d_formatter)

        self.x_plot.xaxis.set_major_locator(self.xx_locator)
        self.x_plot.yaxis.set_major_locator(self.xy_locator)
        self.y_plot.xaxis.set_major_locator(self.yx_locator)
        self.y_plot.yaxis.set_major_locator(self.yy_locator)

        self.y_plot.xaxis.set_major_formatter(self.tick_formatter)

    def setDataBlock(self,datablock):
        if datablock is self.datablock:
            return

        #if self.datablock:
        #    self.datablock.unsubscribe(self)

        # Connect with changes on associated dataSource

        self.datablock = datablock

    def updateData(self):
        log.log(3,"updating image data")
 
    def _dataChanged(self):

        zdat = self.datablock.getDataColumn(self.zsel)  
        xdat = self.datablock.getDataColumn(self.xsel)  
        ydat = self.datablock.getDataColumn(self.ysel)  

        self.setData(zdat, xdat, ydat, columnnames=[self.zsel,self.xsel,self.ysel])

    def _update_dblock(self):
        xsel = self.datablock.getXSelection()
        self.zsel = self.datablock.getYSelection()[0]
        if len(xsel) == 2:
            self.xsel, self.ysel = xsel
        self._dataChanged()

    def _columnSelectionChanged(self, xsel, y1sel, y2sel):
        self.xsel = xsel[0]
        self.ysel = xsel[1]
        self.zsel = y1sel[0]
        #self.zsel = self.datablock.getYSelection()[0]

        self._dataChanged()
        log.log(3,"column selection changed")

    def setShowGraphs(self, show=True, init=False):
        self._setShowGraphs(show,init)
        self._update()

    def _setShowGraphs(self, show, init):
        if init:
            try:
                self.axes_2d = self.fig.add_subplot(3,2,(1,4))
                #self.cb_axes, kw1 = colorbar.make_axes(self.axes_2d, location='right')
                self.x_plot = self.fig.add_subplot(3,2,5)
                self.y_plot = self.fig.add_subplot(3,2,6)
                self.axes_2d.tick_params(labelsize=10)
                self.x_plot.tick_params(labelsize=8)
                self.y_plot.tick_params(labelsize=8)
            except TypeError:  # I should check the matplotlib version here
                self.axes_2d = self.fig.add_subplot(2,1,1)
                self.x_plot = self.fig.add_subplot(2,2,3)
                self.y_plot = self.fig.add_subplot(2,2,4)


        #self.axes_2d.set_visible(True)
        #self.cb_axes.set_visible(True)
        self.x_plot.set_visible(True) 
        self.y_plot.set_visible(True)

    def setDataType(self, data_type):
        if self._setDataType(data_type):
            self._update()

    def _setDataType(self, data_type):
        if data_type != self.data_type:
            self.data_type = data_type
            return True
        else:
            return False

    def set2DStyle(self, style_2d):
        log.log(3,"setting 2D Style was: %s / setting it to %s" % (self.style_2d, style_2d))
        if self._set2DStyle(style_2d):
            self._update()

    def _set2DStyle(self, style_2d):
        if style_2d != self.style_2d:
            self.style_2d = style_2d
            self.prefs.setValue("style_2d",self.style_2d)
            return True
        else:
            return False

    def setColumnNames(self, zlabel, xlabel=None, ylabel=None):
        self._setColumnNames(zlabel, xlabel, ylabel)
        self.figcanvas.draw()

    def _setColumnNames(self, zlabel, xlabel, ylabel):
        self.xlabel = (xlabel is not None) and xlabel or ""
        self.ylabel = (ylabel is not None) and ylabel or ""
        self.zlabel = (zlabel is not None) and zlabel or ""
        self._update_labels()

    def setData(self,zdat,xdat=None,ydat=None, data_type=None, columnnames=None):

        if columnnames:
             zlab, xlab, ylab = columnnames
             self._setColumnNames(zlab, xlab, ylab)

        self.zdata = zdat

        if data_type is not None:
            self._setDataType(data_type)
        else:
            self._setDataType("scattered")

        if xdat is not None:
            self.xdata = xdat
        else:
            self.xdata = None

        if ydat is not None:
            self.ydata = ydat
        else:
            self.ydata = None
 
        self._update()

    def setShape(self, shape):
        if len(shape) == 2:
            self.xdim, self.ydim = shape
            self._update()

    def _setZData(self, zdata):
         xdim, ydim = zdata.shape

    def _update(self):

        plt = None
        self.axes_2d.clear()

        if self.zdata is None or not self.zdata.any():
            return

        # 
        # Prepare data
        # 
  

            # tolerance
        if self.xdata is not None:
            xvalues = np.unique(self.xdata)
            xvalues.sort()
            dist = [xvalues[i+1] - xvalues[i] for i in range(len(xvalues) - 1) ]
            x_ave_dist = np.mean(dist)
            self.x_sel_tol = x_ave_dist * self.tolerance_factor # is the discrimination value to select values in list

        if self.ydata is not None:
            yvalues = np.unique(self.ydata)
            yvalues.sort()
            dist = [yvalues[i+1] - yvalues[i] for i in range(len(yvalues) - 1) ]
            y_ave_dist = np.mean(dist)
            self.y_sel_tol = y_ave_dist * self.tolerance_factor

            # prepare data in a grid if needed (x,y,z) 

        if self.style_2d in ["contour", "wireframe", "image", "3dsurface"]:
            code, xi, yi, zi = self.gridify(self.xdata, self.ydata, self.zdata)
            grid_ok = (code > 0) and True or False

        # 
        # Prepare data END
        # 

        self.axes_2d.set_xlabel(self.xlabel)
        self.axes_2d.set_ylabel(self.ylabel)
        self.axes_2d.set_title(self.zlabel)

        show_points = False


        if self.data_type == "scattered" or self.data_type == "mesh":
             zmax = self.zdata.max()
             zdat = self.zdata
             
             xbeg, xend = self.xdata.min(), self.xdata.max()
             ybeg, yend = self.ydata.min(), self.ydata.max()

             style_2d = self.style_2d

             if xbeg == xend or ybeg == yend:
                 style_2d = "scatter"

             if style_2d == "scatter":  # allow for extra space for correct viewing of scatter dots
                xrang = xend - xbeg
                xmarg = xrang * 0.05
                yrang = yend - ybeg
                ymarg = yrang * 0.05
                xbeg, xend = xbeg-xmarg,  xend+xmarg
                ybeg, yend = ybeg-ymarg, yend+ymarg

             self.axes_2d.set_xlim([xbeg,xend])
             self.axes_2d.set_ylim([ybeg,yend])

             if style_2d == "contour":
                 if grid_ok:
                     plt = self.axes_2d.contour(xi, yi, zi, 6, colors='k')
                     self.axes_2d.clabel(plt, fmt="%.3g", fontsize=9, inline=1)
                     plt = self.axes_2d.contourf(xi, yi, zi, cmap=pyplot.cm.jet)
             elif style_2d == "triangles":
                 min_radius = 0.25
                 triang = tri.Triangulation(self.xdata,self.ydata)
                 xmid = self.xdata[triang.triangles].mean(axis=1)
                 ymid = self.ydata[triang.triangles].mean(axis=1)
                 mask = np.where(xmid*xmid + ymid*ymid < min_radius*min_radius, 1, 0)
                 triang.set_mask(mask)
                 plt = self.axes_2d.tripcolor(triang, self.zdata, shading='flat')
             elif style_2d == "wireframe":
                 if grid_ok:
                     plt = self.axes_2d.plot_wireframe(xi, yi, zi)
                     #self.axes_2d.clabel(plt, fontsize=9, inline=1)
             elif style_2d == "3dsurface":
                 if grid_ok:
                     plt = self.axes_2d.plot_surface(xi, yi, zi)
                     #self.axes_2d.clabel(plt, fontsize=9, inline=1)
             elif style_2d == "image":
                 zdat = np.flipud(zi)
                 if grid_ok:
                     plt = self.axes_2d.imshow(zdat, extent=(xi.min(), xi.max(), \
                        yi.min(), yi.max()), aspect="auto", interpolation='nearest')
             else:  # only scattered. point size correspond to value
                 area = np.pi * (10 * self.zdata/zmax)**2  
                 plt = self.axes_2d.scatter(self.xdata, self.ydata , c=zdat, s=area, alpha=0.5)
                 show_points = False

        elif self.data_type == "image":
             zdat = self.zdata
             im = self.axes_2d.imshow(zdat, extent=(xdat.min()-0.5, xdat.max()+0.5, \
                        ydat.min()-1, ydat.max()+1), aspect="auto", interpolation='nearest')

        if show_points:
            self.axes_2d.scatter(self.xdata, self.ydata, c='b', marker='o', s=5)

        if plt:
            self._format_axes()
            self.fig.subplots_adjust(wspace=0.3,bottom=0.1, right=0.85, left=0.1, top=0.9, hspace=0.6)

            # add colorbar
            cax = self.fig.add_axes([0.9, 0.1, 0.01, 0.8])
            try:
                cax.tick_params(labelsize=10)
            except:
                pass
            self.fig.colorbar(plt, cax=cax)

            self.figcanvas.draw()

        # This line is meant to update the x_plot while data is arriving. Do not use it yet
        #self.set_x_plot(self.ydata[-1])

    def mouse_clicked(self,ev):
        self.last_rect = None
        if not ev.inaxes:
            return

        self.moved = 0

        if ev.inaxes == self.axes_2d:
            if ev.button == 3: # right button
                self._update()
                return

        if ev.inaxes == self.x_plot:
            #if ev.dblclick:
                #log.log(3,"Double clicked on x plot")
            return

        if ev.inaxes == self.y_plot:
            #if ev.dblclick:
                #log.log(3,"Double clicked on y plot")
            return


        #if ev.dblclick:
            #self.double_clicked = True
            #self.setShowGraphs(False)
            #return

        self.selecting = True
        self.xbeg = ev.xdata
        self.ybeg = ev.ydata

    def mouse_released(self,ev):
        self.selecting = False

        if self.last_rect:
            self.last_rect.remove()

        if ev.button == 1:
            if self.moved > 0:
                self.axes_2d.set_xlim([self.xbeg, self.xend])
                self.axes_2d.set_ylim([self.ybeg, self.yend])
                self.figcanvas.draw()
            elif not self.double_clicked: 
                self._update_graphs(ev)
        self.double_clicked = False

    def key_pressed(self,ev):
        log.log(3, "key pressed: " + str(ev.key) )

    def _update_labels(self):
        self.axes_2d.set_xlabel(self.xlabel, fontsize=12)
        self.axes_2d.set_ylabel(self.ylabel, fontsize=12)
        self.axes_2d.set_title(self.zlabel, fontsize=12)

        self.x_plot.set_xlabel(self.xlabel, fontsize=10)
        self.x_plot.set_ylabel(self.zlabel, fontsize=10)

        self.y_plot.set_xlabel(self.ylabel, fontsize=10)
        self.y_plot.set_ylabel(self.zlabel, rotation="vertical", fontsize=10)

        self._format_axes()

    def _update_graphs(self,ev):

         if self.data_type == "scattered":
              x_sel, y_sel = ev.xdata, ev.ydata
              
              self.set_x_plot(y_sel)
              self.set_y_plot(x_sel)

         #self.setShowGraphs(True)

         self.figcanvas.draw()

    def set_x_plot(self, y_sel):
        xd = [];zdx=[]

        for ptno in range(len(self.zdata)):
            xval = self.xdata[ptno]
            yval = self.ydata[ptno]
            zval = self.zdata[ptno]

            if abs(yval - y_sel) <  self.y_sel_tol:
                xd.append(xval); zdx.append(zval)

        # sort xd, zdx together
        xa = np.array(xd); zax = np.array(zdx) 
        si = xa.argsort() # get indexes after sorting
        xa = xa[si]
        zax = zax[si]

        self.x_plot.clear()
        self.x_plot.plot(xa,zax, marker="o")
        self.x_plot.set_title("at %s=%3g " % (self.ylabel,y_sel), fontsize=10)

    def set_y_plot(self, x_sel):
        yd = [];zdy=[]

        for ptno in range(len(self.zdata)):
            xval = self.xdata[ptno]
            yval = self.ydata[ptno]
            zval = self.zdata[ptno]

            if abs(xval - x_sel) <  self.x_sel_tol:
                yd.append(yval); zdy.append(zval)

        ya = np.array(yd); zay = np.array(zdy) 
        si = ya.argsort() # get indexes after sorting
        ya = ya[si]
        zay = zay[si]

        self.y_plot.clear()
        self.y_plot.plot(ya,zay, marker="o")
        self.y_plot.set_title("at %s=%3g " % (self.xlabel,x_sel), fontsize=10)

    def mouse_moved(self,ev):
        # if selecting draw rectangle while moving

        if not ev.inaxes:
            return

        if ev.inaxes == self.x_plot or ev.inaxes == self.y_plot:
            return

        if self.selecting:
            self.moved += 1
            self.xend, self.yend = ev.xdata, ev.ydata
            width = self.xend - self.xbeg
            height = self.yend - self.ybeg
            if self.last_rect:
                self.last_rect.remove()
            self.last_rect = self.axes_2d.add_patch(patches.Rectangle( (self.xbeg, self.ybeg), width, height, linewidth=3, color="red", fill=False) )
            self.figcanvas.draw()

        xval = ev.xdata
        yval = ev.ydata
        zval = "N/A"
        dist = 10e6

        for ptno in range(len(self.zdata)):
            zv = self.zdata[ptno]
            xv = self.xdata[ptno]
            yv = self.ydata[ptno]
            if abs(xv-xval) < self.x_sel_tol:
                if abs(yv-yval) < self.y_sel_tol:
                    newdist = (xv-xval)*(xv-xval) + (yv-yval)*(yv-yval)
                    if newdist < dist:
                        zval = "%8.3g" % zv

        pos_str = "x=%8.3g  y=%8.3g  z=%s" % (xval,yval,zval)
        self.coordlab.setText(pos_str)

    def find_canvas_xy_values(self,ev):
        inv = self.axes_2d.transData.inverted()

    def find_canvas_indexes(self,ev):
        inv = self.axes_2d.transAxes.inverted()
        x_ax, y_ax = inv.transform((ev.x, ev.y))  # find axes position from pixel coord.

        x_idx = int(math.floor(x_ax * len(self.xdata))) # find index in array
        y_idx = int(math.floor(y_ax * len(self.ydata))) # find index in array
          
        return x_idx, y_idx

    def gridify(self, xdat, ydat, zdat):

        xvals = np.unique(xdat)
        yvals = np.unique(ydat)
    
        if len(xvals) * len(yvals) == len(zdat):
            # perfect square of data
            xvals.sort()
            yvals.sort()
            xi = xvals; yi = yvals
    
            xl = list(xi)
            yl = list(yi)
    
            zi = np.empty((len(yvals),len(xvals)))
    
            for ptno in range(len(zdat)):
                xidx =  xl.index( xdat[ptno] )
                yidx =  yl.index( ydat[ptno] )
                zi[yidx,xidx] = zdat[ptno]
            code = 1
    
        elif len(xdat) == len(ydat) and len(xdat) == len(zdat):
            log.log(3,"irregular linear data %s / %s" % (len(xdat), len(ydat)) )
            npoints = len(xvals)
            xi = np.linspace(xdat.min(), xdat.max(), npoints)
            yi = np.linspace(ydat.min(), ydat.max(), npoints)
            zi = np.empty((len(yvals),len(xvals)))
            if grid_interp_method == "tri":
                xi, yi = np.meshgrid(xi,yi)
                triang = tri.Triangulation(xdat,ydat)
                interp_z = tri.CubicTriInterpolator(triang,zdat,kind='min_E')
                zi = interp_z(xi,yi)
            else:
                zi = griddata(xdat, ydat, zdat, xi, yi, interp=grid_interp_method)
            code = 2
        else:
            code = -1
    
        if code == 0:
            xi = yi = zi = None
    
        return code, xi, yi, zi

    def saveAsImage(self, filename,title):
        self.savefig(title, filename)

    def savefig(self, title,filename):
        from textwrap import wrap

        slines = []
        for line in title.split("\n"):
            slines.extend(wrap(line,60))
        title = "\n".join(slines)

        title_art = self.axes_2d.set_title(title)
 
        title_art.set_y(1.05)
        self.fig.subplots_adjust(top=0.8)
        self.fig.savefig(filename)
        self.axes_2d.set_title('')
        self.fig.subplots_adjust(top=0.95)
        self.figcanvas.draw()

def main():

    # standalone test.  Try  
    #    python SpecImageDisplay.py --pyqt4 --matplotlib <spec> <arrname>
    #
    import sys
    import numpy as np
    app = QApplication([])  
    win = QMainWindow()
    dis = SpecPlot2D(win)
    win.setCentralWidget(dis) 
    win.show()

    if "file" in sys.argv:
        testfile(dis)
    else:
         # scatter
         xdat = np.array([1,2,3,4]*4)
         ydat = np.array([10,]*4 + [12,]*4 + [14,]*4 + [16,]*4)
         zdat = np.array(range(16))*20 - 10.0
         dis.setData(zdat,xdat,ydat,columnnames=["Detector","TZ3","TX3"])

         # mesh
         #xdat = np.array([1,2,3,4])
         #ydat = np.array([10,12,14,16])
         #zdat = np.array(np.random.rand(16)) * 30
         #zdat = np.array([range(0,4), range(4,8), range(8,12), range(12,16)])*2
         ##zdat = np.array([range(0,4), range(4,8), np.empty(4), np.empty(4)])*2
         ##zdat = np.empty((4,4))
         #dis.setColumnNames("TZ3","TX3","Detector")
         #dis.setData(zdat, xdat,ydat,"mesh")
     
    try:
        exec_ = getattr(app,"exec_")
    except AttributeError:
        exec_ = getattr(app,"exec")

    sys.exit(exec_())

def testfile(dis):
    from pyspec.file.spec import FileSpec
    from DataBlock import DataBlock

    fs = FileSpec("../data/mesh.dat")
    scan = fs[0]
    data = scan.getData()
    labels = scan.getLabels()
    
    dblock = DataBlock()
    dblock.setData(data, labels)
    dblock.setMode2D(True)
    
    xsel = ["TX3", "TZ3"]
    y1sel = ["If1"]
    y2sel = None

    dblock.setXSelection(xsel)
    dblock.setY1Selection(y1sel)

    dis.setDataBlock(dblock)
    dis._columnSelectionChanged(xsel, y1sel, y2sel)
    dis._dataChanged()
    #dis.set2DStyle("image")
    dis.set2DStyle("contour")
    #dis.set2DStyle("scatter")
    #dis.setShowGraphs(True)
    #dis.set2DStyle("contour")
    #dis.set2DStyle("3Dsurface")

    #xdat = dblock.getDataColumn("TZ3")
    #ydat = dblock.getDataColumn("TX3")
    #zdat = dblock.getDataColumn("If1")
    #dis.setData(zdat,xdat,ydat, data_type="scattered", columnnames=["Detector", "TZ3", "TX3"])

if __name__ == '__main__':
    main()
