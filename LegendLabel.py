#******************************************************************************
#
#  @(#)LegendLabel.py	3.3  04/28/20 CSS
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

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log

class LegendLabel(QLabel):

    def __init__(self, direction, parent):

        QLabel.__init__(self)

        self.parent = parent

        self.cntlist = []
        self.label = None
        self.bottomText = ""

        self.direction = direction

        self.setFixedWidth(20)

        font = self.font()
        font.setBold(True)
        self.setFont(font)

    def setCounters(self, cntlist, label):
        log.log(3,"setting counters for legend %s / label %s" % (cntlist, label))
        self.label = label
        self.cntlist = cntlist
        self.repaint()

    def setBottomText(self, btext):
        self.bottomText = btext

    def getLabel(self):
        return self.label or " ".join(self.cntlist)

    def paintEvent(self, event):

        painter = QPainter(self)

        rect = self.rect()
        self.h = rect.height()

        self.pixelSize = 0
        self.identSize = 10
        self.inspace = 5
        self.outspace = 10

        fontMetrics = QFontMetrics(self.font())

        totalLength = 0

        totalLength = 20

        if self.label:
            totalLength = fontMetrics.width(self.label)
   
        for item in self.parent.hiddenlegend.legendItems():
            txt = item.text().text()
            txtLength = fontMetrics.width(txt)

            if txt in self.cntlist:
                totalLength += self.identSize + self.inspace + txtLength + self.outspace

        start = (self.h - totalLength) / 2.0

        if self.bottomText:
            pnt = QPoint(-start,10)
            painter.drawText(pnt, self.bottomText)
            self.setFixedWidth(fontMetrics.width(self.bottomText) + 12)

        if self.direction > 0:
            painter.rotate(-90)
        else:
            painter.rotate(90)

        if self.label:
            pnt = QPoint(-(start+(totalLength/2.)+self.outspace), 10)
            painter.drawText(pnt,self.label)
        else: 
            for item in self.parent.hiddenlegend.legendItems():
                txt = item.text().text()
                if txt in self.cntlist:
                    start += self.drawItem(item, start, painter)
    
        painter.end()

    def drawItem(self, item, start, p):

        txt = item.text().text()
        fontMetrics = QFontMetrics(self.font())
        txtLength = fontMetrics.width(txt)

        if self.direction > 0:  # going up
            pnt = QPoint(-(start + txtLength + self.outspace), 10)
            p.drawText(pnt, txt)
            rect = QRect(-(start + txtLength + self.identSize +
                           self.inspace + self.outspace), 0, self.identSize, 10)
            item.drawIdentifier(p, rect)
        else:
            rect = QRect(start, -20, self.identSize, 10)
            item.drawIdentifier(p,  rect)
            pnt = QPoint(start + self.identSize + self.inspace, -10)
            txt = item.text().text()
            p.drawText(pnt, txt)

        itemLength = self.identSize + 2 * self.inspace + txtLength + self.outspace
        return itemLength
