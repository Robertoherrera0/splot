#******************************************************************************
#
#  @(#)ColumnSelectionWidget.py	3.12  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2020,2023,2024
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
import sys
import copy
import weakref

from pyspec.css_logger import log

from Colors import ColorWidget, ColorTable

from Constants import *

import icons

from Features import haveFeature

class ColorCellWidget(QWidget):

    def __init__(self, color, *args):
        QWidget.__init__(self, *args)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.colorWidget = ColorWidget(color, self)
        self.layout().addWidget(self.colorWidget)

    def cwidget(self):
        return self.colorWidget


NB_TREE_COLUMNS = 7
NAME_COLUMN, X_COLUMN, Y1_COLUMN, Y2_COLUMN, COLOR_COLUMN, DUP_COLUMN, \
    SPACER_COLUMN = range(NB_TREE_COLUMNS)

NB_E_TREE_COLUMNS = 7
E_NAME_COLUMN, E_Y1_COLUMN, E_Y2_COLUMN, E_COLOR_COLUMN, E_DUP_COLUMN,  \
    E_BIN_COLUMN, E_SPACER_COLUMN = range(NB_E_TREE_COLUMNS)

class ColumnTreeItem(QTreeWidgetItem):


    def __init__(self, parent, tree, xgroup, *args):

        super(ColumnTreeItem, self).__init__(tree, *args)

        self.tree = tree
        self.parent = parent
        self.columnName = None
        self.color = None

        self.buttonGroup = QButtonGroup()
        self.buttonGroup.setExclusive(False)

        self.xbutton = QRadioButton("", self.tree)
        self.xbutton.setObjectName("xcolbutton")
        self.xbutton.setFixedWidth(20)
        self.y1button = QRadioButton(self.tree)
        self.y2button = QRadioButton(self.tree)

        self.moreWidget = QWidget()
        self.moreLayout = QHBoxLayout()
        self.moreLayout.setContentsMargins(0, 0, 0, 0)
        self.moreLayout.setSpacing(2)
        self.moreWidget.setLayout(self.moreLayout)

        self.colorWidget = ColorWidget("black", self.tree)
        self.colorWidget.setToolTip("Change curve color")
        icondir = os.path.join(os.path.dirname(__file__), 'icons')
        self.selectButton = QPushButton()
        self.selectButton.setToolTip("Show curve on another data source")
        self.selectButton.setFlat(True)
        self.selectButton.setIcon(icons.get_icon('pin'))

        self.moreLayout.addWidget(self.colorWidget)
        self.moreLayout.addWidget(self.selectButton)

        self.spacerLabel = QLabel("")

        xgroup.addButton(self.xbutton)
        self.buttonGroup.addButton(self.y1button)
        self.buttonGroup.addButton(self.y2button)

        self.tree.setItemWidget(self, X_COLUMN, self.xbutton)
        self.tree.setItemWidget(self, Y1_COLUMN, self.y1button)
        self.tree.setItemWidget(self, Y2_COLUMN, self.y2button)
        self.tree.setItemWidget(self, COLOR_COLUMN, self.colorWidget)
        self.tree.setItemWidget(self, DUP_COLUMN, self.selectButton)
        self.tree.setItemWidget(self, SPACER_COLUMN, self.spacerLabel)
        #self.xbutton.clicked.connect(self.xChanged)

        self.buttonGroup.buttonClicked.connect(self.ySelectionChanged)

        self.colorWidget.colorChanged.connect(self.colorChanged)
        self.selectButton.clicked.connect(self._addToSelection)

    def setColumnName(self, colname):
        self.columnName = colname
        self.setText(NAME_COLUMN, self.columnName)

    def getColumnName(self):
        return self.columnName 

    def setColor(self, color):
        self.color = color
        self.colorWidget.setColor(color)

    def getColor(self):
        return self.color

    def xChecked(self):
        return self.xbutton.isChecked()

    def y1Checked(self):
        return self.y1button.isChecked()

    def y2Checked(self):
        return self.y2button.isChecked()

    def setXChecked(self, flag):
        self.xbutton.setChecked(flag)

    def setY1Checked(self, flag):
        self.y1button.setChecked(flag)

    def setY2Checked(self, flag):
        self.y2button.setChecked(flag)

    def enableY1(self):
        self.y1button.setEnabled(True)
    def disableY1(self):
        self.y1button.setEnabled(False)
        self.y1button.setChecked(False)

    def enableY2(self):
        self.y2button.setEnabled(True)
    def disableY2(self):
        self.y2button.setEnabled(False)
        self.y2button.setChecked(False)

    def getSelection(self):
        x = self.xbutton.isChecked()
        y1 = self.y1button.isChecked()
        y2 = self.y2button.isChecked()
        return [x, y1, y2]

    def ySelectionChanged(self, button):
        selected = button.isChecked()
        buttons = self.buttonGroup.buttons()
        if selected:
            for but in buttons:
                if but is not button:
                    but.setChecked(False)
        self.parent.yChanged(self)

    def colorChanged(self, color):
        self.color = str(color)
        #log.log(2,color)
        #log.log(2, str(color))
        self.parent.colorChanged(self.columnName, self.color)

    def _addToSelection(self):
        self.parent._getColumnData(self)

