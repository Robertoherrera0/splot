#******************************************************************************                                                 '
#
#  @(#)OnzeWidget.py	3.10  07/21/21 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2020,2021
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


try:
    import fabio
except ImportError:
    print("Fabio not installed. Install fabio module for more file formats support")

import numpy as np
import time

try:
    from collections import OrderedDict
except ImportError:
    from pyspec.ordereddict import OrderedDict

from pyspec.graphics.QVariant import QApplication, QSize, QSizePolicy, \
        QWidget, QHBoxLayout, QVBoxLayout, QToolBar, QLabel, Qt, QLineEdit, \
        QComboBox, QIntValidator, pyqtSignal

from pyspec.graphics.QVariant import mpl_backend

from pyspec.css_logger import log, log_exception

from DialogTools import getPrinter, getSaveFile
from Preferences import Preferences
from Colormap import Colormap, ColormapDialog

import icons

from matplotlib.figure import Figure
from matplotlib import ticker
from matplotlib import patches

from RoiSelectionDialog import RoiSelectionDialog

# import matplotlib.colorbar as colorbar

FigureCanvas = mpl_backend.FigureCanvasQTAgg

MODE_ZOOM, MODE_VERT, MODE_HORIZ, MODE_LINE, MODE_SQUARE, MODE_POINT = \
        (0,1,2,3,4,5)

NO_SELECTION, HORIZONTAL, VERTICAL, LINE, SQUARE = (0,1,2,3,4)
SELECTION_TYPE = {
        NO_SELECTION:   "None",
        HORIZONTAL:   "Row",
        VERTICAL:   "Column",
        LINE:   "Line",
        SQUARE:   "Square",
        }

MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT = (0,1,2,3)

class OnzeWidget(QWidget):

    #refresh_time = 30 # millisecs

    selectionUpdated = pyqtSignal(object, object)

    def __init__(self,parent=None,*args):

        self.current_action = None
        self.parent = parent 
        #self.timer = None

        QWidget.__init__(self, *args)
        self.build_widget()

    def build_widget(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(18,18)) 

        self.zoom_action = self.toolbar.addAction(icons.get_icon('zoom'), "Z", self.set_zoom_mode)
        self.zoom_action.setToolTip("Zoom")
        self.zoom_action.setCheckable(True)

        self.toolbar.addSeparator()

        self.square_action = self.toolbar.addAction(icons.get_icon('square'), "S", self.set_square_selection)
        self.square_action.setToolTip("Square selection")
        self.square_action.setCheckable(True)

        self.horiz_action = self.toolbar.addAction(icons.get_icon('horiz'),"H", self.set_horizontal_selection)
        self.horiz_action.setToolTip("Horizontal selection")
        self.horiz_action.setCheckable(True)

        self.vert_action = self.toolbar.addAction(icons.get_icon('vert'),"V", self.set_vertical_selection)
        self.vert_action.setToolTip("Vertical selection")
        self.vert_action.setCheckable(True)

        self.line_action = self.toolbar.addAction(icons.get_icon('diag'),"D", self.set_line_selection)
        self.line_action.setToolTip("Line selection")
        self.line_action.setCheckable(True)

        self.w_label = QLabel("  W:")
        self.w_ledit = QLineEdit()
        self.w_ledit.setText("1") 
        self.w_ledit.setFixedWidth(60)
        self.w_validator = QIntValidator(1,100, self)
        self.w_ledit.setValidator(self.w_validator)
        self.w_ledit.textChanged.connect(self.set_selection_width)

        self.toolbar.addWidget(self.w_label)
        self.toolbar.addWidget(self.w_ledit)

        self.toolbar.addSeparator()
        self.print_action = self.toolbar.addAction(icons.get_icon('printer'),"P", self.printPlot)
        self.print_action.setToolTip("Print Image")
        self.print_action.setCheckable(False)

        self.t_spacer = QWidget()
        self.t_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(self.t_spacer)

        self.aspect_label = QLabel('Aspect:')
        self.aspect_cbox = QComboBox()
        self.aspect_options = ["equal", "auto"]
        self.aspect_cbox.addItems(self.aspect_options)
        self.aspect_cbox.currentIndexChanged.connect(self.aspect_changed)
        self.toolbar.addWidget(self.aspect_label)
        self.toolbar.addWidget(self.aspect_cbox)

        self.canvas = OnzeCanvas(self)

        self.line_plot = OnzePlot(self)

        cv_sizepol = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setSizePolicy(cv_sizepol)

        plt_sizepol = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.line_plot.setSizePolicy(plt_sizepol)

        self.canvas.set_line_plot(self.line_plot)
        self.canvas.selectionUpdated.connect(self.selection_updated)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=3)
        layout.addWidget(self.line_plot, stretch=1)

        self.line_plot.hide()

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

    def set_horizontal_selection(self):
        self.set_selection_mode(MODE_HORIZ)
        self.select_action(self.horiz_action)
        self.w_ledit.setEnabled(True) 

    def set_vertical_selection(self):
        self.set_selection_mode(MODE_VERT)
        self.select_action(self.vert_action)
        self.w_ledit.setEnabled(True) 

    def set_line_selection(self):
        self.set_selection_mode(MODE_LINE)
        self.select_action(self.line_action)
        self.w_ledit.setEnabled(False) 

    def set_square_selection(self):
        self.set_selection_mode(MODE_SQUARE)
        self.select_action(self.square_action)
        self.w_ledit.setEnabled(False) 

    def aspect_changed(self, index):
        self.set_aspect_ratio(self.aspect_options[index])

    def set_aspect_ratio(self, ratio):
        self.canvas.set_aspect_ratio(ratio)

    def load_file(self, filename):
        img = fabio.open(filename)
        data = img.data
        self.set_data(data)

    def getPlot(self):
        return self.canvas

    def setData(self, data, metadata):
        self.data = data
        self.metadata = metadata
        self.canvas.set_data(data, metadata)

    def setActive(self):
        self.active = True

        ##if self.timer:
            #self.timer.start(self.refresh_time)

    def setInactive(self):
        self.active = False
        #if self.timer:
            #self.timer.stop()

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

    def edit_colormap(self):
        try:
            self.canvas.edit_colormap()
        except:
            log_exception()

    def show_histogram(self):
        self.canvas.show_histogram()

