#******************************************************************************
#
#  @(#)McaWidget.py	3.4  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2021,2022,2023,2024
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


import numpy as np
import time

try:
    from collections import OrderedDict
except ImportError:
    from pyspec.ordereddict import OrderedDict

from pyspec.graphics.QVariant import QApplication, QSize, QSizePolicy, \
        QWidget, QHBoxLayout, QVBoxLayout, QToolBar, QLabel, Qt, QLineEdit, \
        QIntValidator, pyqtSignal

from pyspec.graphics.QVariant import mpl_backend

from pyspec.css_logger import log, log_exception

from DialogTools import getPrinter, getSaveFile
from Preferences import Preferences
from Colormap import Colormap, ColormapDialog

import icons

from matplotlib.figure import Figure
from matplotlib import patches

from RoiSelectionDialog import RoiSelectionDialog

FigureCanvas = mpl_backend.FigureCanvasQTAgg

MODE_ZOOM, MODE_REGION = \
        (0,1)

NO_SELECTION, REGION = (0,1)

SELECTION_TYPE = {
        NO_SELECTION:   "None",
        REGION:   "Region",
        }

MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT = (0,1,2,3)

class McaWidget(QWidget):

    selectionUpdated = pyqtSignal(object, object)

    def __init__(self,parent=None,*args):

        self.current_action = None
        self.parent = parent 

        QWidget.__init__(self, *args)
        self.build_widget()

    def build_widget(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(18,18)) 

        self.horiz_action = self.toolbar.addAction(icons.get_icon('regionin'),"R", self.set_region_selection)
        self.horiz_action.setToolTip("Region selection")
        self.horiz_action.setCheckable(True)

        self.hozir_reset_action = self.toolbar.addAction(icons.get_icon('regionout'), "Reset Region", self.region_reset)
        self.hozir_reset_action.setCheckable(False)
        self.hozir_reset_action.setEnabled(False)

        self.toolbar.addSeparator()

        self.zoom_action = self.toolbar.addAction(icons.get_icon('zoom'), "Zoom", self.set_zoom_mode)
        self.zoom_action.setCheckable(True)
        self.zoom_action.setEnabled(True)

        self.zoomout_action = self.toolbar.addAction(icons.get_icon('zoomout'), "Zoom-", self.zoom_out)
        self.zoomout_action.setStatusTip('Zoom Out Plot')
        self.zoomout_action.setEnabled(False)

        self.zoomin_action = self.toolbar.addAction(icons.get_icon('zoomin'), "Zoom+", self.zoom_in)
        self.zoomin_action.setStatusTip('Zoom In Plot')
        self.zoomin_action.triggered.connect(self.zoom_in)
        self.zoomin_action.setEnabled(False)

        self.toolbar.addSeparator()
        self.print_action = self.toolbar.addAction(icons.get_icon('printer'),"P", self.printPlot)
        self.print_action.setToolTip("Print plot")
        self.print_action.setCheckable(False)

        self.canvas = McaCanvas(self)

        #try:
        #    cv_sizepol = QSizePolicy.Expanding |  QSizePolicy.Expanding
        #except NameError:
        #    cv_sizepol = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.canvas.selectionUpdated.connect(self.selection_updated)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=3)

    def highlight_point(self, x, y):
        self.canvas.highlight_point(x,y)
        self.canvas.show_cursor_values(x,y)

    def highlight_end(self):
        self.canvas.highlight_end()
        self.canvas.show_cursor_values()

    def set_description(self, *description):
        self.description = description  # it is a list of values (specname, varname)

    def selection_updated(self, selection_info, selection_data):
        self.selectionUpdated.emit(selection_info, selection_data)

    def select_action(self,action):
        if action == self.current_action:
            return

        if self.current_action:
            self.current_action.setChecked(False)

        self.current_action = action
        self.current_action.setChecked(True)

    def get_selection_mode(self):
        return self.canvas.get_selection_mode()

    def set_selection_mode(self, mode):
        self.canvas.set_selection_mode(mode)

    def set_selection_width(self, width):
        self.canvas.set_selection_width(width)

    def set_zoom_mode(self):
        if self.get_selection_mode() == MODE_ZOOM:
            self.canvas.reset_zoom()
        else:
            self.set_selection_mode(MODE_ZOOM)
            self.select_action(self.zoom_action)

    def zoom_out(self):
        pass

    def zoom_in(self):
        pass

    def set_region_selection(self):
        self.set_selection_mode(MODE_REGION)
        self.select_action(self.horiz_action)
        self.w_ledit.setEnabled(True) 

    def region_reset(self):
        pass

    def getPlot(self):
        return self.canvas

    def setData(self, xdata, ydata, metadata):
        self.xdata = np.array(xdata)
        self.ydata = np.array(ydata)

        self.metadata = metadata

        log.log(2, "MCA metadata is %s" % str(metadata))
        self.canvas.set_data(xdata,ydata,metadata)

    def setActive(self):
        self.active = True

    def setInactive(self):
        self.active = False

    def getTitle(self):
        return ":".join(self.description)

    def printPlot(self, mute=False, filename=None):
        self.prefs = Preferences()

        printer = getPrinter(self.prefs, mute, self, filename)

        if printer is None:
            log.log(1,"Cannot obtain a printer")
            return

        title = self.getTitle()
        self.canvas.printfig(printer,title, filename)

    def saveAsImage(self, filename=None):
        title = self.getTitle()

        if filename is None:
            filename = getSaveFile(self, prompt="Choose output file", \
                    filetypes="Image files (*.jpg *png);;ALL(*)")

        if not filename:
            return

        try:
            self.canvas.savefig(filename, title)
        except:
            import traceback
            log.log(2, traceback.format_exc())

