
#
#  @(#)DataBlock.py	3.10  10/30/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2020
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

from Constants import *
from pyspec.css_logger import log 
from DataObservable import DataObservable
from SpecLeastSquaresFit import LeastSquaresFit
from Preferences import Preferences

from Features import haveFeature

import numpy as np
import DataStatistics
import copy

class DataBlock(DataObservable):

    def __init__(self, data=None, columnnames=None, metadata=None):

        super(DataBlock,self).__init__()

        # data
        self.data = np.empty((0))

        self.fulldata = self.data

        self.rangeX = []
        self.reduced_mode = False
        self.reduced = False

        self.extra_data = {}

        self.colnames = []
        self.aliases = {}
        self.canonics = {}

        # context data
        self.title = None
        self.scanobj = None
        self.source_description = None
        self.metadata = {}

        # selection
        self.mode_2d = False

        self.x_selection = []
        self._x_selection = []

        self.y_selection = None
        self._ySelection = None

        self.y1_selection = []
        self._y1_selection = []
        self.y2_selection = []
        self._y2_selection = []

        self.x_columns_default = []
        self.y1_columns_default = []
        self.y2_columns_default = []

        self.y1_columns_overriden = None

        self.using_xdefault = True
        self.using_x2default = True
        self.using_ydefault = True

        self.active_column = None
        self._current_stats = None

        self.update(data, columnnames, metadata)

    # Description
    def getDescription(self):
        return self.source_description

    def setSourceDescription(self, info):
        self.source_description = info

    # DATA
    def hasData(self):
        return self.data.any()

    def shape(self):
        if len(self.data.shape) > 1:
            nblines, nbcols = self.data.shape
        else:
            nblines = self.data.shape[0]
            nbcols = 1
        return nblines, nbcols

    def numberColumns(self):
        """ Returns the number of columns in  the datablock """
        return self.shape()[1]

    def numberLines(self):
        """ Returns the number of lines in  the datablock """
        return self.shape()[0]

    def getShape(self):
        return self.shape()

    def getData(self):
        return self.data

    def getData2D(self):
        return   

    def getDataColumn(self, column):
        if column and column in self.colnames:
            colno = self.getColumnNumber(column)
            return self.getDataColumnByNumber(colno)
        else:  # return point no.
            nblines, nbcols = self.shape()
            return np.array(range(nblines))

    def getXYDataForColumn(self, column):
        if column in self.colnames: 
            colno = self.getColumnNumber(column)
            ydata = self.getDataColumnByNumber(colno)
            xcolname, xdata = self.getXSelectionData()[0]
            return [xcolname, xdata, column, ydata]
        elif column in self.extra_data.keys():
            coldata, opts = self.extra_data[column] 
            xcolname = coldata['xcolumn']
            xdata = coldata['xdata']
            ydata = coldata['ydata']
            return [xcolname, xdata, column, ydata]
        else:  
            return [None,] *4

    def getXYDataSliceForColumn(self, column, slice_number=None):
        xcolname, xdata, column, ydata = self.getXYDataForColumn(column)

        if xdata is not None and xdata.any():
            if ydata is not None and ydata.any():
               if self.slices:
                   slice_number = self.slice_selected
                   if slice_number is None:
                       slice_number = -1
                   fidx, lidx = self.slices[slice_number]
                   xdata = xdata[fidx:lidx]
                   ydata = ydata[fidx:lidx]

        return [xcolname, xdata, column, ydata]
     
    def getMeshData(self, x1, x2, y):
        """ Returns a 2D array 3xnpoints """
        _x1data = self.getDataColumn(x1)
        _x2data = self.getDataColumn(x2)
        _ydata = self.getDataColumn(y)
        leny = len(_ydata)
  
        _x1uniq = list( np.sort( np.unique(_x1data) ) )
        lenx1 = len(_x1uniq)
        _x2uniq = list( np.sort( np.unique(_x2data) ) )
        lenx2 = len(_x2uniq)
        
        log.log(3,"x1 %s / x2 %s / y %s " % (lenx1, lenx2, leny))
        if lenx1 * lenx2 != leny:
            log.log(3,"Irregular mesh. Returning scattered %d points" % len(_x1data))
            return ["scatter", _x1data, _x2data, _ydata]
        else:
            log.log(3,"Mesh is %s x %s" % (len(_x1uniq), len(_x2uniq)))

            _2data = _ydata.reshape((lenx1, lenx2))
            return ["mesh", _x1uniq, _x2uniq, _2data]

    def getXSelectionData(self):

        ret = []

        if len(self.x_selection) == 0:
            nblines, nbcols = self.shape()
            xcolname = "Point no."
            xdata = np.array(range(nblines))
            ret.append([xcolname, xdata])
            if self.mode_2d:
                ret.append([xcolname, xdata])
        else:
            for xcolname in self.x_selection:
                xdata = self.getDataColumn(xcolname)
                ret.append([xcolname, xdata])

        return ret

    def getDataColumnByNumber(self, colno):
        if self.hasData():
            if len(self.data.shape) == 1:
                cdata = np.array([self.data[colno], ])
            else:
                cdata = self.data[0:, colno]
            return(cdata)
        else:
            return np.empty((0, len(self.colnames)))

    def setData(self, data=None, columnnames=None):
        self._update(data,columnnames)

    def update(self, data=None, columnnames=None, metadata=None):
        self._update(data, columnnames, metadata)

    def _update(self, data=None, columnnames=None, metadata=None):

        columns_changed=self._setColumnNames(columnnames)

        olddata = copy.copy(self.data)

        self._setData(data)

        self._update_slice_info()
             
        if not np.array_equal(olddata,self.data):
             data_changed = True
        else:
             data_changed = False

        columns_matched = self._matchColumnsAndData()

        if columns_changed or (not columns_matched):
            self.emit(COLUMNS_CHANGED, [self.colnames,list(self.extra_data.keys())])

        if metadata:
            self._setMetaData(metadata)

        selection_changed = self._applySelection()

        if data_changed:
            self.emit(DATA_CHANGED)
            if not selection_changed: # otherwise stats already updated
                self._updateStats()

    def _setData(self, data=None, columnnames=None):

        # Creating np array from data
        self.resetRange()

        if type(data) == np.ndarray:
            if data.any() == False:
                self.resetData()
            else:
                self.data = data
        elif data:
            self.data = np.array(data)
        else:
            self.data = np.empty((0, len(self.colnames)))

        if len(self.data.shape) == 1:
            self.data = np.reshape(self.data, (self.data.shape[0], 1))

        self.fulldata = self.data
        self.fullrange = self.getRange()

    def _set_no_slice(self):
        self.slices = [[0,self.data.shape[1]]]
        self.slice_selected = None
        self.emit_slices()

    def select_slice(self, slice_idx):
        self.slice_selected = slice_idx
        self.slice_modified = True
        self.emit(DATA_CHANGED)
        self._updateStats()

    def _update_slice_info(self):

        if not self.scanobj or not self.scanobj.isMesh():
            self._set_no_slice()
            return

        slow_pos = self.scanobj.getSlowMotorPositions() 
        posdist = abs((slow_pos[1] - slow_pos[0]) / (len(slow_pos) + 0.0))
        mindist = posdist * 0.5 # half of the expected distance

        lastpos = None
        lastidx = 0

        slow_data = self.getDataColumnByNumber(1)

        if len(slow_data) < 2:
            self._set_no_slice()
            return

        d_idx = self.last_slice_idx
        lastpos = self.last_slice_pos
        slice_start_idx = self.slice_start

        slices = self.slices[:-1] # the last one might be incomplete

        for pos in slow_data[d_idx:]:
            if lastpos is None:
                lastpos = pos
            elif lastpos != pos:
                # is this a new position? ok. if further to 
                if abs(pos-lastpos) > mindist:
                    slices.append([slice_start_idx, d_idx-1])
                    lastpos = pos
                    slice_start_idx = d_idx
                 
            d_idx += 1

        self.last_slice_idx = d_idx
        self.last_slice_pos = lastpos
        self.slice_start = slice_start_idx

        slices.append([slice_start_idx, d_idx-1])

        if slices != self.slices:
            # assign slice_selected to last if not manually selected
            #if self.slice_selected >= len(self.slices)-1 or self.slice_selected is None:
            if not self.slice_modified:
                self.slice_selected = len(slices)-1
            self.slices = slices
            self.emit_slices()  

    def emit_slices(self):
        self.emit(SLICES_CHANGED, len(self.slices), self.slice_selected) 

    def getSliceInfo(self):
        return self.slices

    def resetData(self):
        self.data = np.empty((0, len(self.colnames)))
        self.fulldata = self.data
        self.fullrange = self.getRange()
        self.purgeExtraData()

    def setScanObject(self, scanobj):
        if scanobj != self.scanobj:
            self.scanobj = scanobj
            self.newScan()

    def newScan(self):
        # 
        self.purgeExtraData()
        if self.scanobj and self.scanobj.isMesh() and haveFeature("2D"):
            self.setMode2D(True)
        else:
            self.setMode2D(False)

        # initialize data for slice identification (in case of mesh)
        self.slices = []
        self.slice_start = 0
        self.last_slice_pos = None
        self.last_slice_idx = 0
        self.slice_modified = False

        self.emit(NEW_SCAN, self.scanobj)

    def purgeExtraData(self):
        ex_colnames = self.extra_data.keys()

        for colname in ex_colnames:
            curve, options = self.extra_data[colname]
            if options['keep'] == False:
               self.extra_data.pop(colname)

    def addPoint(self, pointno, point):
        self._addPoint(point)
        self.emit(DATA_CHANGED)
        self._updateStats()

    def _addPoint(self, point):
        try:
            self.data = np.vstack((self.data, point))  # adding to existing
        except:
            self.data = np.array(point)    # first point

        self._update_slice_info()

    def addPoints(self, points, point_indexes=None):

        if point_indexes is not None:
            # when buffered data arrives before data is first read. normally
            #  only when splot is started with server mode 
            do_replace = False
            for idx in point_indexes: 
                if idx < len(self.data):
                    do_replace = True

            if do_replace:
                toadd_points = []
                for ptno in range(len(points)):
                    idx = point_indexes[ptno]
                    point = points[ptno]
                    if idx < len(self.data):
                        self.data[idx] = point 
                    else:
                        toadd_points.append(point)

                if toadd_points:
                    points = toadd_points

        if points:
            try:
                self.data = np.vstack((self.data, points))  # adding to existing
            except:
                self.data = np.array(points)    # first point

        self._update_slice_info()

        self.emit(DATA_CHANGED)
        self._updateStats()

    # END Data

    # Columns
    def getColumnNames(self):
        """ Returns the labels describing the columns of the datablock """
        return [self.colnames, self.extra_data.keys()]

    def getColumnNumber(self, name):
        if name in self.colnames:
            return self.colnames.index(name)
        else:
            return -1

    def getColumnName(self, number):

        if type(number) is int and number >= 0 and number < len(self.colnames):
            return self.colnames[number]
        elif number < 0 and abs(number) <= len(self.colnames):
            number = len(self.colnames) - abs(number)
            return self.colnames[number]
        else:
            return None

    def setColumnNames(self, columnnames):
        updated = self._setColumnNames(columnnames)

        if updated:
            self.emit(COLUMNS_CHANGED, [columnnames, list(self.extra_data.keys())])
            self._applySelection()  # re-apply selection with new colnames

    def _setColumnNames(self, columnnames):
        """ Sets the labels describing the columns of the datablock. colnames must be a list of string labels """
        columns_updated = False

        if columnnames and type(columnnames) is list:
            colnames = [str(column) for column in columnnames]
            if colnames != self.colnames:
                columns_updated = True
                self.colnames = colnames

            self.colnames = colnames

        return columns_updated

    def setDefaultModeDefault(self):
        self.y1_columns_overriden = None

    def setDefaultSelection(self, xsel, y1sel, y2sel, x2sel=None):
        changed = self._setDefaultSelection(xsel,y1sel,y2sel, x2sel)
        #if changed:
        #    self._applySelection()

    def _setDefaultSelection(self, xsel, y1sel, y2sel, x2sel=None):

        changed = False

        if xsel != self.x_columns_default:
            self.x_columns_default = xsel 
            changed = True

        if y1sel != self.y1_columns_default:
            self.y1_columns_default = y1sel 
            changed = True

        if y2sel != self.y2_columns_default:
            self.y2_columns_default = y2sel 
            changed = True

        return changed
          
    def _verifyDefaultSelection(self):

        if len(self.colnames) > 0:
            cfound = []
            if len(self.colnames) > 1:
                for colname in self.x_columns_default:
                    if colname in self.colnames:
                        cfound.append(colname)

            if cfound:
                if self.mode_2d:
                    if len(cfound) < 2:
                        firstcol = cfound[0]
                        self.x_columns_default = [firstcol,]
                        for col in self.colnames:
                            if col != firstcol:
                               self.x_columns_default.append(col)
                               break
                            #if len(self.x_columns_default) == 2:
                               #break
                    else:
                        self.x_columns_default = cfound[0:2] 
                else:
                    self.x_columns_default = cfound[0:1]
            else:
                if self.mode_2d and len(self.colnames) > 1:
                    self.x_columns_default = self.colnames[0:2]
                else:
                    if len(self.colnames) > 1:
                        self.x_columns_default = self.colnames[0:1]
                    else:
                        self.x_columns_default = []

            cfound = []

            for colname in self.y1_columns_default:
                if colname in self.colnames:
                    cfound.append(colname)

            if cfound:
                self.y1_columns_default = cfound
            else:
                self.y1_columns_default = [self.colnames[-1]]

            cfound = []

            for colname in self.y2_columns_default:
                if colname in self.colnames:
                    cfound.append(colname)

            if cfound:
                self.y2_columns_default = cfound
            else:
                self.y2_columns_default = []

        else:
            self.x_columns_default = []
            self.y1_columns_default = []
            self.y2_columns_default = []

    def _verifySelection(self):

        # X
        if self.using_xdefault:
            self._x_selection = self.x_columns_default
        else:
            if not self._x_selection:
                pass
            else:
                # first check if selected still in colnames
                cfound = []
                somefound = False

                for colname in self._x_selection:
                    if colname in self.colnames:
                        cfound.append(colname)

                self._x_selection = cfound

                if cfound:
                    somefound = True

                if not somefound:
                    if self.mode_2d and len(self.x_columns_default) > 1:
                        self._x_selection = self.x_columns_default[0:2]
                    elif len(self.x_columns_default):
                        self._x_selection = self.x_columns_default[0:1]
                    self.using_xdefault = True

        # Y
        if self.using_ydefault:
            if self.y1_columns_overriden:
                self._y1_selection = self.y1_columns_overriden
            else:
                self._y1_selection = self.y1_columns_default
            self._y2_selection = self.y2_columns_default
        else:   # when selection was manually made 
            if not self._y1_selection and not self._y2_selection:
                # if nothing selected... fine
                pass
            else:
                cfound = []
                somefound = False

                for colname in self._y1_selection:
                    if colname in self.colnames:
                        cfound.append(colname)

                self._y1_selection = cfound

                if cfound:
                    somefound = True

                cfound = []
                for colname in self._y2_selection:
                    if colname in self.colnames:
                        cfound.append(colname)

                self._y2_selection = cfound
                if cfound:
                    somefound = True

                if not somefound:
                    if self.y1_columns_overriden:
                        self._y1_selection = self.y1_columns_overriden
                    else:
                        self._y1_selection = self.y1_columns_default
                    self._y2_selection = self.y2_columns_default
                    self.using_ydefault = True


    def _verifyExtraSelection(self):
        for colname in self.extra_data:
            curve,options = self.extra_data[colname] 
            if curve['axis'] == 'y1':
                if colname not in self._y1_selection:
                    self._y1_selection.append(colname)
            elif curve['axis'] == 'y2':
                if colname not in self._y2_selection:
                    self._y2_selection.append(colname)
            else:
                continue

    # END Columns

    def _matchColumnsAndData(self):

        use_default_names = False

        if self.hasData():
            nblines, nbcols = self.shape()
            if not self.colnames:
                use_default_names = True
            elif len(self.colnames) != nbcols:
                use_default_names = True
        elif self.colnames:  # no data
            pass

        if use_default_names:
            self.colnames = []

            nblines, nbcols = self.shape()

            for col in range(nbcols):
                colname = "Column %d" % (col + 1)
                self.colnames.append(colname)
          
            return False
        else:
            return True

    # Metadata
    def setMetaData(self, metadata):
        self._setMetaData(metadata)
        self._updateStats()

    def _setMetaData(self, metadata):
        if metadata:
            self.metadata.update(metadata)

        # Default metadata
        title =  self.metadata.get("title", "")
        if title != self.title:
            self.setTitle(title)

        if "datastatus" not in self.metadata:
            self.metadata["datastatus"] = DATA_STATIC

        if "xColumn" in self.metadata and "yColumns" in self.metadata:
            self.setDefaultSelection([self.metadata['xColumn'],], self.metadata['yColumns'],[])
        elif "yColumns" in metadata:
            self.setDefaultSelection([], self.metadata['yColumns'],[])

        if "motornames" in self.metadata and "motormnes" in self.metadata: 
            names = self.metadata["motornames"]
            mnes = self.metadata["motormnes"]
            self.addAliases(mnes, names)

        if "counternames" in self.metadata and "countermnes" in self.metadata: 
            names = self.metadata["counternames"]
            mnes = self.metadata["countermnes"]
            self.addAliases(mnes, names)

    def addAliases(self, canonics, aliases):
        if None in [canonics, aliases]:
            log.log(3,"cannot make motor aliases") 
            return

        if len(canonics) == len(aliases):
            for _no in range(len(canonics)):
                can = canonics[_no]
                alias= aliases[_no]
                self.addAlias(can, alias)
        else:
            log.log(3,"cannot make aliases correspond %s / %s " % (len(canonics), len(aliases)))

    def addAlias(self, mne, name):
        self.aliases[name] = mne
        self.canonics[mne] = name 

    def getAliases(self):
        return self.aliases

    def getAlias(self, canonic):
        return self.canonics.get(canonic,canonic)

    def getCanonic(self, alias):
        return self.aliases.get(alias,alias)

    def getMetaData(self, metakey):
        return self.metadata.get(metakey, None)

    def getTitle(self):
        return self.title

    def setTitle(self, title):
        self.title = title
        self.emit(TITLE_CHANGED,title)

    def getMotorAlias(self, motorky):

        motnames = None
        motmnes = None

        if 'motornames' in self.metadata:
            motnames = self.metadata['motornames']
        if 'motmnes' in self.metadata:
            motmnes = self.metadata['motormnes']

        if motmnes is None or motnames is None:
            return motorky

        if len(motmnes) != len(motnames):
            return motorky

        if motorky in motnames:
            return motmnes[motnames.index(motorky)]

        if motorky in motmnes:
            return motnames[motmnes.index(motorky)]

        return motorky

    # END Metadata

 
    # Selection

    def getXSelection(self):
        return self.x_selection

    def getYSelection(self):
        return self.y_selection

    def getY1Selection(self):
        return self.y1_selection

    def getY2Selection(self):
        return self.y2_selection

    def getMode2D(self):
        return self.mode_2d 

    def setMode2D(self,mode=True):
        """ Setting mesh mode allows to select 2 columns for X and 1 for Y """
        if mode != self.mode_2d:
            self.mode_2d = mode
            self.resetDefaultColumns()
            self.emit(PLOT2D_CHANGED, mode)

    def setSelection(self, xcols, y1cols, y2cols, x2col=None):
        self.using_xdefault = False
        self.using_ydefault = False
        self._setSelection(xcols, y1cols, y2cols)
        self._applySelection()
        self._updateStats()

    def setXSelection(self, colname, override_default=False):
        if override_default:
            self.using_xdefault = True
            self.x_columns_default = colname
        else:
            self.using_xdefault = False

        self._setXSelection(colname)
        self._applySelection()
        self._updateStats()

    def setY1Selection(self, colnames, override_default=False):
        if override_default:
            self.using_ydefault = True
            #self.y1_columns_default = colnames
            self.y1_columns_overriden = colnames
        else:
            self.using_ydefault = False
        self._setY1Selection(colnames)
        self._applySelection()
        self._updateStats()

    def setY2Selection(self, colnames, override_default=False):
        if override_default:
            self.using_ydefault = True
            self.y2_columns_default = colnames
        else:
            self.using_ydefault = False
        self._setY2Selection(colnames)
        self._applySelection()
        self._updateStats()

    def resetDefaultColumns(self):
        self.using_xdefault = True
        self.using_ydefault = True

        self._x_selection = self.x_columns_default
        self._y1_selection = self.y1_columns_default
        self._y2_selection = self.y2_columns_default

        self._applySelection()
        self._updateStats()

    # END getter/setter functions callable from outside

    def _setSelection(self, xcols, y1cols, y2cols):
        self._setXSelection(xcols)
        self._setY1Selection(y1cols)
        self._setY2Selection(y2cols)

    def _setXSelection(self, colnames):
        if colnames != self.x_selection:
            self.resetRange()

        self._x_selection = []
        for colname in colnames:
            if colname not in self.colnames:
                try:  # accept a column number
                    colnum = int(colname) 
                    colname = self.colnames[colnum]
                except:
                    pass

            if colname in self.colnames:
                self._x_selection.append(colname) 

    def _setY1Selection(self, colnames):
        self._y1_selection = []
        for colname in colnames:
            if colname not in self.colnames:
                try:  # accept a column number
                    colnum = int(colname) 
                    colname = self.colnames[colnum]
                except:
                    pass

            if colname in self.colnames:
                self._y1_selection.append(colname)

    def _setY2Selection(self, colnames):
        self._y2_selection = []
        for colname in colnames:
            if colname not in self.colnames:
                try:  # accept a column number
                    colnum = int(colname) 
                    colname = self.colnames[colnum]
                except:
                    pass

            if colname in self.colnames:
                self._y2_selection.append(colname)

    def _applySelection(self):

        self._verifyDefaultSelection()
        self._verifySelection()
        self._verifyExtraSelection()

        selection_changed = False
     
        if self._x_selection != self.x_selection:
            self.x_selection = self._x_selection
            self.x_selection = copy.copy(self._x_selection)
            self.emit(X_SELECTION_CHANGED, self.x_selection)
            selection_changed = True

        if self._y1_selection != self.y1_selection:
            self.y1_selection = copy.copy(self._y1_selection)
            self.emit(Y1_SELECTION_CHANGED, self.y1_selection)
            selection_changed = True

        if self._y2_selection != self.y2_selection:
            self.y2_selection = copy.copy(self._y2_selection)
            self.emit(Y2_SELECTION_CHANGED, self.y2_selection)
            selection_changed = True

        _ySelection = self._y1_selection + self._y2_selection 

        if _ySelection != self.y_selection:
            self.y_selection = copy.copy(_ySelection)
            self.emit(Y_SELECTION_CHANGED, self.y_selection)

        if selection_changed:
            self.emit(SELECTION_CHANGED, self.x_selection, self.y1_selection, self.y2_selection)
            self._updateStats()

        return selection_changed

    # END Selection

    # EXTRA data
    def getExtraData(self, colname):
        if colname in self.extra_data:
            return self.extra_data[colname]

    def addExtraData(self, curve, options):
        colname = ""

        if curve['source'] != self.getDescription():
            sep = ":"
            colname = curve['source']
        else:
            sep = ""

        colname += sep + curve['colname']

        if 'extra' in curve.keys():
            colname += '-' + curve['extra']

        _no = 0
        _colname = colname
        while _colname in self.colnames:
           _no += 1
           _colname = "%s_%d" % (_colname,_no)
        while _colname in self.extra_data.keys():
           _no += 1
           _colname = "%s_%d" % (_colname,_no)
        colname = _colname

        curve['description'] = colname
        if 'axis' not in curve.keys():
            curve['axis'] = "y1"

        self.extra_data[colname]  = [curve, options]
        self.emit(COLUMNS_CHANGED, [self.colnames, list(self.extra_data.keys())])
        self._applySelection() 

    def setLockExtraData(self,colname,lockstate):
        if colname in self.extra_data.keys():
            curve,opts = self.extra_data[colname]
            opts['keep'] = lockstate
            self.emit(DATACONFIG_CHANGED, colname)
        elif colname in self.colnames:
            log.log(3,"locking normal curve")

    def getDataConfig(self, colname):
        config = {}
        if colname in self.extra_data.keys():
            curve,opts = self.extra_data[colname]
            if 'usedots' in curve:
                config['usedots'] = curve['usedots']  
            if 'color' in curve:
                config['color'] = curve['color']  
        return config

    def setExtraDataAxis(self,colname, axis):
        if colname in self.extra_data.keys():
            curve,opts = self.extra_data[colname]
            curve['axis'] = axis
            self._applySelection() 

    def deleteExtraData(self, colname):
        if colname in self.extra_data.keys():
            self.extra_data.pop(colname)
            changed = True  
        else:
            changed = False

        if changed:
            self.emit(COLUMNS_CHANGED, [self.colnames, list(self.extra_data.keys())])
            self._applySelection() 

    # END extra data

    # REDUCE data
    def setInterval(self, interval):

        # save full data
        if not self.reduced and not self.rangeX:
            self.fullrange = self.getRange()
            self.fulldata = self.data

        self.reduced = True

        if interval.find(":") != -1:
            parts = interval.split(":")
            beg, fin = parts[0:2]
            beg = self._convertDataIndex(beg)
            fin = self._convertDataIndex(fin, last=True)
            self.data = self.fulldata[beg:fin][:]
        elif interval.find(",") != -1:
            pts = interval.split(",")
            pts = map(int, pts)
            for ptidx in range(len(pts)):
                if pts[ptidx] < 0:
                    pts[ptidx] = len(self.data) + pts[ptidx]
            pts.sort()
            self.data = self.fulldata[pts][:]
        else:
            try:
                numpts = int(interval)
            except:
                pass
            else:
                self.data = self.fulldata[:numpts][:]

        if len(self.data) < len(self.fulldata):
            self.reduced_mode = True
        else:
            self.reduced_mode = False
        self._updateStats()

    def _convertDataIndex(self, idx, last=False):
        if idx == '':
            return None

        idx = int(idx)

        # Uncomment following code to include the last index in the selection
        if last == False:
            return idx
        elif idx == -1:
            return None
        return idx + 1

        return idx

    def setNumberPoints(self, numpts, firstpt=0):

        if not self.data.any():
            return

        maxpt = self.data.shape[0]
        if firstpt < 0 or firstpt >= maxpt:
            return
        if numpts < 0 or numpts >= maxpt:
            return
        if numpts + firstpt >= maxpt:
            return

        self.reduced = True
        self.data = self.fulldata[firstpt:firstpt + numpts][:]
        self._updateStats()

    def setRange(self, xbeg, xend):

        if not self.data.any():
            return

        if xbeg > xend:
            xend, xbeg = xbeg, xend

        if not self.reduced and not self.rangeX:
            self.fullrange = self.getRange()
            self.fulldata = self.data

        self.rangeX = xbeg, xend

        xcol = self.getColumnNumber(self.x_selection[0])
        self.data = self.fulldata[self.fulldata[:, xcol] >= xbeg]
        self.data = self.data[self.data[:, xcol] <= xend]
        if len(self.fulldata) > len(self.data):
            self.reduced_mode = True
        else:
            self.reduced_mode = False
        self._updateStats()

    def resetRange(self):
        if not self.rangeX and not self.reduced:
            return
        self.rangeX = []
        self.reduced = False
        self.data = self.fulldata
        self.reduced_mode = False
        self._updateStats()

    def isReduced(self):
        return self.reduced_mode

    def getFullRange(self):
        return self.fullrange

    def getRange(self):
        if self.x_selection:
            xcol = self.getDataColumn(self.x_selection[0])
        else:
            return (0, 0)

        if xcol.any() == False:
            return (0, 0)
        xmin = xcol.min()
        xmax = xcol.max()
        return xmin, xmax

    def getRegionRange(self):
        return self.rangeX

    # Statistics
    def setStatsActive(self,flag):
        self.stats_active = flag

    def calculateStats(self, colname=None):

        stats = {}

        if not self.hasData():
            return stats

        if colname == None:
            colname = self.active_column

        if self.mode_2d:
            xdata = self.getXSelectionData()
            if len(xdata) != 2:
                log.log(1,"selection does not correspond to selection mode")
                return
            xcol, xdat = xdata[0]
            ycol, ydat = xdata[1]
            zdat = self.getDataColumn(colname)

            peakidx = zdat.argmax()
            log.log(3,"Peakidx: %s" % peakidx)
            xpos = xdat[peakidx]
            ypos = ydat[peakidx]

            stats = {'2d': True, 
                     'xcolumn': xcol, 'ycolumn': ycol, 'column': colname,
                     'sum': zdat.sum(), 
                     'peak': zdat.max(), 
                     'peak_x': xpos, 
                     'peak_y': ypos }
            log.log(3," 2d stats:  %s" % stats )
        else:
            if self.scanobj and self.scanobj.isMesh():
                xcol, xdata, ycol, ydata = self.getXYDataSliceForColumn(colname)
            else:
                xcol, xdata, ycol, ydata = self.getXYDataForColumn(colname)
    
            if ydata.shape[0]:
                com = DataStatistics.calc_com(xdata, ydata)
                peak = DataStatistics.calc_peak(xdata, ydata)
                fwhm = DataStatistics.calc_fwhm(xdata, ydata)
                stats = {'2d': False, 'xcolumn': xcol, 'column': colname, 'com': com, 'peak': peak, 'fwhm': fwhm}

        return stats

    def setActiveColumn(self, ys):
        if ys != self.active_column:
            self.active_column = ys
            self.emit(ACTIVECOLUMN_CHANGED, self.active_column)
            self._updateStats()

    def getStats(self, ys=None):
        if not ys:
            ys = self.active_column

        return self.calculateStats(ys)

    def _updateStats(self):
        
        if self.active_column:
            stats = self.calculateStats()
        else:
            stats = {}

        if stats != self._current_stats:
            self._current_stats = stats
            self.emit(STATS_UPDATED, self._current_stats) 

    def doFit(self, model=None):

        if self.scanobj and self.scanobj.isMesh():
            xcolumn, xdata, ycolumn, ydata = self.getXYDataSliceForColumn(self.active_column)
        else:
            xcolumn, xdata, ycolumn, ydata = self.getXYDataForColumn(self.active_column)

        stats = self.calculateStats(self.active_column)

        self.prefs = Preferences()
        sampling = self.prefs.get("sampling", 100)

        if model is None:
            model = GaussianModel()
            log.log(3,"Fitting to: %s" %  model.get_description())

        estim_pars = model.estimate_parameters(xdata, ydata, stats)

        errd = np.sqrt(abs(ydata)); errd.shape = (len(ydata),)
        
        fpars, chisqr, sigma = LeastSquaresFit(model,estim_pars,xdata=xdata,ydata=ydata,sigmadata=errd, linear=False)

        # Set the number of points to resample the fitted function
        nb_samples = self.prefs['sampling']

        if nb_samples is None:
            nb_samples = 200

        fit_xdata = np.arange(xdata.min(), xdata.max(), (xdata.max()-xdata.min())/nb_samples)
        fit_ydata = model(fpars,fit_xdata)

        fitresult = model.result_message(fpars)

        curve = {
           # 'isfit' : True,
           # 'fitmodel': model.get_mnemonic(),
           'xdata' : fit_xdata,
           'ydata' : fit_ydata,
           'xcolumn' : xcolumn,
           'colname' : ycolumn + "_fit",
           'usedots' : False,
           'dotsize' : 0,
           'source' : self.getDescription(),
           'color' : 'red',
           'curve_info' : "Fit Result:" + fitresult,
        }

        opts = {
            'keep': False
        }

        if len(fpars) > 3:
           curve['peakpos'] = fpars[3]

        self.addExtraData(curve, opts)
        self.setActiveColumn(curve['description'])

    # OTHER
    def __repr__(self):
        nblines, nbcols = self.shape()
        rp = """%s (%d columns, %d lines)""" % (
            self.__class__, nbcols, nblines)
        rp += "\n Columns are: %s " % str(self.getColumnNames())
        return rp

    def __str__(self):
        return str(self.data)

