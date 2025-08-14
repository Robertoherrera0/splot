#******************************************************************************
#
#  @(#)SpecDataSource.py	3.20  07/21/21 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2020,2021
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
import sys
import time
import copy
import weakref

from pyspec.graphics.QVariant import *
from pyspec.css_logger import log

from Constants import *
import DataBlock

from DataSource1D import DataSource1D
from ServerPanel import ServerPanel
from MotorWidget import MotorWidget
from Features import haveFeature
from Scan import Scan

class SpecVariableSource(DataSource1D):

    def __init__(self, parent, spec_source, varname):

        sourcetype = SOURCE_SPEC
        name = varname

        self.spec_source = spec_source

        DataSource1D.__init__(
            self, parent, sourcetype, name)

        self.varname = varname
        self.connected = False

    def follow(self):
        self.variabletimer = QTimer()
        self.variabletimer.timeout.connect(self.updateMe)
        self.variabletimer.start(UPDATE_VARIABLE)

    def updateMe(self):
        # first check if mother spec_source is connected
        #   only then, start updating data. 
        if self.spec_source.isConnected():
            self.connected = True
            self.spec_connection = self.spec_source.specConn
            self.updateConnData()
        else: 
            self.connected = False

    def updateConnData(self):
        if self.connected:
            if self.spec_connection.variable_updated(self.varname):
                data, meta = self.spec_connection.get_data_variable(self.varname)
                self.setData(data)

