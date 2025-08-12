#******************************************************************************
#
#  @(#)ScrollBar.py	3.6  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2018,2020,2022,2023,2024
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

import math

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log

class ScrollBar(QScrollBar):

    sliderMoved = pyqtSignal(object, float, float)

    def __init__(self, orientation, parent, minBase=None, maxBase=None):

        QScrollBar.__init__(self, orientation, parent)

        self.d_inverted = (orientation == Qt.Vertical)

        self.d_minBase = 0.0
        self.d_maxBase = 1.0

        self.isLog = False

        self.d_minLog = -10
        self.d_maxLog = -1

        self.d_baseTicks = 1000000

        self.moveSlider(self.d_minBase, self.d_maxBase)

        if minBase is not None and maxBase is not None:
            self.setBase(minBase, maxBase)
            self.moveSlider(minBase, maxBase)
        else:
            self.moveSlider(self.d_minBase, self.d_maxBase)

    def setInverted(self, inverted):

        if self.d_inverted != inverted:
            self.d_inverted = inverted
            self.moveSlider(self.minSliderValue(), self.maxSliderValue())

    def isInverted(self):
        return self.d_inverted

    def minBaseValue(self):
        return self.d_minBase

    def maxBaseValue(self):
        return self.d_maxBase

    def minSliderValue(self):
        return self.sliderRange(self.value())[0]

    def maxSliderValue(self):
        return self.sliderRange(self.value())[1]

    def extent(self):
        opt = QStyleOptionSlider()
        opt.init(self)
        opt.subControls = QStyle.SC_None
        opt.activeSubControls = QStyle.SC_None
        opt.orientation = self.orientation()
        opt.minimum = self.minimum()
        opt.maximum = self.maximum()
        opt.sliderPosition = self.sliderPosition()
        opt.sliderValue = self.value()
        opt.singleStep = self.singleStep()
        opt.pageStep = self.pageStep()
        opt.upsideDown = self.invertedAppearance()

        if (self.orientation() == Qt.Horizontal):
            opt.state |= QStyle.State_Horizontal

        return self.style().pixelMetric(QStyle.PM_ScrollBarExtent, opt, self)

    def setBase(self, min, max):

        if (min == self.d_minBase) and (max == self.d_maxBase):
            return

        self.d_minBase = min
        self.d_maxBase = max

        # check log values
        if self.d_minBase <= 0:
            self.d_minLog = -10
        else:
            self.d_minLog = math.log10(self.d_minBase)

        if self.d_maxBase <= 0:
            self.d_maxLog = 0
        else:
            self.d_maxLog = math.log10(self.d_maxBase)

        self.moveSlider(self.minSliderValue(), self.maxSliderValue())

    def setLog(self, flag):
        #self.isLog = flag
        pass

    def moveSlider(self, min, max):

        #sliderTicks = qRound(
        sliderTicks = round(
            (max - min) / (self.d_maxBase - self.d_minBase) * self.d_baseTicks)

        # setRange initiates a valueChanged of the scrollbars
        # in some situations. So we block
        # and unblock the signals.

        self.blockSignals(True)

        self.setRange(int(sliderTicks / 2), int(self.d_baseTicks - sliderTicks / 2))

        steps = int(sliderTicks / 200)

        if steps <= 0:
            steps = 1

        self.setSingleStep(int(steps))
        self.setPageStep(sliderTicks)

        tick = int(self.mapToTick(min + (max - min) / 2))

        if self.isInverted():
            tick = self.d_baseTicks - tick

        self.setSliderPosition(int(tick))
        self.blockSignals(False)

    def sliderChange(self, value):

        QScrollBar.sliderChange(self, value)
        min, max = self.sliderRange(self.value())

        self.sliderMoved.emit(self.orientation(), min, max)

    def sliderRange(self, value):

        if self.isInverted():
            value = self.d_baseTicks - value

        visibleTicks = self.pageStep()

        minticks = value - visibleTicks / 2.0
        maxticks = value + visibleTicks / 2.0

        min = self.mapFromTick(minticks)
        max = self.mapFromTick(maxticks)

        return min, max

    def sliderValue(self):
        return self.mapFromTickLog(self.value())

    def mapToTick(self, v):
        if self.isLog:
            return self.mapToTickLog(v)
        else:
            return (v - self.d_minBase) / (self.d_maxBase - self.d_minBase) * self.d_baseTicks

    def mapFromTick(self, tick):
        if self.isLog:
            return self.mapFromTickLog(tick)
        else:
            return self.d_minBase + (self.d_maxBase - self.d_minBase) * tick / self.d_baseTicks

    def mapToTickLog(self, v):
        if v <= 0:
            return 0

        logval = math.log10(v)

        if self.d_maxLog == self.d_minLog:
            return 0

        return (logval - self.d_minLog) / (self.d_maxLog - self.d_minLog) * self.d_baseTicks

    def mapFromTickLog(self, tick):
        # check for neg values

        logvalue = self.d_minLog + \
            (self.d_maxLog - self.d_minLog) * tick / self.d_baseTicks

        return pow(10, logvalue)
