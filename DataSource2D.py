#******************************************************************************
#
#  @(#)DataSource2D.py	3.11  07/21/21 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2019,2020,2021
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

import os
import sys
import copy
import weakref

try:
    from collections import OrderedDict
except ImportError:
    from pyspec.ordereddict import OrderedDict

from pyspec.graphics.QVariant import *
from Constants import *
from pyspec.css_logger import log
from pyspec.utils import is_windows, is_unity, is_macos

from ErrorDialog import popupError
from RoiSelectionDialog import RoiSelectionDialog

import icons
import time

try:
    import hdf5plugin
    import h5py
    h5py_imported = True
except ImportError:
    h5py_imported = False

try:
    import fabio
    fabio_imported = True
except ImportError:
    fabio_imported = False

try:
   from xraise import xraise_id
except ImportError:
   log.log(1,"Cannot import xraise. Using dummy")
   def xraise_id(*args):
       pass

import themes

try:
    from pyspec.client import spec_shm
    shm_available = True
except:
    shm_available = False

from OnzeWidget import OnzeWidget

from Preferences import Preferences

import numpy as np
from FunctionModels import GaussianModel, LorentzianModel, LinearModel

import DataBlock

cssname = "app.css"
cssfile = os.path.join(os.path.dirname(__file__), cssname)

from Preferences import Preferences

from DataSource import DataSource

# this is for now a spec 2D / it should be split in two classes 