class ExtraColumnTreeItem(QTreeWidgetItem):

    def __init__(self, parent, tree, *args):

        super(ExtraColumnTreeItem, self).__init__(tree, *args)

        self.tree = tree
        self.parent = parent
        self.columnName = None
        self.color = None

        icondir = os.path.join(os.path.dirname(__file__), 'icons')

        self.buttonGroup = QButtonGroup()
        self.buttonGroup.setExclusive(False)

        self.moreWidget = QWidget()
        self.moreLayout = QHBoxLayout()
        self.moreLayout.setContentsMargins(0, 0, 0, 0)
        self.moreLayout.setSpacing(2)
        self.moreWidget.setLayout(self.moreLayout)

        self.y1button = QRadioButton()
        self.y2button = QRadioButton()

        self.lockButton = QPushButton()
        self.lockButton.setFlat(True)

        self.basketButton = QPushButton()
        self.basketButton.setToolTip("Remove curve")
        self.basketButton.setFlat(True)
        self.basketButton.setIcon(icons.get_icon('basket'))

        self.colorWidget = ColorWidget("black", self.tree)
        self.colorWidget.setToolTip("Change curve color")

        self.moreLayout.addWidget(self.colorWidget)
        self.moreLayout.addWidget(self.lockButton)
        self.moreLayout.addWidget(self.basketButton)

        self.spacerLabel = QLabel("  ")

        self.tree.setItemWidget(self, E_Y1_COLUMN, self.y1button)
        self.tree.setItemWidget(self, E_Y2_COLUMN, self.y2button)
        self.tree.setItemWidget(self, E_COLOR_COLUMN, self.colorWidget)
        self.tree.setItemWidget(self, E_DUP_COLUMN, self.lockButton)
        self.tree.setItemWidget(self, E_BIN_COLUMN, self.basketButton)
        self.tree.setItemWidget(self, E_SPACER_COLUMN, self.spacerLabel)

        self.buttonGroup.addButton(self.y1button)
        self.buttonGroup.addButton(self.y2button)

        self.colorWidget.colorChanged.connect(self.colorChanged)
        self.basketButton.clicked.connect(self.deleteCurve)
        self.lockButton.clicked.connect(self.lockCurve)

        self.buttonGroup.buttonClicked.connect(self.ySelectionChanged)

    def setColumnName(self, colname):
        self.columnName = colname
        self.setText(E_NAME_COLUMN, self.columnName)

    def setAxis(self, axis):
        if axis == 'y1':
            self.y1button.setChecked(True)
            self.y2button.setChecked(False)
        elif axis == 'y2':
            self.y1button.setChecked(False)
            self.y2button.setChecked(True)
        else:
            self.y1button.setChecked(False)
            self.y2button.setChecked(False)

    def setLocked(self, lock_state):
        if lock_state is True:
           self.lockButton.setIcon(icons.get_icon('lock'))
           self.lockButton.setToolTip("Click to unlock")
        else:
           self.lockButton.setIcon(icons.get_icon('unlock'))
           self.lockButton.setToolTip("Click to lock")
        self.lock_state = lock_state

    def setColor(self, color):
        self.color = color
        self.colorWidget.setColor(color)

    def ySelectionChanged(self, button):
        if button.isChecked():
            for but in self.buttonGroup.buttons():
                if but is not button:
                    but.setChecked(False)
                else:
                    if but is self.y2button:
                        axis = 'y2'
                    else:
                        axis = 'y1'
        else:
            axis = ''

        self.parent.setExtraCurveAxis(self.columnName, axis)

    def colorChanged(self, color):
        self.color = str(color)
        self.parent.colorChanged(self.columnName, str(color))

    def lockCurve(self):
        self.parent.setLockCurve(self.columnName,not self.lock_state)

    def deleteCurve(self):
        self.parent.deleteCurve(self.columnName)