class OnzePlot(QWidget):
    def __init__(self,parent,*args):
        QWidget.__init__(self, parent, *args)
        self.parent = parent
        self.p = None
        self.axis = None
        self.pos_line = None
        self.showing_cursor = False

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0) 
        self.setLayout(layout)
        figsize = (6,3)
        self.plots_fig = Figure(figsize=figsize,facecolor='#f0f0f0')
        self.plots = FigureCanvas(self.plots_fig)

        self.plots.setParent(self)
        self.plots.setFocusPolicy(Qt.StrongFocus)
        self.plots.setFocus()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.axes = self.plots_fig.add_subplot(111)
        try:
            self.axes.tick_params(axis='both', which='major', labelsize=8)
            self.axes.tick_params(axis='both', which='minor', labelsize=6)
        except Exception as e:
            log.log(2, "setting tick label size fails")

        self.plots.mpl_connect("motion_notify_event", self.mouse_moved)
        self.plots.mpl_connect("figure_leave_event", self.reset_line)

        layout.addWidget(self.plots)

    def mouse_moved(self, ev):

        try:
            if not ev.inaxes:
                self.reset_line()
                self.parent.highlight_end()
                self.plots.draw()
                self.showing_cursor = False
                return

            self.xpos = int(round(ev.xdata))
            self.reset_line()

            if self.xpos < 0: 
                self.xpos = 0
            elif self.xpos >= len(self.data):
                self.xpos = len(self.data)-1

            self.showing_cursor = True
            self.show_cursor()

        except Exception as e:
            import traceback
            log.log(2, traceback.format_exc())
            

    def show_cursor(self):

        self.pos_line = self.axes.axvline(self.xpos, color='green')
        self.plots.draw()

        if self.axis:
            value = self.data[self.xpos]
            if self.axis == 'X':
                x=self.position
                y=self.xpos
            elif self.axis == 'Y':
                x=self.xpos
                y=self.position
            elif self.axis == 'Line':
                x = self.position[0][self.xpos] 
                y = self.position[1][self.xpos]
                value = self.data[self.xpos]
            self.parent.highlight_point(x,y)
        
    def reset_line(self, ev=None):
        if self.pos_line:
            self.pos_line.remove()
            self.pos_line = None

    def update_data(self, title, axis, position, data):
        self.axis = axis

        if self.axis == 'Y':
            botlabel = 'Column'
        elif self.axis == 'X':
            botlabel = 'Row'
        elif self.axis == 'Line':
            self.showing_cursor = False
            self.parent.highlight_end()
            botlabel = ''

        self.position = position

        self.n_points = max(data.shape)
        self.data = data

        self.axes.clear()
        self.p, = self.axes.plot(self.data)

        self.axes.set_title(title, fontsize=8)
        self.axes.set_xlabel(botlabel, fontsize=8)

        try:
            self.axes.autoscale()
        except:
            pass

        #self.plots_fig.subplots_adjust(hspace=0.001)
        if self.showing_cursor:
            self.show_cursor()
        self.plots.draw()

