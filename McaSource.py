#******************************************************************************
#
#  @(#)McaSource.py	3.4  09/28/22 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2019,2020,2021,2022
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
import DataStatistics

from McaWidget import McaWidget

try:
    import hdf5plugin
    import h5py
    h5py_imported = True
except ImportError:
    h5py_imported = False

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

from Preferences import Preferences

import numpy as np
from FunctionModels import GaussianModel, LorentzianModel, LinearModel

import DataBlock

cssname = "app.css"
cssfile = os.path.join(os.path.dirname(__file__), cssname)

from Preferences import Preferences

from DataSource1D import DataSource1D

# this is for now a spec 2D / it should be split in two classes 

class McaSource(DataSource1D):
    refresh_time = 30 # millisecs

    def __init__(self, app, specname=None, varname=None, filename=None, imgformat=None):

        self.specname = specname
        self.varname = varname

        self.spec_c = None
        self.xdata = None
        self.ydata = None

        self.selected_data = None
        self.refresh_cnt = 0

        sourcetype = SOURCE_1D | SOURCE_MCA

        DataSource1D.__init__(self, app, sourcetype, varname)

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
        self.plot_w = McaWidget(self)
        self.plot_w.set_description(self.specname,self.varname)

        self.plot = self.plot_w.getPlot()
        self.plot_w.selectionUpdated.connect(self.selection_updated)
        return self.plot_w

    def open_file(self,filename,fileformat):

        data = None
        try:
            if fileformat == 'CSV':
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
        except BaseException as e:
            import traceback
            popupError(self, "open mca data file", "problem opening file %s - %s" % (filename, str(e)),
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

    def setData(self, data, metadata=None):
        # data could be:
        #   list of two arrays ->  xdata, ydata
        #   list of numbers --> ydata (xdata is point no)
        #   list of lists --> series of 1D arrays / xdata is point no
        self.multiple = False
        xdata = None
        log.log(2, "showing mca data: %s" % str(data))

        if isinstance(data, list):
            log.log(2, "data is list")
            if len(data) == 1:
                log.log(2, "one dimension list")
                if isinstance(data[0], list):
                    ydata = data[0]
                else:
                    log.log(1, "wrong MCA data")
                    return
            elif len(data) == 2:
                xdata, ydata = data
            else:
                log.log(2, "multiple mcas. ")
                self.mcas = data
                ydata = self.mcas[0]
                self.multiple = True
        else:
            # handle numpy arrays
            sh = data.shape
            log.log(2, "data is numpy. shape is: %s" % str(sh))
            if len(sh) == 1:
                ydata = data
            elif sh[0] == 1:
                ydata = data[0]
            elif sh[1] == 1:
                ydata = data[0:-1,0].flatten()
            elif sh[1] == 2:
                xdata = data[0:-1,0].flatten()
                ydata = data[0:-1,1].flatten()
            else:
                xdata = data[0]
                ydata = data[1]

        if xdata is None:
            xdata = range(len(ydata))

        log.log(2, "MCA Source data ready. xlen: %d / ylen: %d" % (len(xdata), len(ydata)))
        self.xdata, self.ydata = xdata, ydata

        com = DataStatistics.calc_com(xdata, ydata)
        peak = DataStatistics.calc_peak(xdata, ydata)
        fwhm = DataStatistics.calc_fwhm(xdata, ydata)
        stats = {'com': com, 'peak': peak, 'fwhm': fwhm}

        self.metadata['com'] = com
        self.metadata['peak'] = peak
        self.metadata['fwhm'] = fwhm
 
        self.plot_w.setData(xdata,ydata,metadata) 

    def getData(self):
        return self.xdata, self.ydata

    def getPlot(self):
        return self.plot_w

    def selection_updated(self, selection_info, selection_data):
        self.selection_info = selection_info
        self.selection_data = selection_data
        log.log(2, "selection updated: %s " % selection_info)
        self.show_stats()
        if self.roi_dialog:
            self.roi_dialog.set_info(self.selection_info['info'])

    def show_stats(self):
        ydata = self.ydata
        xdata = self.ydata

        stats = OrderedDict()

        stats['total'] = OrderedDict()
        fstats = stats['total']
        fstats['nb channels'] = len(ydata)
        fstats['dtype'] = ydata.dtype
        fstats['sum'] = "%3.6g" % ydata.sum()
        fstats['max'] = "%3.6g" % ydata.max() 
        fstats['min'] = "%3.6g" % ydata.min()
        fstats['average'] = "%3.6g" % ydata.mean()
        fstats['std dev'] = "%3.6g" % ydata.std()

        stats['statistics'] = OrderedDict()
        sstats = stats['statistics']
        if self.metadata and 'peak' in self.metadata:
            peak = self.metadata['peak']
            fwhm = self.metadata['fwhm']
            com = self.metadata['com']

        sstats['peak'] = "@ %3.6g is %3.6g" % (peak[0], peak[1])
        sstats['fwhm'] = "@ %3.6g is %3.6g" % (fwhm[1], fwhm[0])
        sstats['COM'] = "@ %3.6g" % com

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
        self.set_data(data)

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

        ldata = spec_shm.getdata(self.spec, self.arrname)
        ldata, metadata = self.spec_c.get_data_variable(self.arrname)

        adata = np.array(ldata)
        datshape = adata.shape

        if 2 not in datshape and 1 not in datshape:
            popupError(self, "reading 1D data from spec", "problem reading data from %s:%s" % (self.spec, self.arrname),
                           moremsg="hint: is this really a 1D array?")
            return

        if len(datshape) == 2:
            if datshape[0] > datshape[1]:
                adata = adata.transpose()

        self.setData(adata, metadata)

    def _update(self):
        if not shm_available:
            # log.log(2,"NO SHM available")
            return

        if spec_shm.is_updated(self.spec, self.arrname, self):
            self.refresh_cnt += 1
            t0 = time.time()
            log.log(2,"new mca data from spec detected")
            self.read_spec_data()
            elapsed = time.time()-t0
            log.log(2,"   updated in: %3.3f secs" % elapsed)

    def follow(self):
        if self.varname is None:
            return

        self.load_spec(self.specname,self.varname)

    def update_menubar(self, menubar_set):
        menubar_set.dataMenu.menuAction().setEnabled(True)
        menubar_set.plotMenu.menuAction().setEnabled(True)
        menubar_set.mathMenu.menuAction().setEnabled(True)
        
    def define_roi(self):
        try:
            log.log(2, " defining roi")
            roi_cnts = self.spec_c.sendCommand("roi_counters()") 
            self.roi_dialog.show()
            self.roi_dialog.set_counters(roi_cnts.split(","))

            if not roi_cnts or roi_cnts == '0':
                log.log(2,"roi macros not loaded. try loading roi.mac")
                return

        except:
            import traceback
            log.log(2, traceback.format_exc())

    def set_roi(self, device, cntmne, cntname, operation, coords):
        log.log(2, "setting roi for %s on dev=%s" % (cntmne, device))

        if device == None:
            return

        coord_str = ','.join(coords)

        cmd = 'roiconf %s:%s:%s:%s:%s' % (device, cntmne, cntname, operation, coord_str)
        log.log(2,"sending command %s" % cmd)
        self.spec_c.sendCommand(cmd)