class McaCanvas(QWidget):
     
    colors = {
            'zoom': 'cyan',
            'selection': 'green',
            'selection_bg': '#aaffaa',
            }

    default_xlabel = "Channel"
    default_ylabel = "Counts"

    move_by = 5 # percentage with arrow movements

    selectionUpdated = pyqtSignal(object, object)

    def __init__(self,*args):

        QWidget.__init__(self, *args)

        self.fulldata = None
        self.selected_data = None

        self.selection_mode = MODE_ZOOM
        self.selection_type = NO_SELECTION
        self.selection_position = None
        self.selecting = False

        self.zoomrect = None
        self.last_selrect = None
        self.last_line = None
        self.hl_mkr = None

        self.l_width = 1

        self.scroll_zoom_scale = 1.2

        self.xval = None
        self.yval = None
        self.zval = None

        self.x_dir = 1
        self.y_dir = 1

        self.selection_info = OrderedDict()

        self.build_widget()

    def build_widget(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.fig = Figure(facecolor='#f0f0f0')

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.position_label = QLabel()

        layout.addWidget(self.canvas)
        layout.addWidget(self.position_label)

        self.canvas.mpl_connect("motion_notify_event", self.mouse_moved)
        self.canvas.mpl_connect("button_press_event", self.mouse_clicked)
        self.canvas.mpl_connect("button_release_event", self.mouse_released)
        self.canvas.mpl_connect("key_press_event", self.key_pressed)
        self.canvas.mpl_connect("figure_leave_event", self.leave_event)

        self.mca_axes = self.fig.add_subplot(111)
        self.fig.tight_layout()


    def highlight_point(self, x, y):

        if self.hl_mkr:
            self.hl_mkr.remove()
            self.hl_mkr = None

        self.hl_mkr = self.mca_axes.scatter([x],[y], marker='o', color='green')
        self.canvas.draw()

    def highlight_end(self):
        if self.hl_mkr:
            self.hl_mkr.remove()
            self.hl_mkr = None
            self.canvas.draw()

    def set_data(self, xdata,ydata, metadata):

        self.metadata = metadata

        if isinstance(xdata, list):
            xdata = np.array(xdata)

        if isinstance(ydata, list):
            ydata = np.array(ydata)

        if len(ydata.shape) > 1:
            ydata = ydata[:,0]

        self.fulldata = np.stack([xdata,ydata])
        self.xdata, self.ydata = xdata, ydata
        self.update_data()

    def update_data(self):

        self.x_dir = 1
        self.y_dir = 1

        #if self.x_range[1] < self.x_range[0]:
        #    self.x_dir = -1
        #    self.x_range.sort()
#
#        if self.y_range[1] < self.y_range[0]:
#            self.y_range.sort()
#            self.y_dir = -1

        self._update_selection()
        self.refresh_plot()

    def refresh_plot(self):
        t0 = time.time()

        self.do_plot()

        if self.metadata is not None and self.metadata != "":
            xlabel = self.metadata.get('x', self.default_xlabel)
            ylabel = self.metadata.get('y', self.default_ylabel)
        else:
            xlabel = self.default_xlabel
            ylabel = self.default_ylabel

        self.mca_axes.set_xlabel(xlabel) # , fontsize=8)
        self.mca_axes.set_ylabel(ylabel) # , fontsize=8)
        self._display_selection()

        #self.fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
        self.canvas.draw()

        log.log(2, "Refreshing plot took %s" % (time.time()-t0))

    def do_plot(self):
        self.mca_axes.clear()
        self.p, = self.mca_axes.plot(self.xdata, self.ydata)

    def get_selection_mode(self):
        return self.selection_mode 

    def set_selection_mode(self, mode):
        self.selection_mode = mode

        if self.selection_mode != MODE_ZOOM:
            self.reset_selection()

    def mouse_clicked(self,ev):
        if not ev.inaxes:
            return

        if ev.button == 3:  # right click
            self.right_clicked = True
        else:
            self.xbeg = int(round(ev.xdata))
            self.ybeg = int(round(ev.ydata))

        if self.selection_mode == MODE_REGION:
            self.selecting = True
            self.apply_selection(MODE_REGION, self.ybeg)
        elif self.selection_mode == MODE_ZOOM:
            self.selecting = True
             
    def reset_selection(self):
        if self.last_selrect:
            self.last_selrect.remove()
            self.last_selrect = None

        if self.last_line:
            self.last_line.remove()
            self.last_line = None

    def mouse_moved(self,ev):

        xval = ev.xdata
        yval = ev.ydata

        if xval is None or yval is None:
            return

        if self.fulldata is None:
            return

        if self.selecting: 
            self.xend = int(round(xval))
            self.yend = int(round(yval))

            if self.xend < self.xbeg:
                xend = self.xbeg
                xbeg = self.xend
            else:
                xbeg = self.xbeg
                xend = self.xend

            if self.yend < self.ybeg:
                yend = self.ybeg
                ybeg = self.yend
            else:
                ybeg = self.ybeg
                yend = self.yend

            if self.selection_mode == MODE_ZOOM:
                self.display_zoomrect(self.xbeg, self.ybeg, self.xend, self.yend)
                self.display_selection()  # show selection if available

        self.show_cursor_values(xval)

    def mouse_released(self,ev):
        
        xval = ev.xdata
        yval = ev.ydata

        if self.selecting:
            self.selecting = False

        if xval is not None and yval is not None:
            self.xend = int(round(xval))
            self.yend = int(round(yval))

        if self.xend < self.xbeg: 
            xbeg, xend = self.xend, self.xbeg
        else:
            xend, xbeg = self.xend, self.xbeg

        if self.yend < self.ybeg: 
            ybeg, yend = self.yend, self.ybeg
        else:
            yend, ybeg = self.yend, self.ybeg

        width = xend - xbeg
        height = yend - ybeg

        if width < 1 and height < 1:
            return

        if self.selection_mode == MODE_ZOOM:

            #self.mca_axes.set_xlim([xbeg-0.5, xend+0.5])
            #self.mca_axes.set_ylim([ybeg-0.5, yend+0.5])
            self.mca_axes.set_xlim([xbeg, xend])
            self.mca_axes.set_ylim([ybeg, yend])

            if self.zoomrect:
                self.zoomrect.remove()
                self.zoomrect = None

            self.update_selection()
            self.canvas.draw()

    def key_pressed(self,ev):
        print("key pressed on mca. key is %s" % str(ev.key))

        if ev.key == 'escape':
            self.reset_zoom()
        elif ev.key == 'left':
            self.move_selection(MOVE_LEFT)
        elif ev.key == 'right':
            self.move_selection(MOVE_RIGHT)
            print("right")
        elif ev.key == 'up':
            self.move_selection(MOVE_UP)
        elif ev.key == 'down':
            self.move_selection(MOVE_DOWN)

    def leave_event(self, ev):
        self.show_cursor_values()

    def apply_selection(self, sel_type, selection_data):
        return
        if sel_type == MODE_HORIZ:
            self.horizontal_line(selection_data)
        elif sel_type == MODE_VERT:
            self.vertical_line(selection_data)
        elif sel_type == MODE_LINE:
            self.arbitrary_line(selection_data)
        elif sel_type == MODE_SQUARE:
            self.square_box(selection_data)

    def horizontal_line(self, ypos):
        half_width = int(self.l_width/2.0)

        beg_pos = ypos-half_width
        end_pos = int(beg_pos+self.l_width)

        # correct position at 
        if beg_pos < 0:
           beg_pos = 0
           end_pos = self.l_width
        elif end_pos > self.rows:
           end_pos = self.rows
           beg_pos = self.rows - self.l_width

        linepos = [beg_pos, end_pos]
        self.s_pos = ypos
 
        # show plot
        self.set_selection(HORIZONTAL, linepos)

    def vertical_line(self, xpos):
        half_width = int(self.l_width/2.0)

        beg_pos = xpos-half_width
        end_pos = int(beg_pos+self.l_width)

        self.s_pos = xpos
                
        # correct position at 
        if beg_pos < 0:
           beg_pos = 0
           end_pos = self.l_width
        elif end_pos > self.cols:
           end_pos = self.cols
           beg_pos = self.cols - self.l_width

        # show plot
        linepos = [beg_pos, end_pos]
        self.set_selection(VERTICAL, linepos)

    def arbitrary_line(self, line_coords):
        xbeg, ybeg, xend, yend = line_coords

        p0 = (xbeg,ybeg)
        p1 = (xend,yend)

        self.set_selection(LINE, (p0,p1))

    def square_box(self, square_coords):
        xbeg, ybeg, xend, yend = square_coords
        p0 = (xbeg,ybeg)
        p1 = (xend+1,yend+1)
        self.set_selection(SQUARE, (p0,p1))

    def set_selection(self, selection_type, coords):
        self.selection_type = selection_type
        self.selection_position = coords
        self.update_selection()

    def update_selection(self):
        self._update_selection()
        self.display_selection()

    def _update_selection(self):

        color = self.colors['selection']

        self.selection_info = OrderedDict()

        title = None
        xtitle = ""
        roi_shape = None
        roi_nbpix = None
        roi_sum = None
        roi_max = None
        roi_min = None
        roi_aver = None
        roi_std = None

        if self.selection_type is REGION:
            # select 
            beg_pos,end_pos = self.selection_position
            self.selected_data = self.fulldata[beg_pos:end_pos,:]
            line_data = self.selected_data.sum(axis=0)

            selrange = [beg_pos, end_pos, 0, self.cols-1]

            if end_pos - beg_pos == 1:
                title = "Y=%s" % beg_pos
            else:
                title = "Y. %s to %s" % (beg_pos, end_pos-1)

            self.line_plot.update_data(title, 'Y', \
                    self.s_pos, line_data)

        else:
            self.selection_info['selection'] = SELECTION_TYPE[self.selection_type]
            title = ""
            selrange = []

        if self.selection_type != NO_SELECTION:
            roi_shape = self.selected_data.shape
            if len(roi_shape) == 2:
                roi_nbpix = roi_shape[0]*roi_shape[1]
            else:
                roi_shape = roi_shape[0]
                roi_nbpix = roi_shape
            roi_sum = self.selected_data.sum()
            roi_max = self.selected_data.max()
            roi_min = self.selected_data.min()
            roi_aver = self.selected_data.mean()
            roi_std = self.selected_data.std()

        self.selection_info['selection'] = SELECTION_TYPE[self.selection_type]
        self.selection_info['coords'] = title
        self.selection_info['info'] = selrange

        if roi_shape:
            self.selection_info['shape'] = roi_shape 

        if roi_nbpix:
            self.selection_info['nb pixels'] = roi_nbpix 

        if roi_sum is not None:
            self.selection_info['sum'] = "%3.6g" % roi_sum

        if roi_max is not None:
            self.selection_info['max'] = "%3.6g" % roi_max 

        if roi_min is not None:
            self.selection_info['min'] = "%3.6g" % roi_min

        if roi_aver is not None:
            self.selection_info['average'] = "%3.6g" % roi_aver

        if roi_std is not None:
            self.selection_info['std dev'] = "%3.6g" % roi_std

        self.selectionUpdated.emit(self.selection_info, self.selected_data)

    def display_zoomrect(self, xbeg, ybeg, xend, yend):
        color = self.colors['zoom']
        color = self.colors['zoom']
        lstyle = 'dashed'
        width = xend - xbeg 
        height = yend - ybeg 

        if self.zoomrect:
             self.zoomrect.remove()
             self.zoomrect = None

        self.zoomrect = self.mca_axes.add_patch(patches.Rectangle( \
               (xbeg, ybeg), width, height, 
               linewidth=1, linestyle=lstyle, color=color, fill=False))

    def display_selection(self):
        self.reset_selection()
        self._display_selection()
        self.canvas.draw()

    def _display_selection(self):
        color = self.colors['selection']
        bgcolor = self.colors['selection_bg']

        if self.selecting:
            style = "dashed"
        else:
            style = "solid"

        if self.selection_type is REGION:
            beg_pos,end_pos = self.selection_position
            self.last_line = self.mca_axes.axhspan(beg_pos-0.5, end_pos-0.5, \
                edgecolor=color,facecolor=bgcolor, \
                alpha=0.5)

    def show_cursor_values(self, xval=None):
        if xval is not None: 
            if xval != self.xval: 
                self.xval = int(round(xval))
                xidx = (np.abs(self.xdata - xval)).argmin()
                self.xval = self.xdata[xidx]
                self.yval = self.ydata[xidx]
                pos_txt = "x=%d, y=%f " % (self.xval, self.yval)
                self.position_label.setText(pos_txt)

            if self.selecting is False:
                self.highlight_point(self.xval, self.yval)
        else:
            self.position_label.setText("")
            self.highlight_end()

    def set_line_plot(self, plot):
        self.line_plot = plot

    def move(self, direction):

        cur_xlim = list( self.mca_axes.get_xlim() )
        cur_ylim = list( self.mca_axes.get_ylim() )

        cur_xlim.sort()
        cur_ylim.sort()

        xleft, xright = cur_xlim
        ybot, ytop = cur_ylim

        x_extent = cur_xlim[1] - cur_xlim[0]
        y_extent = cur_ylim[1] - cur_ylim[0]

        delta_x = int( x_extent * self.move_by / 100.0 )
        delta_y = int( y_extent * self.move_by / 100.0 )

        if direction == MOVE_UP:
            ytop += delta_y
            ybot = ytop - y_extent
        elif direction == MOVE_DOWN:
            ybot -= delta_y
            ytop = ybot + y_extent
        elif direction == MOVE_RIGHT:
            xright += delta_x
            xleft = xright - x_extent
        elif direction == MOVE_LEFT:
            xleft -= delta_x
            xright = xleft + x_extent

        xlim = [xleft, xright]
        ylim = [ybot, ytop]

        self.set_limits(xlim,ylim)
        self.canvas.draw()
         
    def move_selection(self, direction):
        changed = False

        if direction == MOVE_UP and self.selection_type == HORIZONTAL:
            bpos, epos = self.selection_position
            if bpos != 0:
                bpos -= self.l_width
                epos -= self.l_width
                if bpos < 0:
                    bpos = 0
                    epos = self.l_width
                self.s_pos = (bpos + epos) / 2
                self.selection_position  = [bpos, epos]
                changed = True
        elif direction == MOVE_DOWN and self.selection_type == HORIZONTAL:
            bpos, epos = self.selection_position
            if epos != self.rows:
                bpos += self.l_width
                epos += self.l_width
                if epos >= self.rows:
                    bpos = self.rows-self.l_width
                    epos = self.rows
                self.s_pos = (bpos + epos) / 2
                self.selection_position  = [bpos, epos]
                changed = True
        elif direction == MOVE_RIGHT and self.selection_type == VERTICAL:
            bpos, epos = self.selection_position
            if epos != self.cols:
                bpos += self.l_width
                epos += self.l_width
                if epos > self.cols:
                    bpos = self.cols-self.l_width
                    epos = self.cols
                self.s_pos = (bpos + epos) / 2
                self.selection_position  = [bpos, epos]
                changed = True
        elif direction == MOVE_LEFT and self.selection_type == VERTICAL:
            bpos, epos = self.selection_position
            if bpos != 0:
                bpos -= self.l_width
                epos -= self.l_width
                if bpos < 0:
                    bpos = 0
                    epos = self.l_width
                self.s_pos = (bpos + epos) / 2
                self.selection_position  = [bpos, epos]
                changed = True

        if changed:
            self.update_selection()

    def reset_zoom(self):
        self.update_data()

    def scrolled_zoom(self,ev):
        if not ev.inaxes:
            return

        cur_xlim = list( self.mca_axes.get_xlim() )
        cur_ylim = list( self.mca_axes.get_ylim() )

        cur_xlim.sort()
        cur_ylim.sort()

        cur_xrange = (cur_xlim[1] - cur_xlim[0])*.5
        cur_yrange = (cur_ylim[1] - cur_ylim[0])*.5

        xpos = ev.xdata # get event x location
        ypos = ev.ydata # get event y location

        if ev.button == 'up':
            scale_factor = 1/self.scroll_zoom_scale
        elif ev.button == 'down':
            scale_factor = self.scroll_zoom_scale
        else:
            # deal with something that should never happen
            scale_factor = 1

        if scale_factor < 0.2:
            return
        
        xdelta = cur_xrange * scale_factor
        xlim = [xpos-xdelta, xpos+xdelta]

        ydelta = cur_yrange*scale_factor
        ylim = [ypos-ydelta, ypos+ydelta]

        self.set_limits(xlim, ylim)
        self.canvas.draw()

    def set_limits(self, xlim, ylim):
        lims = self.fix_lims(xlim, total_range=self.x_range, direction=self.x_dir)
        self.mca_axes.set_xlim(lims)

        lims = self.fix_lims(ylim, total_range=self.y_range, direction=self.y_dir)
        self.mca_axes.set_ylim(lims)

    def fix_lims(self, lims, total_range, direction):
        # limit to available range and fix direction of axes
        lims.sort()
        extent = lims[1] - lims[0]

        if lims[1] > total_range[1]:
            lims[1] = total_range[1]
            lims[0] = lims[1] - extent
        elif lims[0] < total_range[0]:
            lims[0] = total_range[0]
            lims[1] = lims[0] + extent

        if direction < 0:
            return lims[1], lims[0]
        else:
            return lims[0], lims[1]

    def draw(self):
        self.canvas.draw()

    def savefig(self, filename, title):
        self.prepare_print(title)
        self.fig.savefig(filename)
        self.restore_after_print()

    def printfig(self, printer, title, filename):
        self.prepare_print(title, bw=True)
        self.canvas.render(printer)
        self.restore_after_print()

    def prepare_print(self, title, bw=False):
        from textwrap import wrap

        self.print_bw = bw
        if bw:
            self.canvas_bgcolor = self.mca_axes.get_fc()
            self.fig_bgcolor = self.fig.patch.get_facecolor()

        try:
            slines = []
            for line in title.split("\n"):
                slines.extend(wrap(line,60))
        except BaseException as e:
            import traceback
            log.log(2,traceback.format_exc())

        title = "\n".join(slines)

        title_art = self.mca_axes.set_title(title, loc="left")
        self.draw()

    def restore_after_print(self):
        try:
            title_art = self.mca_axes.set_title(' ', loc="left")

            if self.print_bw:
                self.mca_axes.set_facecolor(self.canvas_bgcolor)
                self.fig.patch.set_facecolor(self.fig_bgcolor)

            self.draw()
        except:
            import traceback
            log.log(2, traceback.format_exc())

if __name__ == '__main__':
    import sys
    from pyspec.client import spec_shm

    log.start(2)

    app = QApplication([]) 
    win = McaWidget()
    win.show()

    #win.load_file(sys.argv[1])

    specname = sys.argv[1]
    varname = sys.argv[2]

    data = spec_shm.getdata(specname, varname)
    if len(data) == 1:
        ydata = data[0]
        xdata = range(len(ydata))
    elif len(data) == 2:
        ydata = data[1]
        xdata = data[0]
    else:
        print("Wrong data selected for 1D")

    print(ydata)
    win.setData(xdata,ydata)
    app.exec_()
    
