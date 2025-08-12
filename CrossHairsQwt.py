#******************************************************************************
#
#  @(#)CrossHairsQwt.py	3.3  04/28/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2020
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


from PyQt4 import Qwt5 as Qwt
from PyQt4 import Qt

from pyspec.css_logger import log
from Constants import *


class CrossHairs(Qwt.QwtPlotPicker):

    def __init__(self, plot):

        self.plot = plot

        Qwt.QwtPlotPicker.__init__(self,
                                   Qwt.QwtPlot.xBottom,
                                   Qwt.QwtPlot.yLeft,
                                   Qwt.Qwt.QwtPicker.PointSelection | Qwt.QwtPicker.DragSelection,
                                   Qwt.QwtPlotPicker.CrossRubberBand,
                                   Qwt.QwtPicker.AlwaysOn,
                                   self.plot.canvas())

        self.selected.connect(self.pointSelection)

    def setEnabled(self, flag):
        if flag:
            self.setRubberBandPen(Qt.QPen(Qt.QColor(CROSSHAIRS_COLOR)))
            self.setTrackerPen(Qt.QPen(Qt.QColor(CROSSHAIRS_COLOR)))
        Qwt.QwtPlotPicker.setEnabled(self, flag)

    def pointSelection(self, point):

        log.log(3,"Crosshairs clicked. point selected is %s" % (str(point)))
        self.plot.pointSelection(point)

        for mne in self.plot.curves:
            curve = self.plot.curves[mne]
            if curve.isVisible():
                closest = curve.closestPoint(point.toPoint())
                data = curve.data()
                xs = data.xData()
                ys = data.yData()
