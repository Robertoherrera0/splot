#******************************************************************************
#
#  @(#)PlotOptions.py	3.5  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2020,2023,2024
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
from Preferences import Preferences
from pyspec.css_logger import log

from widgets.PlotOptionsUIDialog import Ui_plotOptionsDialog
from SwitchButton import SwitchButton
import copy

PlotDefaults = {
    'showbars':  False,
    'usedots':  True,
    'dotsize':  5,
    'mindotsize': 2,
    'maxdotsize': 15,
    'uselines':  True,
    'linethick':  1,
    'minlinethick': 1,
    'maxlinethick': 6,
    'showlegend': True,
    'legendpos': 'auto',
}

LegendPositions = ['auto', 'top_left', 'top_center', 'top_right', 'bottom_left', 'bottom_center', 'bottom_right']

class PlotOptionsDialog(QDialog, Ui_plotOptionsDialog):

    def __init__(self,parent):
        super(PlotOptionsDialog, self).__init__(parent)

        self.prefs = Preferences()
        self.orig_prefs = copy.copy(self.prefs)

        self.auto_updating = False

        self.setupUi(self)

        # hide checkboxes from UI design. Substitute them with switchbuttons
        self.useDotsCheck.hide() 
        self.useLinesCheck.hide() 
        self.showLegendCheck.hide() 
        self.showErrorBarsCheck.hide() 
        self.errorBarsLabel.hide() 

        self.useDotsSwitch = SwitchButton()
        self.useLinesSwitch = SwitchButton()
        self.showErrorBarsSwitch = SwitchButton()
        self.showLegendSwitch = SwitchButton()

        self.useDotsSwitch.setLabels("Use","No")
        self.useLinesSwitch.setLabels("Draw","No")
        self.showErrorBarsSwitch.setLabels("Show","No")
        self.showLegendSwitch.setLabels("Yes","No")

        self.dotSizeSpin.setRange(
            PlotDefaults['mindotsize'], PlotDefaults['maxdotsize'])

        self.lineThickSpin.setRange(
            PlotDefaults['minlinethick'], PlotDefaults['maxlinethick'])

        self.optionsLayout.addWidget(self.useDotsSwitch, 0, 1)
        self.optionsLayout.addWidget(self.useLinesSwitch, 1, 1)
        #self.optionsLayout.addWidget(self.showErrorBarsSwitch, 2, 1)
        self.optionsLayout.addWidget(self.showLegendSwitch, 3, 1)

        showbars = self.prefs.getValue('showbars')
        if showbars is not None:
            self.barsflag = eval(str(showbars))
        else:
            self.barsflag = PlotDefaults['showbars']
        self.initial_bars = self.barsflag

        usedots = self.prefs.getValue('usedots')
        if usedots is not None:
            self.dotsflag = eval(str(usedots))
        else:
            self.dotsflag = PlotDefaults['usedots']
        self.initial_dots = self.dotsflag

        dotsize = self.prefs.getValue('dotsize')
        if dotsize is not None:
            self.dotsize = int(dotsize)
        else:
            self.dotsize = PlotDefaults['dotsize']
        self.initial_dotsize = self.dotsize

        uselines = self.prefs.getValue('uselines')
        if uselines is not None:
            self.lineflag = eval(str(uselines)) 
        else:
            self.lineflag = PlotDefaults['uselines']
        self.initial_lines = self.lineflag

        if self.prefs['linethick'] is not None:
            self.linethick = int(self.prefs['linethick'])
        else:
            self.linethick = PlotDefaults['linethick']
        self.initial_linethick = self.linethick

        showlegend = self.prefs.getValue('showlegend')
        if showlegend is not None: 
            self.showlegend = eval(str(showlegend))
        else:
            self.showlegend = PlotDefaults['showlegend']
        self.initial_showlegend = self.showlegend

        legendpos = self.prefs.getValue('legendpos')
        if legendpos is not None and legendpos in LegendPositions: 
            self.legendpos = str(legendpos)
        else:
            self.legendpos = PlotDefaults['legendpos']
        self.initial_legendpos = self.legendpos

        self.legendPositionCombo.addItems(LegendPositions)

        self._check_disable_entries()

        self.useDotsSwitch.toggled.connect(self.apply)
        self.useLinesSwitch.toggled.connect(self.apply)
        self.showErrorBarsSwitch.toggled.connect(self.apply)
        self.showLegendSwitch.toggled.connect(self.apply)

        self.dotSizeSpin.valueChanged.connect(self.apply)
        self.lineThickSpin.valueChanged.connect(self.apply)
        self.legendPositionCombo.currentIndexChanged.connect(self.apply)

        self.restoreButton.clicked.connect(self.restore_defaults)
    
    def _update(self):
        self._auto_updating = True

        self.useDotsSwitch.setChecked(self.dotsflag)
        log.log(3,"_updating dotsize is %s" % self.dotsize)
        self.dotSizeSpin.setValue(self.dotsize)

        self.useLinesSwitch.setChecked(self.lineflag)
        self.lineThickSpin.setValue(self.linethick)

        self.showErrorBarsSwitch.setChecked(self.barsflag)

        self.showLegendSwitch.setChecked(self.showlegend)
        try:
            posidx = LegendPositions.index(self.legendpos)
        except IndexError:
            posidx = 0
        self.legendPositionCombo.setCurrentIndex(posidx)

        self._auto_updating = False

    def show(self):
        self._update()
        self.setFixedSize(self.size())
        QDialog.show(self)

    def _check_disable_entries(self):
        if self.dotsflag:
            self.dotSizeSpin.setEnabled(True)
        else:
            self.dotSizeSpin.setEnabled(False)

        if self.lineflag:
            self.lineThickSpin.setEnabled(True)
        else:
            self.lineThickSpin.setEnabled(False)

        if self.showlegend:
            self.legendPositionCombo.setEnabled(True)
        else:
            self.legendPositionCombo.setEnabled(False)

    def get_selection(self):

        dotsflag = self.useDotsSwitch.isChecked()
        dotsize = int(str(self.dotSizeSpin.text()))

        lineflag = self.useLinesSwitch.isChecked()
        linethick = int(str(self.lineThickSpin.text()))

        barsflag = self.showErrorBarsSwitch.isChecked()

        showlegend = self.showLegendSwitch.isChecked()
        legendpos = str(self.legendPositionCombo.currentText())

        return ((dotsflag, dotsize), (lineflag, linethick), \
                           barsflag, (showlegend, legendpos))


    def restore_defaults(self):
        log.log(3,"Restoring defaults")
        self.dotsflag = PlotDefaults['usedots']
        self.dotsize = PlotDefaults['dotsize']
        log.log(3,"setting default dotsize is %s" % self.dotsize)
        self.barsflag = PlotDefaults['showbars']
        self.lineflag = PlotDefaults['uselines']
        self.linethick = PlotDefaults['linethick']

        self.showlegend = PlotDefaults['showlegend']
        self.legendpos = PlotDefaults['legendpos']

        log.log(3,"setting default legend to %s / %s" % (self.showlegend, self.legendpos))

        self._update()
        self._check_disable_entries()
        self._apply()

    def apply(self):

        if self._auto_updating:
            return

        dots, lines, bars, legend = self.get_selection()

        self.dotsflag, self.dotsize = dots
        self.lineflag, self.linethick = lines
        self.barsflag = bars
        self.showlegend, self.legendpos =  legend
        self._check_disable_entries()
        self._apply()

    def _apply(self):
        self.prefs.setValue('usedots', self.dotsflag)
        self.prefs.setValue('uselines', self.lineflag)
        self.prefs.setValue('dotsize', self.dotsize)
        self.prefs.setValue('linethick', self.linethick)
        self.prefs.setValue('showlegend', self.showlegend)
        self.prefs.setValue('legendpos', self.legendpos)
        self.prefs.setValue('showbars', self.lineflag)

        if self.parent():
            self.parent().setDots(self.dotsflag, self.dotsize)
            self.parent().setLines(self.lineflag, self.linethick)
            self.parent().showErrorBars(self.barsflag)
            self.parent().setLegend(self.showlegend, self.legendpos)
            self.parent().redrawCurves()

    def accept(self):
        self.prefs.save()
        self.hide()

    def reject(self):
        self.barsflag = self.initial_bars
        self.dotsflag = self.initial_dots
        self.lineflag = self.initial_lines
        self.dotsize = self.initial_dotsize
        self.linethick = self.initial_linethick
        self._apply()
        self.hide()

def getPlotOptions():
    dialog = PlotOptionsDialog(None)
    dialog.show()

def main():
    import logging
    from pyspec.css_logger import addStdOutHandler
    # addStdOutHandler(logging.DEBUG)
    addStdOutHandler()

    app = QApplication([])
    main = QMainWindow()
    dialog = PlotOptionsDialog(main)
    but = QPushButton("hello")
    but.clicked.connect(dialog.show)
    
    main.setCentralWidget(but)
    main.show()
    
    try:
        exec_ = getattr(app,"exec_")
    except AttributeError:
        exec_ = getattr(app,"exec")
    exec_()

if __name__ == '__main__':
    main()
