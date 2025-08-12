#******************************************************************************
#
#  @(#)SwitchButton.py	3.3  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2016,2020,2023,2024
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

class SwitchButton(QWidget):

    toggled = pyqtSignal(bool) 

    def __init__(self,*args):
        super(SwitchButton,self).__init__(*args)
      
        self.setColors(QColor("#99ff99"),QColor("#dddddd"))
        self.border_color = "grey"
        self.checked = False
       
        self.setStyleSheet("background-color: #dddddd; border: 2px solid;" ) #% self.border_color)

        #defaults

        self.rect_margin = 2
        self.rect_border = 1

        self.border_radius = 5

        self.handler_margin = 1
        self.handler_border = 3
        self.handler_radius = 5 

        on_color_default = "lightgreen"
        off_color_default = "white"
  
        disable_color_default = "lightgrey"

        self.setColors(on_color_default, off_color_default, disable_color_default) 

        on_label_default = "On"
        off_label_default = "Off"

        self.setLabels(on_label_default, off_label_default)

    def setColors(self, on, off, disable=None):
        """ on and off parameters must be QColor type """
        self.on_color = QColor(on)
        self.off_color = QColor(off)
        if disable is not None:
            self.disable_color = QColor(disable)
       
        if self.on_color.red() + self.on_color.green() + self.on_color.blue() > 500:
            self.on_label_color = Qt.black
        else:
            self.on_label_color = Qt.white

        if self.off_color.red() + self.off_color.green() + self.off_color.blue() > 500:
            self.off_label_color = Qt.black
        else:
            self.off_label_color = Qt.white

    def setLabels(self, on, off):
        self.on_label = on
        self.off_label = off

        metrics = self.fontMetrics()
        self.setMinimumWidth( metrics.boundingRect(self.off_label).width() + \
                              metrics.boundingRect(self.on_label).width() + metrics.height()*2)
        #self.setMinimumHeight( metrics.height()*1.6)

    def setChecked(self,mode):
        if mode is not self.checked:
            self.checked = mode
            self.toggled.emit(self.checked)
            self.repaint()

    def isChecked(self):
        return self.checked

    def mouseReleaseEvent(self,ev):
        self.setChecked(not self.checked)

    def paintEvent(self, ev):
        #QPushButton.paintEvent(self,ev)

        QWidget.paintEvent(self,ev)
        p = QPainter(self)
        p.save()

        rect_width = int(ev.rect().width()/2)

        met = self.fontMetrics()
        rect = ev.rect()
        rectf = QRectF(ev.rect())

        try:
            p.setRenderHint(QPainter.Antialiasing)
        except AttributeError:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

        outline = rectf.adjusted(self.rect_margin, self.rect_margin, -self.rect_margin, -self.rect_margin)
        path = QPainterPath()
        path.addRoundedRect(outline, self.border_radius, self.border_radius);

        pen = QPen(QColor(self.border_color))
        pen.setWidth(self.rect_border)
        p.setPen(pen)

        p.drawPath(path)

        if self.isEnabled():
            onc = self.on_color
            offc = self.off_color
        else:
            onc = self.disable_color
            offc = self.disable_color

        if self.isChecked():
            h_rect = rect.adjusted(self.handler_margin, self.handler_margin, -rect_width, -self.handler_margin)
            h_rectf = QRectF(h_rect)

            text_pos = h_rect.center()-QPoint( int(met.boundingRect(self.on_label).width()/2), \
                                               int(1 - met.ascent()/2))

            path = QPainterPath()
            path.addRoundedRect(h_rectf, self.handler_radius, self.handler_radius);
            p.fillPath(path, QBrush(onc))

            pen = QPen(QColor(self.border_color))
            pen.setWidth(self.handler_border)

            p.drawPath(path)
            p.setPen(self.on_label_color)
            p.drawText(text_pos,self.on_label)
        else:
            h_rect = rect.adjusted(rect_width, self.handler_margin, -self.handler_margin, -self.handler_margin)
            h_rectf = QRectF(h_rect)

            text_pos = h_rect.center()-QPoint( int(met.boundingRect(self.off_label).width()/2), \
                                               int(1 - met.ascent()/2))

            path = QPainterPath()
            path.addRoundedRect(h_rectf, self.handler_radius, self.handler_radius);
            p.fillPath(path, QBrush(offc))

            pen = QPen(QColor(self.border_color))
            pen.setWidth(self.handler_border)

            p.drawPath(path)
            p.setPen(self.off_label_color)
            p.drawText(text_pos,self.off_label)

        p.restore()

if __name__ == '__main__':
    app = QApplication([])
    win = QMainWindow()
    bla = QWidget()
    lay = QHBoxLayout()
    bla.setLayout(lay)
    lab = QLabel("Server:")
    but = SwitchButton()
    but.setEnabled(False)
    lay.addWidget(lab)
    lay.addWidget(but)
    win.setCentralWidget(bla)
    win.show()

    try:
        exec_ = getattr(app, "exec_")
    except AttributeError:
        exec_ = getattr(app, "exec")
    exec_()