class SpecDataSource(DataSource1D):

    specConnected = pyqtSignal(int)
    filenameChanged = pyqtSignal(str)
    sourcetype = SOURCE_SPEC

    def __init__(self, parent, specname, variable=None, filtername="1"):

        self.specname = specname
        self.parent = parent

        self.filtername = filtername  #  used by spec to address different source for same spec
        self.plotconfig = None
        self.plotconfig_modified = True
        self.slice_atpoint = 0
        self.slice_latest_size = None

        self.is_connected = False
        self.is_server_connected = False
        self.scanobj = Scan()

        self.children = {}

        if variable is None:
            variable = "SCAN_D"

        if variable == "SCAN_D":
            name = specname
        else:
            name = variable

        self.variable = variable

        DataSource1D.__init__(
            self, parent, self.sourcetype, name)

        self.datablock.subscribe(self, X_SELECTION_CHANGED, self._updateFollowMotor)

        self.specValue.setText(specname)
        self.plot_w.showSourceStatus()
        self.plot_w.setServerStatus(STATUS_OFF)

        self.lastTimeGUIUpdated = time.time()

    def init(self):

        DataSource1D.init(self)
        self.paramsInit = False
        self.user = ""
        self.date = ""
        self.hkl = ""

        self.status = 1
        self.datastatus = DATA_UNKNOWN
        self.data = np.array([], ndmin=2)
        self.specConn = None

        self.scan_status = "unknown"

        self.last_scanno = 0
        self.last_pt_added = 0
        self.last_status = "unknown"

        self.scanno = -1
        self.allmotorm = {}
        self.metadata = {}

        self.current_motor_mne = None

        self.just_finished = False

        self.selectedcounters = None
        self.filename = None

        self.buffered_points = []
        self.buffered_point_indexes = []

        self.initOk = False

    def init_widget(self):
        self.motorWidgets = {}

        self.topWidget = QWidget()

        self.topLayout = QGridLayout()
        self.topLayout.setSpacing(3)
        self.topLayout.setContentsMargins(0, 0, 0, 0)

        self.specLabel = QLabel("spec:")
        self.specValue = QLabel("")
        self.specValue.setObjectName("specname")

        self.spacer = QLabel("")
        self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.variableLabel = QLabel("Displaying:")
        self.variableValue = QLabel("")

        self.statusLabel = QLabel("Status:")
        self.statusValue = QLabel("")
        self.statusValue.setObjectName("readystatus")


        self.topLayout.addWidget(self.specLabel, 0, 0)
        self.topLayout.addWidget(self.specValue, 0, 1)
        self.topLayout.addWidget(self.spacer, 0, 2, 5, 1)

        self.topLayout.addWidget(self.variableLabel, 1, 0)
        self.topLayout.addWidget(self.variableValue, 1, 1)

        self.topLayout.addWidget(self.statusLabel, 2, 0)
        self.topLayout.addWidget(self.statusValue, 2, 1)

        self.topWidget.setLayout(self.topLayout)

        self.set_source_header_widget(self.topWidget)

        self.serverPanel = ServerPanel()

        self.statusDisconnected()

        self.timer = QTimer()
        self.timer.timeout.connect(self.checkData)

        self.variabletimer = QTimer()
        self.variabletimer.timeout.connect(self.basicScanDisplay)

        self.servertimer = QTimer()
        self.servertimer.timeout.connect(self.server_update)

        self.showServerPanel()

    def init_source_area(self):
        self.show_column_selection_widget()
        self.show_metadata_widget()

    def set_connection(self, conn):

        self.specConn = conn
        self.specname = conn.getName()
        self.startWatch()

        if not self.specConn.is_remote():
            if haveFeature("embed_xterm"): 
                import getpid 
                import QTerminal 
                if not getpid.getpid(self.specname):
                    log.log(3,"spec %s is not running. starting it" % self.specname)
                    self.spec_terminal = QTerminal.QTerminal(self.specname)
                    self.main_splitter.addWidget(self.spec_terminal)
                else:
                    log.log(3,"spec %s is running" % self.specname)
            else:
                 log.log(3,"embed xterm not available")

        #if self.specConn.isServerMode():
        #if True:
            #self.plot_w.setServerMode(True)
            #self.plot_w.setAbortAction(self.abort)

    def getTypeString(self):
        return "spec"

    def getSpecName(self):
        return self.specname

    def getDescription(self):
        return "%s_s%s" % (self.getSourceName(), self.scanno)

    def getVariableName(self):
        return self.variable

    def getConnectName(self):
        return self.connectpars

    def update(self):
        host = self.getHost()
        spec = self.getSpecName()

        if host is None or host == "localhost":
            specValue = "%s" % spec
        else:
            specValue = "%s:%s" % (host, spec)

        self.specValue.setText(specValue)

        if self.specConn:
            #if not self.specConn.isScanData():
                self.variableValue.setText(self.specConn.getVariable())
            #else:
                #self.variableValue.setText("scan data")

        if self.is_connected is False:
            self.statusDisconnected()
        else:
            self.statusConnected()

        self.style().unpolish(self)
        self.style().polish(self)

    def statusDisconnected(self):
        self.statusValue.setText("GANS: Disconnected")
        self.statusValue.setStyleSheet("""
            font-family: 'Segoe UI', 'IBM Plex Sans', sans-serif;
            font-size: 10pt;
            font-weight: 500;
            color: #9e9e9e;  /* grey text */
            background-color: transparent;
            border: none;
        """)

        self.plot_w.setServerStatus(STATUS_OFF)


    def statusConnected(self):
        if self.status == 1:
            self.statusValue.setText("GANS: Ready")
            self.statusValue.setStyleSheet("""
                font-family: 'Segoe UI', 'IBM Plex Sans', sans-serif;
                font-size: 10pt;
                font-weight: 500;
                color: #2e7d32;  /* green text */
                background-color: transparent;
                border: none;
            """)
            self.serverPanel.setBusy(False)
        else:
            self.statusValue.setText("GANS: Busy")
            self.statusValue.setStyleSheet("""
                font-family: 'Segoe UI', 'IBM Plex Sans', sans-serif;
                font-size: 10pt;
                font-weight: 500;
                color: #ff9800;  /* amber/orange text */
                background-color: transparent;
                border: none;
            """)
            self.serverPanel.setBusy(True)


    # shm
    def checkData(self):

        # update loop via timer in case of SHM
        self.checkConnection()

        if not self.isConnected():
            return

        if not self.specConn.shm_conn_ready:
            return

        newdata = self.specConn.hasNewData()

        # image data
        if self.specConn.isImage():
            if newdata:
                self.updateConnData()
                self.image_w.updateData()
            return

        # plot data
        infoOk = self.specConn.updateInfo()

        if not infoOk:
            if newdata:
                self.basicScanDisplay()
            return

        if not newdata:
            return

        status = self.specConn.getStatus()
        scanno = self.specConn.getScanNumber()
        pointno = self.specConn.getLastPointNo()

        do_update = False

        if self.last_status != status:
            if status == "idle":
                self.timer.setInterval(UPDATE_IDLE)
                self.checkRaise(endscan=True)
            else:
                pass

            self.statusChanged(status)
            self.last_status = status

        if scanno != self.last_scanno:
            self.newScan(update=True)
        elif pointno != -1 and pointno != self.last_pt_added:
            self.newScanPoints(pointno)
        else:  # shm changed but not new points. metadata 
            self.newScanPoints(pointno, refresh=True)

    # both
    def startWatch(self):
        self.start_watch_server()
        self.start_watch_shm()

    # both
    def stopWatch(self):
        try:
            self.stop_watch_server()
            self.stop_watch_shm()
        except:
            pass

    # shm
    def start_watch_shm(self):
        self.timer.start(UPDATE_IDLE)

    # shm
    def stop_watch_shm(self):
        self.timer.timeout.disconnect(self.checkData)

    # server
    def start_watch_server(self):
        #if self.specConn.isScanData():
            self.servertimer.start(UPDATE_SERVER)
        #else:
            #self.variabletimer.start(UPDATE_VARIABLE)

    # server
    def stop_watch_server(self):
         #if self.specConn.isScanData():
             self.servertimer.timeout.disconnect(
                        self.server_update)
         #else:
             #self.variabletimer.timeout.disconnect(
                        #self.basicScanDisplay)

    # server
    def showServerPanel(self):
        self.tabs.addTab(self.serverPanel, "Command Server")
        self.serverPanel.setDataSource(weakref.ref(self))
        self.serverPanel.setDataBlock(self.datablock)

    # server
    def _updateFollowMotor(self, cur_x=None):

        if cur_x is None:
            cur_mot = self.datablock.getXSelection()[0]
        else:
            if len(cur_x) > 0:
                cur_mot = cur_x[0]
            else:
                cur_mot = None

        if cur_mot not in self.allmotorm:
            alias = self.datablock.getCanonic(cur_mot)
            if alias in self.allmotorm:
                cur_mne = alias
            else:
                cur_mne = None
        else:
            cur_mne = cur_mot

        if cur_mne != self.current_motor_mne:
            if self.current_motor_mne is not None:
                self.specConn.unfollowMotor(self.current_motor_mne)
    
            if cur_mne is not None:
                self.specConn.followMotor(cur_mne)
                self.plot.showMotorMarker()
            else:
                self.plot.hideMotorMarker()
     
        self.current_motor_mne = cur_mne

    def setPlotConfigModified(self, flag):
        # set internal flag to force a refresh in plotconfig
        #  if there is a change in display. plot command for example
        self.plotconfig_modified = flag

    def updatePlotConfig(self, plotconfig):

        if plotconfig == self.plotconfig:
            return

        self.plotconfig = copy.copy(plotconfig)
        self.setPlotConfigModified(True)
        self._updatePlotConfig()

    def _updatePlotConfig(self):

        if not self.plotconfig_modified:
            return

        self.setPlotConfigModified(False)
        self.plot.setPlotConfig(self.plotconfig, self.filtername)
        self.checkChildren()

    # both
    def checkChildren(self):

        # handle children if necessary
        plotconfig = self.plotconfig
        if plotconfig is None:
            return

        mode = int(plotconfig.get("mode", 0))

        filters = {}
        if not (mode & PL_MULTI_SPLOT):
            filtname = "1"
            if 'yColumns' in self.metadata.keys():  # split version of meta['selectedcounters']
                filters[filtname] = self.metadata['yColumns']
            self.datablock.setDefaultModeDefault()  #  remove overriden
        else:
            cntinfilter = plotconfig.get("cntinfilter", "")
            
            cnts = cntinfilter.split(";")

            for cnt in cnts:
                if not cnt.strip():
                    continue
                filtname, colname = cnt.split("-")

                if filtname not in filters:
                    filters[filtname] = [colname]
                else:
                    filters[filtname].append(colname)

        # if not MULTI_SPLOT filters will be empty
        if "1" not in filters.keys() and len(filters.keys()) > 0:
            # "1" filter not provided. Set first as "1"
            thekey = filters.keys()[0]
            filters["1"] = filters[thekey]
            filters.pop(thekey)

        for childname in self.children.keys():
            if childname not in filters:
                self.closeChild(childname)

        for filtname in filters:
            if filtname not in self.children and filtname != "1":
                if filtname != "1":   # 1 is the main window
                    self.createChild(filtname)

            self.setChildColumns(filtname, filters[filtname])

    # both
    def closeChild(self, childname):
        realname, child = self.children[childname]
        self.children.pop(childname)
        self.app.closeSource(child)

    # both
    def createChild(self, filtname):
        child = SpecDataChild(self, filtname)
        sname = "%s-%s" % (self.getSourceName(), filtname)
        realname = self.app.addSource(child, sname)
        child.set_connection(self.specConn)
        self.app.detach(realname)
        self.children[filtname] = [realname, child]

    # both
    def setChildColumns(self, childname, columnlist):
        if childname == "1":
            self.setY1Selection(columnlist, override_default=True)
        else:
            realname, child = self.children[childname]
            child.setY1Selection(columnlist, override_default=True)

    # both
    def checkRaise(self, endscan=False):

        if self.plotconfig is None:
            return

        mode = int(self.plotconfig.get("mode", 0))

        doraise = False
        if (not (mode & PL_RAISE_1)):
            doraise = True

        if endscan:
            if (not (mode & PL_RAISE_2)):
                doraise = True

        if doraise:
            self.raiseAll()

    # both
    def raiseAll(self):
        for childname in self.children:
            realname, child = self.children[childname]
            child.xraise()

        self.xraise()

    # server
    def scanMotorPositionChanged(self, motor, position):
        self.plot.motorPositionChanged(motor, position)

    # shm
    def checkConnection(self):

        if self.specConn.checkConnection():
            if self.isConnected() is False:
                self.connected()
        else:
            if self.isConnected():
                self.disconnected()

    def isConnected(self):
        return self.is_connected

    def server_connected(self):
        self.is_server_connected = True
        self.updateMotorTable()
        self.connected()

    def connected(self):
        self.specConnected.emit(1)
        self.is_connected = True

        self.serverPanel.setConnected()
        self.plot_w.setServerStatus(STATUS_READY)

        self.plot.pointSelected.connect(self.pointSelection)
        self.plot.regionSelected.connect(self.regionSelection)

        self.update()

    def server_disconnected(self):
        self.is_connected = False
        self.is_server_connected = False
        self.disconnected()

    def disconnected(self):
        self.specConnected.emit(0)
        self.statusDisconnected()
        self.is_server_connected = False
        self.timer.start(UPDATE_IDLE)
        self.plot_w.setServerStatus(STATUS_OFF)
        self.update()

    def close(self):
        self.stopWatch()

        self.specConn.server_close()
        DataSource1D.close(self)
        for mne in self.motorWidgets:
            wid = self.motorWidgets[mne]
            wid.setClosed()

    # server
    def abort(self):
        self.specConn.abort()

    # server (at least for now).  only used in ScanWidget in server panel
    def hasHKL(self):
        return self.specConn.getHKLColumns()

    # server
    def statusReady(self, newstatus):
        self.status = newstatus
        if newstatus:
             self.plot_w.setServerStatus(STATUS_READY)
        else:
             self.plot_w.setServerStatus(STATUS_BUSY)
        self.update()

    # server
    def statusShell(self, newstatus):
        if newstatus:
            self.status = 0
            self.plot_w.setServerStatus(STATUS_BUSY)
        else:
            self.status = 1
            self.plot_w.setServerStatus(STATUS_READY)

        self.update()

    def statusChanged(self, newstatus):
        #

        if newstatus != self.scan_status:
            if newstatus == "running":
                self.datastatus = DATA_LIVE
                self.newScan()

            if newstatus == "idle":
                try:
                    self.syncBufferedPoints()
                    self.checkRaise(endscan=True)
                except BaseException as e:
                    log.log(2, "exception setting status %s" % str(e))
                self.datastatus = DATA_STATIC

            if newstatus == "endless":
                self.datastatus = DATA_TREND

        self.scan_status = newstatus

        # updated in self.statusChanged
        self.plot_w.setDataStatus(self.datastatus)
        self.plot.replot()

    def updateMeta(self):

        self.paramsInits = True

        scanmeta = {
            'title':          "",
            'command':        "",
            'scanno': -1,
            'datastatus':     self.datastatus,
            'HKL':            "",
            'motors':         {},
            'date':           "",
        }

        try:
            scanmeta['spec'] = self.name
            scanmeta['scanno'] = self.specConn.getMeta('scanno')
            scanmeta['command'] = self.specConn.getMeta('title')
            scanmeta['title'] = "Scan %s - %s" % (scanmeta['scanno'], scanmeta['command'])
            scanmeta['scantype'] = self.specConn.getMeta('scantype')
            scanmeta['user'] = self.specConn.getMeta('user')
            scanmeta['date'] = self.specConn.getMeta('date')
            scanmeta['points'] = self.specConn.getLastPointNo()
    
            allcols = self.specConn.getDataColumns()  # get column names in scan updated
    
            scanmeta['columns'] = len(allcols)
            scanmeta['columnnames'] = allcols
    
            allmotorm = self.specConn.getMeta('allmotorm')

            if allmotorm:
                #self.allmotorm = allmotorm.split(";")
                scanmeta['motormnes'] = allmotorm.split(";")
    
            allmotors = self.specConn.getMeta('allmotors')
            if allmotors:
                self.allmotors = allmotors.split(";")
                scanmeta['motornames'] = self.allmotors
    
            allpositions = self.specConn.getMeta('allpositions')
            if allpositions:
                self.allpositions = allpositions.split(";")
    
            selcounters = self.specConn.getMeta('selectedcounters')
    
            if selcounters:
                self.selcounters = selcounters.split(";")
                scanmeta['yColumns'] = self.selcounters
    
            hklvalues = self.specConn.getMeta('hkl')
            if hklvalues:
                self.hkl = hklvalues.split(";")
                scanmeta['HKL'] = " ".join(
                    ["%.4f" % float(hklval) for hklval in self.hkl])
    
            if self.allmotorm and self.allpositions and len(self.allmotorm) == len(self.allpositions):
                scanmeta['motors'] = list( zip(self.allmotorm, self.allpositions) )
            
        except BaseException as e:
            import traceback
            log.log(2, traceback.format_exc())

        self.metadata.update(scanmeta)

        if self.is_server_connected:
            self.updateMotorTable()

        # motor ranges
        #motors = self.specConn.getMeta('motors')
        #self.metadata['ranges'] = None