class OnzeCanvas(QWidget):
     
    colors = {
            'zoom': 'cyan',
            'selection': 'green',
            'selection_bg': '#aaffaa',
            }

    scroll_zoom_scale = 1.1
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
        self.cb = None
        self.im = None
        self.last_line = None
        self.hl_mkr = None

        self.origin = "upper"  # lower, upper
        self.aspect = "equal"  # equal, auto

        self.l_width = 1

        self.scroll_zoom_scale = 1.2

        self.xidx = None
        self.yidx = None

        self.xval = None
        self.yval = None
        self.zval = None

        self.xdata = None
        self.ydata = None

        self.xunits = None
        self.yunits = None

        self.x_dir = 1
        self.y_dir = 1

        self.listeners = []
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
        self.selection_label = QLabel()

        layout.addWidget(self.canvas)
        layout.addWidget(self.position_label)

        self.canvas.mpl_connect("motion_notify_event", self.mouse_moved)
        self.canvas.mpl_connect("button_press_event", self.mouse_clicked)
        self.canvas.mpl_connect("button_release_event", self.mouse_released)
        self.canvas.mpl_connect("key_press_event", self.key_pressed)
        self.canvas.mpl_connect("figure_leave_event", self.leave_event)
        #self.canvas.mpl_connect("scroll_event", self.scrolled_zoom)

        self.im_axes = self.fig.add_subplot(111)

        self.colormap = Colormap()
        self.colormap.colormapChanged.connect(self.colormap_changed)

    def set_aspect_ratio(self, option):
        log.log(2, "setting aspect ratio to %s" % option)
        self.aspect = option
        self.refresh_image()
 
    def edit_colormap(self):
        self.editing_colormap = True
        diag = ColormapDialog(self.colormap, self, data=self.fulldata)
        diag.accepted.connect(self.diag_colormap_closed)
        diag.rejected.connect(self.diag_colormap_closed)
        ret = diag.show()

    def diag_colormap_closed(self):
        log.log(2, "dialog closed")
        self.editing_colormap = False

    def show_histogram(self):
        pass

    def highlight_point(self, x, y):

        if self.hl_mkr:
            self.hl_mkr.remove()
            self.hl_mkr = None

        self.hl_mkr = self.im_axes.scatter([x],[y], marker='o', color='green')
        self.canvas.draw()

    def highlight_end(self):
        if self.hl_mkr:
            self.hl_mkr.remove()
            self.hl_mkr = None
            self.canvas.draw()

    def set_data(self, data, metadata=None):
        if isinstance(data, list):
            data = np.array(data)

        self.fulldata = data
        self.metadata = metadata
        self.data = self.fulldata
        self.update_data()

    def update_data(self):
        self.rows, self.cols = self.data.shape
        self.colormap.datarange = (self.data.min(), self.data.max())

        #self.cb_axes = self.fig.colorbar(self.im, ax = self.im_axes)

        self.x_dir = 1
        self.y_dir = 1

        log.log(2,"image metadata is: %s" % str(self.metadata))

        if self.metadata and "x" in self.metadata:
            self.x_first = self.metadata["xfirst"]
            self.x_last = self.metadata["xlast"]
            self.xunits = self.metadata["xunit"]
            self.xlabel = self.metadata["x"]
        else:
            self.x_first = 0
            self.x_last = self.cols-1 
            self.xunits = None

        self.x_range = [self.x_first,self.x_last]
        self.xdata = np.linspace(self.x_first, self.x_last, self.cols)

        if self.x_range[1] < self.x_range[0]:
            self.x_dir = -1
            self.x_range.sort()

        if self.metadata and "y" in self.metadata:
            self.y_first = self.metadata["yfirst"]
            self.y_last = self.metadata["ylast"]
            self.yunits = self.metadata["yunit"]
            self.ylabel = self.metadata["y"]
        else:
            self.y_first = 0
            self.y_last = self.rows-1 
            self.yunits = None

        self.y_range = [self.y_first, self.y_last]
        self.ydata = np.linspace(self.y_first, self.y_last, self.rows)

        if self.y_range[1] < self.y_range[0]:
            self.y_range.sort()
            self.y_dir = -1

        self._update_selection()
        self.refresh_image()

    def display_image(self):
        
        self.im_axes.clear()
        self.im = self.im_axes.imshow(self.data, cmap=self.colormap.colormap, \
                norm=self.colormap.norm, interpolation='nearest',
                origin=self.origin,aspect=self.aspect,
                extent=self.x_range+self.y_range)

        xaxis = self.im_axes.get_xaxis()
        if self.xunits is None:
            xaxis.set_visible(False)
        else:
            xaxis.set_visible(True)
            xaxis.set_major_formatter(ticker.FormatStrFormatter("%3.3g "+self.xunits))
            for txt in xaxis.get_majorticklabels():
               txt.set_rotation(45)

        yaxis = self.im_axes.get_yaxis()
        if self.yunits is None:
            yaxis.set_visible(False)
        else:
            yaxis.set_visible(True)
            yaxis.set_major_formatter(ticker.FormatStrFormatter("%3.3g "+self.yunits))

        #self.im_axes.axis("off")

    def colormap_changed(self):
        if self.editing_colormap:
            self.refresh_image() 

    def refresh_image(self):
        t0 = time.time()

        self.display_image()
        self._display_selection()
        self.canvas.draw()
        #self.fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
        self.fig.tight_layout()

        log.log(2, "Refreshing image took %s" % (time.time()-t0))

    def get_selection_mode(self):
        return self.selection_mode 

    def set_selection_mode(self, mode):
        self.selection_mode = mode

        if self.selection_mode != MODE_ZOOM:
            self.reset_selection()

        if self.selection_mode in [MODE_SQUARE]:
            self.line_plot.hide()
        elif self.selection_mode in [MODE_HORIZ, MODE_VERT, MODE_LINE]:
            self.line_plot.show()

    def set_selection_width(self, width):
        self.l_width = int(width)

    def mouse_clicked(self,ev):
        if not ev.inaxes:
            return

        if ev.button == 3:  # right click
            self.right_clicked = True
        else:
            self.xbeg = int(round(ev.xdata))
            self.ybeg = int(round(ev.ydata))

        if self.selection_mode in [MODE_ZOOM, MODE_SQUARE, MODE_LINE]:
            self.selecting = True
        elif self.selection_mode == MODE_HORIZ:
            self.selecting = False
            self.apply_selection(MODE_HORIZ, self.ybeg)
        elif self.selection_mode == MODE_VERT:
            self.selecting = False
            self.apply_selection(MODE_VERT, self.xbeg)
             
    def reset_selection(self):

        if self.last_selrect:
            self.last_selrect.remove()
            self.last_selrect = None

        #if self.selection_mode != MODE_ZOOM:
        if self.last_line:
            self.last_line.remove()
            self.last_line = None

    def mouse_moved(self,ev):

        if not ev.inaxes:
            return

        xval = ev.xdata
        yval = ev.ydata

        #self.xidx = min(np.searchsorted(self.xdata, xval), len(self.xdata) - 1)
        #self.yidx = min(np.searchsorted(self.ydata, yval), len(self.ydata) - 1)
        self.xidx = int(round(xval))
        self.yidx = int(round(yval))

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

            if self.selection_mode == MODE_SQUARE:
                self.apply_selection(self.selection_mode, [xbeg, ybeg, xend, yend])
            elif self.selection_mode == MODE_LINE:
                self.apply_selection(self.selection_mode, [self.xbeg, self.ybeg, self.xend, self.yend])
            elif self.selection_mode == MODE_ZOOM:
                self.display_zoomrect(self.xbeg, self.ybeg, self.xend, self.yend)
                self.display_selection()  # show selection if available

        self.show_cursor_values(xval,yval)

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
            self.im_axes.set_xlim([xbeg-0.5, xend+0.5])

            #if self.origin == 'upper':
            self.im_axes.set_ylim([ybeg-0.5, yend+0.5])
            #else:
            #    self.im_axes.set_ylim([yend+0.5, ybeg-0.5])

            if self.zoomrect:
                self.zoomrect.remove()
                self.zoomrect = None
            self.update_selection()
            self.canvas.draw()
        elif self.selection_mode == MODE_SQUARE:
            self.apply_selection(self.selection_mode, [xbeg, ybeg, xend, yend])
        elif self.selection_mode == MODE_LINE:
            self.apply_selection(self.selection_mode, [self.xbeg, self.ybeg, self.xend, self.yend])

    def key_pressed(self,ev):
        print("key pressed on image. key is %s" % str(ev.key))

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
        end_pos = int(beg_pos+self.l_width)-1

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
        end_pos = int(beg_pos+self.l_width)-1

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

        if self.selection_type is HORIZONTAL:
            # select 
            beg_pos,end_pos = self.selection_position
            self.selected_data = self.fulldata[beg_pos:end_pos+1,:]
            line_data = self.selected_data.sum(axis=0)

            selrange = [beg_pos, end_pos, 0, self.cols-1]

            if end_pos == beg_pos:
                title = "Row=%s" % beg_pos
            else:
                title = "Rows: %s to %s" % (beg_pos, end_pos)

            self.line_plot.update_data(title, 'Y', \
                    self.s_pos, line_data)

        elif self.selection_type is VERTICAL:
            # select 
            beg_pos,end_pos = self.selection_position
            self.selected_data = self.fulldata[:,beg_pos:end_pos+1]
            line_data = self.selected_data.sum(axis=1)

            selrange = [0, self.rows-1, beg_pos, end_pos]

            if end_pos == beg_pos:
                title = "Column=%s" % beg_pos
            else:
                title = "Column. %s to %s" % (beg_pos, end_pos)

            self.line_plot.update_data(title, 'X', \
                    self.s_pos, line_data)

        elif self.selection_type is LINE:
            # select 
            coords = self.selection_position
            selrange = []

            x0, y0 = coords[0]
            x1, y1 = coords[1]
            num = max([abs(x1-x0),abs(y1-y0)]) # number of values to interpolate the line
            x, y = np.linspace(x0, x1, num), np.linspace(y0, y1, num)
            x = x.astype(np.int); y= y.astype(np.int)
            self.selected_data = self.fulldata[y,x]

            # display 
            title = "From row=%s,col=%s, To row=%s,col=%s" % (y0,x0,y1,x1)
            self.line_plot.update_data(title, "Line", position=(x,y), data=self.selected_data)

        elif self.selection_type is SQUARE:
            coords = self.selection_position
            x0, y0 = coords[0]
            x1, y1 = coords[1]
            self.selected_data = self.fulldata[y0:y1,x0:x1]

            selrange = [y0,y1-1,x0,x1-1] # rowbeg, rowend, colbeg,colend

            title = "From=%s,%s, To=%s,%s" % (y0,x0,y1-1,x1-1)
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
        lstyle = 'dashed'
        width = xend - xbeg 
        height = yend - ybeg 

        if self.zoomrect:
             self.zoomrect.remove()
             self.zoomrect = None

        self.zoomrect = self.im_axes.add_patch(patches.Rectangle( \
               (xbeg, ybeg), width, height, 
               linewidth=1, linestyle=lstyle, color=color, fill=False))

        #self.canvas.draw()

    def define_axes(self):
        # for now this is just a simulation  
        self.canvas.define_axes()
         
    def set_row_values(self, values=None, row_beg=None, row_end=None):
        nrows = self.data.shape[0]
        newvals = False

        if values is not None:
            if len(values) == nrows:
                self.rowvals = copy.copy(values)
                newvals = True
            else:
                log.log(2, "wrong number of row values provided")
        elif range_info is not None:
            if None in (row_beg, row_end):
                log.log(2, "wrong row value info provided")
            else:
                rowbeg, rowend = range_info 
                self.rowvals = np.linspace(row_beg, row_end, nrows)
                newvals = True

    def set_column_values(self, values=None, range_info=None):
        pass

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

        if self.selection_type is HORIZONTAL:
            beg_pos,end_pos = self.selection_position
            self.last_line = self.im_axes.axhspan(beg_pos-0.5, end_pos-0.5, \
                edgecolor=color,facecolor=bgcolor, \
                alpha=0.5)
        elif self.selection_type is VERTICAL:
            beg_pos,end_pos = self.selection_position
            self.last_line = self.im_axes.axvspan(beg_pos-0.5, end_pos-0.5, \
                edgecolor=color,facecolor=bgcolor, \
                alpha=0.5)
        elif self.selection_type is SQUARE:
            coords = self.selection_position
            x0, y0 = coords[0]
            x1, y1 = coords[1]

            width = x1 - x0 -1
            height = y1 - y0 -1

            self.last_selrect = self.im_axes.add_patch(patches.Rectangle(
               (x0, y0), width, height, linewidth=1, linestyle=style, 
               color=color, fill=False))

        elif self.selection_type is LINE:
            coords = self.selection_position
            x0, y0 = coords[0]
            x1, y1 = coords[1]
            x = (x0, x1)
            y = (y0, y1)
            self.last_line, = self.im_axes.plot(x,y,color=color, \
                 linewidth=1, linestyle=style, alpha=0.5)


    def define_axes(self):
        ticks = self.im_axes.get_xticks()
        print(ticks)

    def show_cursor_values(self, xval=None, yval=None):
        if xval is not None and yval is not None:
            if xval != self.xval or yval != self.yval:
                self.xval = int(round(xval))
                self.yval = int(round(yval))
                self.zval = self.fulldata[self.yval,self.xval]
                pos_txt = "xpos=%3.3g, ypos=%3.3g / value=%6.3f" % (self.xval, self.yval, self.zval)
                self.position_label.setText(pos_txt)
        else:
            self.position_label.setText("")

    def set_line_plot(self, plot):
        self.line_plot = plot

    def move(self, direction):

        cur_xlim = list( self.im_axes.get_xlim() )
        cur_ylim = list( self.im_axes.get_ylim() )

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
        if self.x_dir > 0:
            xr = self.x_range[0], self.x_range[1]
        else:
            xr = self.x_range[1], self.x_range[0]

        if self.y_dir > 0:
            yr = self.y_range[0], self.y_range[1]
        else:
            yr = self.y_range[1], self.y_range[0]

        self.im_axes.set_xlim(xr)
        self.im_axes.set_ylim(yr)

        self.canvas.draw()

    def scrolled_zoom(self,ev):
        if not ev.inaxes:
            return

        cur_xlim = list( self.im_axes.get_xlim() )
        cur_ylim = list( self.im_axes.get_ylim() )

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
        self.im_axes.set_xlim(lims)

        lims = self.fix_lims(ylim, total_range=self.y_range, direction=self.y_dir)
        self.im_axes.set_ylim(lims)

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
            self.canvas_bgcolor = self.im_axes.get_fc()
            self.fig_bgcolor = self.fig.patch.get_facecolor()

        try:
            slines = []
            for line in title.split("\n"):
                slines.extend(wrap(line,60))
        except BaseException as e:
            import traceback
            log.log(2,traceback.format_exc())

        title = "\n".join(slines)

        title_art = self.im_axes.set_title(title, loc="left")
        #title_art.set_y(1.05)
        #self.fig.subplots_adjust(top=0.8)
        self.draw()

    def restore_after_print(self):
        try:
            title_art = self.im_axes.set_title(' ', loc="left")
            #title_art.set_y(1.00)

            #self.fig.subplots_adjust(top=0)

            if self.print_bw:
                self.im_axes.set_facecolor(self.canvas_bgcolor)
                self.fig.patch.set_facecolor(self.fig_bgcolor)

            self.draw()
        except:
            import traceback
            log.log(2, traceback.format_exc())

if __name__ == '__main__':
    import sys
    from pyspec.client import spec_shm

    app = QApplication([]) 
    win = OnzeWidget()
    win.show()

    #win.load_file(sys.argv[1])

    specname = sys.argv[1]
    varname = sys.argv[2]

    data = spec_shm.getdata(specname, varname)
    win.setData(data)
    app.exec_()
    