class DataBlock2D(DataBlock):
    def __init__(self, data=None, columnnames=None, metadata=None):

        super(DataBlock2D,self).__init__()
        self.xdata = None
        self.ydata = None

    def setData(self, zdata=None, xdata=None, ydata=None, columnnames=None, metadata=None):
        self._update(zdata, xdata, ydata, columnnames, metadata)

    def _update(self, zdata=None, xdata=None, ydata=None, columnnames=None, metadata=None):

        if type(zdata) == np.ndarray:
            if zdata.any() == False:
                self.resetData()
            else:
                self.data = zdata
        elif zdata:
            self.data = np.array(zdata)
        else:
            self.data = np.empty((0))

        shape = self.data.shape

        if len(shape) == 2:
            rows, cols = shape
        else:
            log.log(3,"Wrong data for 2D")
            return

        if xdata is None:
            self.xdata = np.arange(cols)
        elif len(xdata) != cols:
            log.log(3,"inconsistent data x,y lengths do not match with data")
            self.xdata = np.arange(cols)

        if ydata is None:
           self.ydata = np.arange(rows)
        elif len(ydata) != rows:
           log.log(3,"inconsistent data x,y lengths do not match with data")
           self.ydata = np.arange(rows)


class DataBlock1D(DataBlock):
    pass