#
#        if motors:
#            motors = motors.split(";")
#            starts = self.specConn.getMeta('starts')
#            stops = self.specConn.getMeta('stops')
#
#            if starts and stops:
#                ranges = {}
#                starts = starts.split(";")
#                stops = stops.split(";")
#
#                for motorno in range(len(motors)):
#                    motor = self.allmotorm[int(motors[motorno])]
#                    ranges[motor] = [starts[motorno], stops[motorno]]
#
#                self.metadata['ranges'] = ranges


        self.datablock.setMetaData(self.metadata)  
        self.updateDataInfo()
        return self.metadata

    def updateConnData(self):
        data = self.specConn.getData(noinfo=True)
        self.setData(data)

    def basicScanDisplay(self):
        self.updateConnData()
        self.updateDataInfo()

    def newScan(self, update=False):

        self.updateMeta()               # get metadata updated

        # create a command object
        if 'command' in self.metadata:
            try:
                scan = Scan(self.metadata['command'])
            except:
                log.log(1,"Cannot parse scan command: %s" % self.metadata['command'])
                scan = Scan()
        else:
            scan = Scan()
        

        #if 'scantype' in self.metadata:
            #scan.setScanType(self.metadata['scantype'])

        #if 'ranges' in self.metadata and self.metadata['ranges']:
            #scan.setMotorRanges(self.metadata['ranges'])

        self.setScanObject(scan)

        # First scan
        if not self.initOk:
            # scan is new but data may exist
            data = self.specConn.getData()
            self.last_pt_added = data.shape[0]
            self.initOk = True
        elif update:
            data = self.specConn.getData()
            self.last_pt_added = data.shape[0]
            self.plotconfig_modified = True
        else:
            self.buffered_points = []
            self.buffered_point_indexes = []
            self.last_pt_added = 0
            self.datablock.resetData()
            data = None

        self.setData(data, self.metadata["columnnames"], self.metadata)

        self._updateFollowMotor()

        self._updatePlotConfig()  # give a change to re-apply the plotconfiguration

        self.scanno = self.specConn.getScanNumber()
        self.filepath = self.specConn.getFilePath()

        if not self.specConn.is_remote():
            self.setFilename(self.filepath)

        self.last_scanno = self.scanno

        self.timer.setInterval(UPDATE_ACTIVE)
        self.serverPanel.newScan(self.metadata)


    # server
    def addScanPoint(self, ptidx, point):

        if not self.scanobj.isTimeScan() and not self.scanobj.isMesh():
            if ptidx < self.last_pt_added:
                log.log(3,"point number smaller than last one")
                self.newScan()

        self.buffered_point_indexes.append(ptidx)
        self.buffered_points.append(point)
        self.last_pt_added = ptidx
        self.meta_widget.setPoints(ptidx)

    # both
    def meshSliceStarted(self, atpoint):
        if atpoint == self.slice_atpoint:
            return

        if atpoint > self.slice_atpoint:
            self.latest_slice_size = (atpoint - self.slice_atpoint)
        else:
            if atpoint == 0:
                self.latest_slice_size = 0
            else:
                log.log(1,"Mmmmm.  Wrong functioning with _g3 variable")
           
        self.slice_atpoint = atpoint  

    # server
    def server_update(self):
        if self.specConn.isServerMode():
            self.plot_w.setServerMode(True)
            self.plot_w.setAbortAction(self.abort)
        else:
            self.plot_w.setServerMode(False)
            if self.is_connected:
                self.status = 1
                self.statusConnected()
            else:
                self.statusDisconnected()

        self.syncBufferedPoints()

    def syncBufferedPoints(self, nbevents=0):
        if not self.initOk:
            return 

        if len(self.buffered_points):
            now = time.time()
            if (self.datastatus != DATA_LIVE) or (now - self.lastTimeGUIUpdated) > 0.05:
                try:
                    self.datablock.addPoints(self.buffered_points, self.buffered_point_indexes)
                except:
                    log.log(3," could not add points. sorry")
                    pass
                    #import traceback
                    #log.log(2, traceback.format_exc())
                    
                self.buffered_points = []
                self.buffered_point_indexes = []
                self.checkRaise()

                self.serverPanel.newPoint(self.last_pt_added)
                self.lastTimeGUIUpdated = now

    # shm
    def newScanPoints(self, last, refresh=False):

        if not self.initOk:
            return

        pointno = 0
        pointdata = np.empty(0)

        if self.scanobj.isMesh():
            if last < self.last_pt_added:
                if refresh:
                    log.log(3,
                        "I dont know how to refresh mesh if data is not in spec memory anymore")
                else:
                    if self.last_pt_added != self.latest_slice_size:
                         start = self.last_pt_added 
                         maxpts = self.latest_slice_size 
                         points1 = self._getDataPoints(self.last_pt_added,maxpts)
                         points2 = self._getDataPoints(0,last)
                         points = np.vstack([points1, points2])
                    else:
                         points = self._getDataPoints(0,last)
            else:
                if refresh:
                    points = self._getDataPoints(0, last)
                else:
                    points = self._getDataPoints(self.last_pt_added, last)
                
        elif self.scanobj.isTimeScan():
            if last < self.last_pt_added:
                if refresh:
                    log.log(3,
                        "I dont know how to refresh mesh/timescan if data is not in spec memory anymore")
                else:
                    maxpts = self.specConn.getMaxPoints()  
                    start = self.last_pt_added - maxpts/2                  
                    points = self._getDataPoints(start,last)
                    #point_indexes = range(start,last)
            else:
                if refresh:
                    self.datablock.resetData()
                    points = self._getDataPoints(0, last)
                else:
                    points = self._getDataPoints(self.last_pt_added, last)
        else:
            if refresh:
                self.datablock.resetData()
                points = self._getDataPoints(0, last)
            else:
                points = self._getDataPoints(self.last_pt_added, last)

        self.last_pt_added = last

        if (points is not None) and points.any():
            self.datablock.addPoints(points.tolist())
            self.checkRaise()

        self.meta_widget.setPoints(self.last_pt_added)

    # shm
    def _getDataPoints(self, begin, end):
        ptidx = begin

        pointno = 0
        pointdata = None

        while ptidx < end:
            try:
                point = self.specConn.getDataPoint(ptidx)
                if pointno:
                    pointdata = np.vstack((pointdata, point))
                else:
                    pointdata = point
                pointno += 1
            except:
                import traceback
                debugmsg = traceback.format_exc()
                log.log(1,"cannot read point")
                log.log(3,debugmsg)
                break
            ptidx += 1
        return pointdata

    # server
    def updateMotorTable(self):
        motlist = self.metadata.get('motormnes', None)
        if motlist is None:
            return

        if motlist == self.allmotorm:
            return

        self.allmotorm = motlist

        #if not self.isServer():
            #return

        for motor in self.motorWidgets:
            if motor not in motlist:
                self.motorWidgets.pop(motor)

        for mne in motlist:
            if mne not in self.motorWidgets:
                #motor = MotorWidget(mne, "%s:%s" % (
                #        self.specConn.getHost(), self.specConn.getName()))
                motor = MotorWidget(mne, self.specConn.server_conn)
                self.motorWidgets[mne] = motor

        self.allmotorm = motlist
        self.serverPanel.setMotors(self.allmotorm)

    # server
    def setDataFile(self,filename):
        if filename:
            self.sendCommand("newfile %s" % filename)

    # both
    def getVariableData(self, varname):
        if self.specConn:
            return self.specConn.getVariableData(varname)
        else:
            return None

    # both
    def isSharedMemory(self):
        if self.specConn:
            return self.specConn.isSharedMemory()
        else:
            return False

    # both
    def isServer(self):
        return True
        if self.specConn:
            return self.specConn.isServerMode()
        else:
            return False

    # server
    def getMotorWidget(self, motmne):
        if motmne in self.motorWidgets:
            return self.motorWidgets[motmne]
        else:
            return None

    def sendCommand(self, cmdstr):
        self.specConn.sendCommand(cmdstr)

    def sendCommandA(self, cmdstr):
        self.specConn.sendCommandA(cmdstr)

    #
    # Handling data file.
    #

    # server
    def setFilename(self, filename):
        if filename and filename != self.filename:
            self.filename = filename
            self.filenameChanged.emit(self.filename)

    def getFileName(self):
        return self.filename

    def setFileName(self):
        """
          It should change filename in spec by using macro 'newfile'
          Internal variable will be changed on event on real change from spec
        """
        pass

    def pointSelection(self, xlabel, xpos):
        if self.isServer():
            self.serverPanel.setPointSelection(xlabel, xpos)

    def regionSelection(self, xlabel, x1, x2):
        if self.isServer():
            self.serverPanel.setRegionSelection(xlabel, x1, x2)

    def sendCommand(self, cmdstring):
        self.specConn.sendCommand(cmdstring)

    def abort(self):
        self.specConn.abort()

    def getMotorPosition(self, mne):
        return self.specConn.getMotorPosition(mne)

    def getHost(self):
        if self.specConn:
            return self.specConn.getHost()

    def getSpecName(self):
        if self.specConn:
            return self.specConn.getName()

    def getSpecVariable(self):
        if self.specConn:
            return self.specConn.getVariable()

class SpecDataChild(SpecDataSource):

    def __init__(self, app, filtername):
        super(SpecDataChild, self).__init__(app.parent, app.getSpecName(), app.getSpecVariable(), filtername)
        self.closeSplitter()

    def checkChildren(self):
        # children do not need to check for children
        pass

    def checkRaise(self, endscan=False):
        # children do not need to check whether to raise or not
        pass

    def updateMenubar(self):

        # TODO.  Show menubar in detached windows
        return 

        menubar = self.menubar
        menubar.clear()

        menubar.addMenu(self.fileMenuDetached)
        menubar.addMenu(self.plotMenu)

        self.plotMenu.setDisabled(False)
        self.updateSpecMenu()

    def openSplitter(self):
        pass

    def attachWhenClosing(self):
        return False


def test_me():
    print("testing me")

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:
        print("Usage: %s spec" % sys.argv[0])
        sys.exit(0)

    test_me()