class DataSource2D(DataSource):
    refresh_time = 30 # millisecs

    def __init__(self, app, specname=None, varname=None, filename=None, imgformat=None):

        self.specname = specname
        self.varname = varname

        self.spec_c = None
        self.data = None
        self.metadata = None

        self.selected_data = None
        self.refresh_cnt = 0

        sourcetype = SOURCE_2D
        DataSource.__init__(self, app, sourcetype, varname)

        if self.specname is not None:
            self.spec_value.setText(self.specname)

        if self.varname is not None:
            vartxt = "%s (array)" % self.varname
        elif filename is not None:
            vartxt = "%s (file)" % filename

        self.display_value.setText(vartxt)

        if filename is not None:
            self.open_file(filename, imgformat)

    def init_source_area(self):
        self.top_widget = QWidget()

        self.spec_label = QLabel("spec:")
        self.display_label = QLabel("Displaying:")
        self.spec_value = QLabel()
        self.display_value = QLabel()

        self.spacer = QLabel("")
        self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.spec_value.setObjectName("specname")

        self.info_widget = QTextEdit()
        self.info_widget.setReadOnly(True)

        self.top_layout = QGridLayout()
        self.top_layout.setSpacing(3)
        self.top_layout.setContentsMargins(0, 0, 0, 0)

        self.top_layout.addWidget(self.spec_label,0,0)
        self.top_layout.addWidget(self.spec_value,0,1)
        self.top_layout.addWidget(self.spacer,0,2)
        self.top_layout.addWidget(self.display_label,1,0)
        self.top_layout.addWidget(self.display_value,1,1)

        self.top_widget.setLayout(self.top_layout)
        self.set_source_header_widget(self.top_widget)
        self.add_source_tab(1, self.info_widget,  "Info")

        self.roi_dialog = RoiSelectionDialog(self)

    def init_graphics_area(self):
        self.plot_w = OnzeWidget(self)
        self.plot_w.set_description(self.specname,self.varname)

        self.plot = self.plot_w.getPlot()
        self.plot_w.selectionUpdated.connect(self.selection_updated)
        return self.plot_w

    def open_file(self,filename,imgformat):

        data = None
        try:
            if imgformat == 'TIFF':
                from pyspec.file.tiff import TiffFile
                data = TiffFile(filename).asarray()
                self.setData(data)
            elif imgformat == 'ITEX':
                from pyspec.file.hamamatsu import ItexImage
                log.log(2, "opening file %s" % filename)
                data = ItexImage(filename).data
            elif imgformat == 'HDF5':
                if not h5py_imported:
                    popupError(self, "open 2d data file", "cannot import h5py/ or hdf5plugin.",
                            moremsg="hint: opening HDF5 files needs module h5py. Try  installing them:" 
                                    "    pip (or pip3) install hdf5plugin"
                                    "    pip (or pip3) install h5py")
                else:
                    try:
                        f = h5py.File(filename)
                        log.log(2,"hdf5 1")
                        d = f['/entry/data/data_000001'][()]
                        log.log(2, "hdf5 2 %s" % str(d.shape))
                        data = d[0]
                        log.log(2, "hdf5 3")
                    except:
                        import traceback
                        log.log(3,traceback.format_exc())
            elif fabio_imported:
                img = fabio.open(filename)
                data = img.data
        except BaseException as e:
            import traceback
            popupError(self, "open 2d data file", "problem opening file %s - %s" % (filename, str(e)),
                           moremsg="hint: check that the selected format (%s)" % imgformat)
            log.log(3,traceback.format_exc())
            return

        if data is not None and data.any():
            self.filename = filename
            self.setData(data)

    def set_connection(self, conn):
        self.spec_c = conn
        try:
            self.specname = self.spec_c.getName()
            self.spec_value.setText(self.specname)
        except:
            pass

    def setData(self,data, metadata=None):
        self.data = data
        self.metadata = metadata
        self.plot_w.setData(data, metadata) 

    def getData(self):
        return self.data

    def getPlot(self):
        return self.plot_w

    def selection_updated(self, selection_info, selection_data):
        self.selection_info = selection_info
        self.selection_data = selection_data
        log.log(2, "selection updated: %s " % selection_info)
        self.show_stats()

        if self.roi_dialog:
            self.roi_dialog.set_range(self.selection_info['info'])

    def set_selection_mode(self):
        # for 2D default selection mode is "square
        try:
            self.plot_w.set_square_selection()
        except BaseException as e:
            log.log(2, "failed to set selection mode: %s" % str(e))

    def show_stats(self):
        data = self.data
        height, width = data.shape
        stats = OrderedDict()

        stats['full image'] = OrderedDict()
        fstats = stats['full image']
        fstats['rows'] = height
        fstats['columns'] = width
        fstats['nb pixels'] = width*height
        fstats['dtype'] = data.dtype

        stats['statistics'] = OrderedDict()
        sstats = stats['statistics']
        sstats['sum'] = "%3.6g" % data.sum()
        sstats['max'] = "%3.6g" % data.max() 
        sstats['min'] = "%3.6g" % data.min()
        sstats['average'] = "%3.6g" % data.mean()
        sstats['std dev'] = "%3.6g" % data.std()

        if self.selection_info is not None:
            if self.selection_info['coords']:
                stats['selected data'] = OrderedDict()
                selstats = stats['selected data']
                for ky in self.selection_info:
                    selstats[ky] = self.selection_info[ky]

        self.display_stats(stats)

    def display_stats(self,stats):
       
        stat_head = ''
        block_line ='<br><u><b>%s</b></u><br>'
        stat_line = '<b>%s:</b>   %s<br>'
        stat_tail = ''
        empty_line = ''

        stat_txt = stat_head

        for ky in stats:
            log.log(2, ky)
            block_stats = stats[ky]
            stat_txt += block_line % ky.upper()
            for bky,val in block_stats.items():
                if bky == 'info':
                   continue
                stat_txt += stat_line % (bky.capitalize(),val)

        stat_txt += stat_tail
        
        self.info_widget.setText(stat_txt)

    def load_file(self, filename):
        img = fabio.open(filename)
        data = img.data
        self.setData(data)

    def load_spec(self, spec, arrname):
        self.spec = spec
        self.arrname = arrname
        self.read_spec_data()
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(self.refresh_time)

    def read_spec_data(self):
        log.log(2,"reading data from spec")

        if not shm_available:
            log.log(2,"NO SHM available")
            return

        ldata, metadata = self.spec_c.get_data_variable(self.arrname)
        #ldata = spec_shm.getdata(self.spec, self.arrname)
        #metadata = spec_shm.getmetadata(self.spec, self.arrname)
        #if metadata:
            #metadata = json.loads(metadata)

        log.log(2,"reading data done")
        data = np.array(ldata)
        log.log(2,"ready to send data")
        self.setData(data, metadata)

    def _update(self):
        if not shm_available:
            # log.log(2,"NO SHM available")
            return

        if spec_shm.is_updated(self.spec, self.arrname, self):
            self.refresh_cnt += 1
            t0 = time.time()
            log.log(2,"new image from spec detected")
            self.read_spec_data()
            elapsed = time.time()-t0
            log.log(2,"   updated in: %3.3f secs" % elapsed)

    def follow(self):
        if self.varname is None:
            return

        self.load_spec(self.specname,self.varname)

    def set_aspect_ratio(self, ratio):
        self.plot_w.set_aspect_ratio(ratio)

    def update_menubar(self, menubar_set):
        menubar_set.dataMenu.menuAction().setEnabled(True)
        menubar_set.plotMenu.menuAction().setEnabled(False)
        menubar_set.mathMenu.menuAction().setEnabled(False)
        
    def edit_colormap(self):
        log.log(2, " edit colormap")
        self.plot_w.edit_colormap()
    
    def define_roi(self):
        try:
            log.log(2, " defining roi")

            roi_cnts = self.spec_c.sendCommand("roi_counters()")
            roi_devs = self.spec_c.sendCommand("roi_devices()")
            #roi_devs = self.spec_c.sendCommand("ccd_list()")

            self.set_selection_mode()
            self.roi_dialog.set_devices(roi_devs)
            self.roi_dialog.set_counters(roi_cnts)
            self.roi_dialog.show()

            if not roi_cnts or roi_cnts == '0':
                log.log(2,"roi macros not loaded. try loading roi.mac or starting SPEC in server mode")
                return
        except:
            import traceback
            log.log(2, traceback.format_exc())

    def set_roi(self, device, cntmne, cntname, operation, coords):
        log.log(2, "setting roi for %s on dev=%s" %(cntmne, device))

        if device == None:
            return

        coord_str = ','.join(coords)

        cmd = "roi_parse_conf('%s:%s:%s:%s:%s')" % (device, cntmne, cntname, operation, coord_str)
        log.log(2,"sending command %s" % cmd)
        self.spec_c.sendCommand(cmd)

    def delete_roi(self, mne):
        cmd = "roidel %s" % mne
        self.spec_c.sendCommand(cmd)

    def define_axes(self):
        log.log(2, " defining axes")
        self.plot_w.define_axes()

    def export2d(self):
        log.log(2, "export 2D data")

