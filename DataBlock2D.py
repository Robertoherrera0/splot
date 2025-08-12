#
#  @(#)DataBlock2D.py	3.3  04/28/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2018,2020
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
from DataBlock import DataBlock

from pyspec.css_logger import log

class DataBlock2D(DataBlock):
    def __init__(self, data=None, columnnames=None, metadata=None):
        super(DataBlock2D,self).__init__()
        self.xdata = None
        self.ydata = None
        self.data = data

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

    def getData2D(self):
        return self.data, self.xdata, self.ydata