class ColumnSelectionWidget(QWidget):

    def __init__(self, *args):

        super(ColumnSelectionWidget, self).__init__(*args)

        self.datablock = None
        self.colorTable = ColorTable()

        self.max_x_allowed = 1
        self.max_y1_allowed = None
        self.max_y2_allowed = None
        self.twod_selection_mode = False

        self.column_data_handler = None

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        self.actionWidget = QWidget()
        self.actionLayout = QHBoxLayout()
        self.actionWidget.setLayout(self.actionLayout)

        self.resetButton = QPushButton("Reset to Default")

        if haveFeature("2D"):
            self.modeLabel = QLabel("Mode:")
            self.modeCombo = QComboBox()
            self.modeCombo.addItems(['1D', '2D'])
        
            self.actionLayout.addWidget(self.modeLabel)
            self.actionLayout.addWidget(self.modeCombo)

            self.modeCombo.currentIndexChanged.connect(self.modeComboChanged)

        self.actionLayout.addWidget(self.resetButton)

        self.extraLabel = QLabel("Added columns:")

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.colorTable.colorChanged.connect(self.changeColumnColor)
        self.xSelectionGroup = QButtonGroup(self)
        self.xSelectionGroup.setExclusive(False)

        self.resetButton.clicked.connect(self.resetDefault)
        self.xSelectionGroup.buttonClicked.connect(self.xChanged)

        self.items = []
        self.columnNames = []

        self.extra_items = []
        self.extra_columns = []

        self.initTree()
        self.initExtraTree()

        self.extraLabel.hide()
        self.extraTreeWidget.hide()

        layout.addWidget(self.actionWidget)
        layout.addWidget(self.treeWidget, 2)
        layout.addWidget(self.extraLabel)
        layout.addWidget(self.extraTreeWidget)

    def initTree(self):

        self.header_labels = ["Name", "X", "Y", "Y2", "C", "...", " "]

        self.treeWidget = QTreeWidget()
        #self.treeWidget.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.treeWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.treeWidget.setObjectName("columnSelectionWidget")

        self.treeWidget.clear()
        self.treeWidget.setColumnCount(NB_TREE_COLUMNS)
        self.treeWidget.setRootIsDecorated(False)
        self.treeWidget.setAlternatingRowColors(True)
                            
        font_metrics = QFontMetrics(self.font())
        self.cell_margin = 7

        self.treeWidget.header().setMinimumSectionSize(25)
        #self.treeWidget.setColumnAlignment()
        self.treeWidget.header().setStretchLastSection(True)

        for colno in range(len(self.header_labels)):
            label = self.header_labels[colno]
            column_width = font_metrics.boundingRect(label).width() + 2*self.cell_margin
            self.treeWidget.header().resizeSection(colno, column_width)

        self.treeWidget.setHeaderLabels( self.header_labels )

        #self.columnArea.setAlignment(Qt.AlignHCenter)
        #self.columnArea.setWidget(self.treeWidget)
        #self.columnArea.setWidgetResizable(True)

    def initExtraTree(self):
        self.extraTreeWidget = QTreeWidget()
        self.extraTreeWidget.setFixedHeight(120)
     
        #self.extraColumns.setWidget(self.extraTreeWidget)
        #self.extraColumns.setWidgetResizable(True)
        #self.extraColumns.setAlignment(Qt.AlignHCenter)

        self.extra_header_labels = ["Name", "Y1", "Y2", "C", "L", "D",""]
        self.extraTreeWidget.clear()
        self.extraTreeWidget.setColumnCount(NB_E_TREE_COLUMNS)
        self.extraTreeWidget.setRootIsDecorated(False)
        self.extraTreeWidget.setAlternatingRowColors(True)

        font_metrics = QFontMetrics(self.font())

        self.extraTreeWidget.setWordWrap(True)

        for colno in range(len(self.extra_header_labels)):
            label = self.extra_header_labels[colno]
            column_width = font_metrics.boundingRect(label).width() + 2*self.cell_margin
            self.extraTreeWidget.header().resizeSection(colno, column_width)

        self.extraTreeWidget.setHeaderLabels(self.extra_header_labels)

    def setDataBlock(self, dblock):

        if self.datablock:
            self.datablock.unsubscribe(self)            

        dblock.subscribe(self, COLUMNS_CHANGED, self.update_columns)
        dblock.subscribe(self, X_SELECTION_CHANGED, self.update_xselection)
        dblock.subscribe(self, Y1_SELECTION_CHANGED, self.update_y1selection)
        dblock.subscribe(self, Y2_SELECTION_CHANGED, self.update_y2selection)
        dblock.subscribe(self, DATACONFIG_CHANGED, self._configureExtraCurve)
        dblock.subscribe(self, PLOT2D_CHANGED, self.set2DSelectionMode)

        self.datablock = dblock

    def update_columns(self, newcolumns):
        self.setColumnNames(newcolumns)

    def update_xselection(self, xselection):
        self.setXSelection(xselection)

    def update_y1selection(self, y1selection):
        self.setY1Selection(y1selection)

    def update_y2selection(self, y2selection):
        self.setY2Selection(y2selection)

    def setColumnNames(self, newcolumns):

        column_list, extra_list =  newcolumns
        changed = False

        if column_list != self.columnNames:
            cur_xs, cur_y1, cur_y2 = self.getSelection()
    
            old_len = len(self.columnNames)
            new_len = len(column_list)
            final_len = new_len if (new_len > old_len) else old_len
    
            colno = old_len
            while colno > new_len:
                self.treeWidget.takeTopLevelItem(colno - 1)
                self.items.pop(-1)
                colno -= 1
    
            colno = old_len
            while colno < new_len:
                item = ColumnTreeItem(self, self.treeWidget, self.xSelectionGroup)
                self.items.append(item)
                self.treeWidget.addTopLevelItem(item)
                colno += 1
    
            self.columnNames = column_list
            
            # reApplySelection
            self.setXSelection(cur_xs)
            self.setY1Selection(cur_y1)
            self.setY2Selection(cur_y2)
            changed = True
    
        if extra_list != self.extra_columns:
            self.setExtraColumns(extra_list)
            changed = True

        if changed:
            self.restoreColors()

    def restoreColors(self):

        fontMetrics = QFontMetrics(self.font())

        min_name_width = fontMetrics.boundingRect("Name").width() + 2*self.cell_margin
        max_name_width = fontMetrics.boundingRect("xxxxxxxx").width() + 2*self.cell_margin
        name_width = min_name_width

        for itemno in range(len(self.columnNames)):
            item_name = self.columnNames[itemno]
            item = self.items[itemno]
            item_name_width = fontMetrics.boundingRect(item_name).width() + 2*self.cell_margin
            if item_name_width > name_width:
                 name_width = item_name_width
            item.setColumnName(item_name)

            color = self.colorTable.getColor(item_name)
            item.setColor(color)
      
        final_width = (name_width > max_name_width) and max_name_width or name_width
        self.treeWidget.header().resizeSection(NAME_COLUMN, final_width)

        itemno = 0
        for item_name in self.extra_columns:
            item = self.extra_items[itemno]
            color = self.colorTable.getColor(item_name)
            item.setColor(color)
            itemno += 1

    def setExtraColumns(self, extra_list):

        old_len = len(self.extra_columns)
        new_len = len(extra_list)

        final_len = new_len if (new_len > old_len) else old_len

        colno = old_len
        while colno > new_len:
            self.extraTreeWidget.takeTopLevelItem(colno - 1)
            self.extra_items.pop(-1)
            colno -= 1

        colno = old_len
        while colno < new_len:
            item = ExtraColumnTreeItem(self, self.extraTreeWidget)
            self.extra_items.append(item)
            self.extraTreeWidget.addTopLevelItem(item)
            colno += 1

        self.extra_columns = copy.copy(extra_list)
        self.presentExtraCurves()

        if len(self.extra_columns):
            self.extraLabel.show()
            self.extraTreeWidget.show()
        else:
            self.extraLabel.hide()
            self.extraTreeWidget.hide()

    def presentExtraCurves(self):
        fontMetrics = QFontMetrics(self.font())

        min_name_width = fontMetrics.boundingRect("Name").width() + 2*self.cell_margin
        max_name_width = fontMetrics.boundingRect("x"*15).width() + 2*self.cell_margin
        name_width = min_name_width

        for extraname in self.extra_columns:
            self._configureExtraCurve(extraname)

            item_name_width = fontMetrics.boundingRect(extraname).width() + 2*self.cell_margin
            if item_name_width > name_width:
                 name_width = item_name_width

        final_width = (name_width > max_name_width) and max_name_width or name_width
        self.extraTreeWidget.header().resizeSection(E_NAME_COLUMN, final_width)

    def _configureExtraCurve(self, colname):
        if not self.datablock:
            return

        curve, options = self.datablock.getExtraData(colname)
        itemno = self.extra_columns.index(colname)
        item = self.extra_items[itemno]
        item.setToolTip(E_NAME_COLUMN, "Origin: %s\nX-Column: %s\nY-Column:%s" % \
                    (curve['source'], curve['xcolumn'], curve['colname']))
        item.setColumnName(colname)
        item.setLocked(options['keep'])
        item.setAxis(curve['axis'])
    
        if self.colorTable.hasColor(colname):
            color = self.colorTable.getColor(colname)
        else:
            color = curve['color']
        item.setColor(color)


    def dataConfigurationChanged(self, colname):
        if colname in self.extra_columns:
            self._configureExtraCurve(colname)

    def setColumnDataHandler(self, handler):
        self.column_data_handler = (weakref.proxy(handler.__self__), weakref.proxy(handler.__func__))

    def _getColumnData(self, colitem):
        xcol, xdata, ycol, ydata, color = self.getColumnData(colitem)

        coldata = {
             'action':  'get',
             'xcolumn': xcol,
             'xdata': copy.copy(xdata),
             'colname': ycol,
             'ydata': ydata,
             'color': color,
        }

        self._handle_column_data(coldata)

    def setLockCurve(self, curvename, state):
        self.datablock.setLockExtraData(curvename, state)
       
    def deleteCurve(self, colname):
        self.datablock.deleteExtraData(colname)

    def setExtraCurveAxis(self, colname, axis):
        self.datablock.setExtraDataAxis(colname,axis)

    def _handle_column_data(self, coldata):
        if self.column_data_handler:
             obj,func = self.column_data_handler
             func(obj,coldata)

    def getColumnIndex(self, name):
        if name in self.columnNames:
            return self.columnNames.index(name)
        else:
            return -1

    def resetDefault(self):
        if self.datablock:
            self.datablock.resetDefaultColumns()

    def setSelection(self, xs, y1s, y2s=None):
        self.setXSelection(xs)
        self.setY1Selection(y1s)
        self.setY2Selection(y2s)

    def setXSelection(self, xcols):
        xsel, y1sel, y2sel = self.getSelection()

        for x in xcols:
            idx = self.getColumnIndex(x)
            if idx != -1:
                self.items[idx].setXChecked(True)

        for x in xsel:
            if x not in xcols: 
                idx = self.getColumnIndex(x)
                if idx != -1:
                    self.items[idx].setXChecked(False)

    def setYSelection(self, ys):
        self.setY1Selection(ys)
        self.setY2Selection([])

    def setY1Selection(self, y1s):
        xsel, y1sel, y2sel = self.getSelection()

        for y1 in y1s:
            idx = self.getColumnIndex(y1)
            if idx != -1:
                self.items[idx].setY1Checked(True)

        for y1 in y1sel:
            if y1 not in y1s:
                idx = self.getColumnIndex(y1)
                if idx != -1:
                    self.items[idx].setY1Checked(False)

    def setY2Selection(self, y2s):
        xsel, y1sel, y2sel = self.getSelection()

        for y2 in y2s:
            idx = self.getColumnIndex(y2)
            if idx != -1:
                self.items[idx].setY2Checked(True)

        for y2 in y2sel:
            if y2 not in y2s:
                idx = self.getColumnIndex(y2)
                if idx != -1:
                    self.items[idx].setY2Checked(False)

    def getSelection(self):

        xsel = []
        y1sel = []
        y2sel = []

        for itemno in range(len(self.columnNames)):
            item = self.items[itemno]
            colname = self.columnNames[itemno]
            xs, y1s, y2s = item.getSelection()
            if xs:
                xsel.append(colname)
            if y1s:
                y1sel.append(colname)
            if y2s:
                y2sel.append(colname)

        return [xsel, y1sel, y2sel]

    def getXSelection(self):

        xsel = []

        for itemno in range(len(self.columnNames)):
            item = self.items[itemno]
            if item.xChecked():
                colname = self.columnNames[itemno]
                xsel.append(colname)
        return xsel

    def getY1Selection(self):
        y1sel = []

        for itemno in range(len(self.columnNames)):
            item = self.items[itemno]
            y1 = item.y1Checked()
            if y1:
                colname = self.columnNames[itemno]
                y1sel.append(colname)

        return y1sel

    def getY2Selection(self):
        y2sel = []

        for itemno in range(len(self.columnNames)):
            item = self.items[itemno]
            y2 = item.y2Checked()
            if y2:
                colname = self.columnNames[itemno]
                y2sel.append(colname)

        return y2sel

    def modeComboChanged(self, idx):
        if idx == 0:
           self._set2DSelectionMode(False)
        else:
           self._set2DSelectionMode(True)

        if self.datablock:
           self.datablock.setMode2D(self.twod_selection_mode)

    def setMaximumXSelection(self, max_allowed):
        self.max_x_allowed = max_allowed

    def setMaximumYSelection(self, max_y1_allowed, max_y2_allowed=None):
        self.max_y1_allowed = max_y1_allowed
        self.max_y2_allowed = max_y2_allowed

        # if max is 0. do not allow to select
        if self.max_y2_allowed == 0:  
            for itemno in range(len(self.columnNames)):
                item = self.items[itemno]
                item.disableY2()
        else:
            for itemno in range(len(self.columnNames)):
                item = self.items[itemno]
                item.enableY2()

        if self.max_y1_allowed == 0:  
            for itemno in range(len(self.columnNames)):
                item = self.items[itemno]
                item.disableY1()
        else:
            for itemno in range(len(self.columnNames)):
                item = self.items[itemno]
                item.enableY1()

    def set2DSelectionMode(self, mode):
        self._set2DSelectionMode(mode)
        if mode:
            self.modeCombo.setCurrentIndex(1)
        else:
            self.modeCombo.setCurrentIndex(0)

    def _set2DSelectionMode(self, mode):

        self.twod_selection_mode = mode

        if mode:
            self.setMaximumXSelection(2)
            self.setMaximumYSelection(1, 0)
        else:
            self.setMaximumXSelection(1)
            self.setMaximumYSelection(None,None)
     
    def xChanged(self, button):

        # Make sure only one X button is checked

        no_checked = 0
        selected = button.isChecked()

        if selected:
            for but in self.xSelectionGroup.buttons():
                if but is not button:
                    if but.isChecked():
                        no_checked += 1
                    if no_checked >= (self.max_x_allowed):
                        but.setChecked(False)

        if self.datablock:
            self._updateDataBlock()

    def _updateDataBlock(self):
        xs, y1s, y2s = self.getSelection()
        self.datablock.setSelection(xs,y1s,y2s)
        
    def yChanged(self, on_item):

        no_checked = 0

        if self.max_y1_allowed not in [None,0]:  # there is a restriction
            item_y1_checked = on_item.y1Checked()

            if item_y1_checked:
                no_checked = 0
                for itemno in range(len(self.columnNames)):
                    item = self.items[itemno]
                    if item is not on_item:
                        if item.y1Checked():
                            no_checked += 1
                        if no_checked >= self.max_y1_allowed:
                            item.setY1Checked(False)

        if self.max_y2_allowed not in [None,0]:  # there is a restriction
            item_y2_checked = on_item.y2Checked()

            if item_y2_checked:
                no_checked = 0
                for itemno in range(len(self.columnNames)):
                    item = self.items[itemno]
                    if item is not on_item:
                        if item.y2Checked():
                            no_checked += 1
                        if no_checked >= self.max_y2_allowed:
                            item.setY2Checked(False)

        if self.datablock:
            self._updateDataBlock()

    def getColumnData(self, colitem):
        ycolumn = colitem.getColumnName()
        color = colitem.getColor()
        xcol, xdata, ycol, ydata = self.datablock.getXYDataForColumn(ycolumn)
        return [xcol, xdata, ycol, ydata, color]

    def getColumnColor(self,colname):
        idx = self.getColumnIndex(colname)
        if idx != -1:
            item = self.items[idx]
            return item.getColor()
        else:
            return None

    def colorChanged(self, colname, color):
        ColorTable().setColor(colname, color)

    def changeColumnColor(self, colname, color):
        idx = self.getColumnIndex(colname)
        if idx != -1:
            item = self.items[idx]
            item.setColor(color)

