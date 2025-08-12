#******************************************************************************
#
#  @(#)Colors.py	3.4  04/28/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2020
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

import sys
import uuid

from pyspec.graphics.QVariant import *

from Preferences import Preferences
from pyspec.css_logger import log

from Constants import *

import themes

# Some predefined colors

class ColorTable(object):

    class _ColorTable(QObject):
        """ Single instance (Singleton) maintaining a table through the application 
         assigning a color to one name.  
         The application should perform persistance for this table """
    
        _default_colors = ["#0000ff", "#ff00ff", "#ff0000",
                      "#007400", "#ff8000", "#909090", "#b01060"]

        colorChanged = pyqtSignal(str, str)
    
        def __init__(self):
            QObject.__init__(self)

            self._colors = {}

            self.prefs = Preferences()
         
            self.theme = themes.get_theme(self.prefs["theme"])

            try:
                self.default_colors = self.theme.default_plot_colors
            except:
                self.default_colors = self._defaults_colors

            if "colortable" in self.prefs.keys():
                try:
                    self._colors = eval(self.prefs["colortable"])
                except:
                    import traceback
                    log.log(3,traceback.format_exc())
    
        def loadTable(self, table):
            self._colors.update(table)
    
        def getDefaultColor(self):
            return self.default_colors[0]

        def getColor(self, name, use_default=True):
   
            if name not in self._colors:
                if not use_default:
                    return None

                self._colors[name] = self.default_colors[
                    len(self._colors) % len(self.default_colors)]
            return self._colors[name]
    
        def hasColor(self, name):
            if name in self._colors:  return True
            return False

        def setColor(self, name, color):
            self._colors[name] = str(color)
            self.prefs["colortable"] = str(self._colors)
            self.colorChanged.emit(name, color)
    
    def __new__(cls, *dt, **mp):
        if not ColorTable.instance:
            ColorTable.instance = ColorTable._ColorTable()
        return ColorTable.instance

    instance = None

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)



class ColorWidget(QRadioButton):

    colorChanged = pyqtSignal(str,)

    def __init__(self, color, parent, *args):
        QRadioButton.__init__(self, parent, *args)
        
        self.uuname = str(uuid.uuid4())[0:10]
        self.style_fmt = "#" + self.uuname + \
                 """::indicator {
border: 1px solid #000;
background-color: %s; 
width: 12px; height: 5px;}"""

        self.setObjectName( self.uuname )
        self.setColor(color)
        self.parent = parent
        self.clicked.connect(self.openDialog)

    def openDialog(self,flag=True):
        color = QColorDialog.getColor(QColor(self.color), self)
        if color.isValid():
            self.setColor(color.name())
            self.colorChanged.emit(color.name())

    def setColor(self, color):
        self.setStyleSheet( self.style_fmt % color )
        self.color = color

    def update(self):
        self.repaint()

    def getColor(self):
        return self.color.name()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = QMainWindow()

    table = ColorTable()
    print( table.default_colors )
    color = table.getColor("det")
    print( "Color for %s is %s" % ("det", color))
    wid = ColorWidget("green", win)
    win.setCentralWidget(wid)
    win.show()

    sys.exit(app.exec_())