# Test data
def testData(setno):
    print("Creating test data number ", setno)

    if setno == 1:
        # Testing with normal list data
        ldata = [[1, 1], [2, 4], [3, 9]]
        dtest = DataBlock(ldata)

    elif setno == 2:
        # Testing giving list data and colnames as list
        ldata = [[1, 5, 33], [2, 12, 44], [3, 7., 55], [4, 3, 37], [5, 1, 22]]
        colnames = ["First", "Second", "Third"]
        meta = {'datastatus': DATA_LIVE}

        dtest = DataBlock(ldata, colnames, meta)

    elif setno == 3:
        # Testing full syntax and numpy data
        fdata = np.array([[2.3, 1.1], [4.5, 1.2], [8.9, 1.3], [10.3, 1.4]])
        colnames = ["Dirua", "Interes"]
        dtest = DataBlock(fdata, colnames)

    elif setno == 4:
        pdata = np.array([[1, 1, 2], [2, 4, 4], [3, 9, 6], [
                         4, 16, 8], [5, 25, 10], [6, 36, 12]])
        colnames = ["num", "num*num", "num2"]
        meta = {}
        meta['scanNumber'] = "2"
        meta['title'] = "Square function"
        meta['xColumn'] = "num"
        meta['yColumns'] = ["num2", ]
        dtest = DataBlock(pdata, colnames, meta)
    elif setno == 5:
        gdata = np.array([[1, 2, 4, 3], [3, 5, 4, 2], [4, 6, 1, 7], [
                         5, 3, 3, 1], [0, 4, 3, 2], [6, 19, 18, 13]])
        colnames = ["x", "sec", "mon", "det"]
        dtest = DataBlock(gdata, colnames)
        dtest.setXSelection("x")
        dtest.setRange(1, 4)
        dtest.setXSelection("mon")
        dtest.setY1Selection(["mon", ])
        dtest.setY2Selection(["det", ])
    elif setno == 6:
        udata = np.array([1, 2, 4, 3, 5, 4, 2, 14, 16, 17])
        dtest = DataBlock(udata)
    return (dtest)

if __name__ == '__main__':
    # print repr( testData(1) )
    testData(5)
    # print repr( testData(3) )
    # print repr( testData(4) )
    # print testData(5).calculateStats()