class ColumnSelectionDialog(QDialog):

    def __init__(self, title, columnlist, extralist, defaultselection=None):

        QDialog.__init__(self)

        self.setWindowTitle("Column Selection")
        self.setModal(True)

        vBoxLayout = QVBoxLayout()
        self.setLayout(vBoxLayout)

        if extralist is None:
            extralist = []

        self.widget = ColumnSelectionWidget(self)
        self.widget.setColumnNames([columnlist, extralist])
        vBoxLayout.setAlignment(self.widget, Qt.AlignTop)

        if defaultselection:
            self.widget.setSelection(*defaultselection)

        vBoxLayout.addWidget(self.widget)

        buttonHBoxLayout = QHBoxLayout()

        okPushButton = QPushButton("Ok")
        okPushButton.clicked.connect(self.okPushButtonClicked)
        #Qt.QObject.connect(okPushButton, Qt.SIGNAL("clicked()"), self.okPushButtonClicked)
        buttonHBoxLayout.addWidget(okPushButton)

        cancelPushButton = QPushButton("Cancel")
        cancelPushButton.clicked.connect(self.cancelPushButtonClicked)
        #Qt.QObject.connect(cancelPushButton, Qt.SIGNAL("clicked()"), self.cancelPushButtonClicked)
        buttonHBoxLayout.addWidget(cancelPushButton)

        vBoxLayout.addLayout(buttonHBoxLayout)

    def setMaximumXSelection(self,allowed):
        self.widget.setMaximumXSelection(allowed)

    def setExtraColumns(self, collist):
        self.widget.setExtraColumns(collist)

    def cancelPushButtonClicked(self):
        self.reject()

    def okPushButtonClicked(self):
        self.accept()

    def getSelection(self):
        return self.widget.getSelection()


def getColumnSelection(title="Column Selection", collist=[], extracols=None, defselection=None):

    extra_cols = {"31oct98.dat.s1:Detector": [{"source":"toto","xcolumn":"X","ycolumn":"TZ","axis":"Y1","color":"blue"},{"keep":True}]} 
    dialog = ColumnSelectionDialog(title, collist, extra_cols, defselection)
    dialog.setMaximumXSelection(2)

    result = dialog.exec_()
    if result == QDialog.Accepted:
        retval = dialog.getSelection()
    else:
        retval = None
    dialog.destroy()
    return retval
   
if __name__ == '__main__':

    from pyspec.css_logger import addStdOutHandler

    app = QApplication([])
    collist = ["th", "monitor", "det", "roi1", "roi2"]
    selected = ["th", ["det"], ["roi1", "roi2"]]
    extra_cols = ["31oct98.dat.s1:Detector", "something"]
    print(getColumnSelection("Column Selection", collist, extra_cols, selected))
