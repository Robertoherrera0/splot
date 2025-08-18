#******************************************************************************
#
#  @(#)SpecDataConnection.py	3.18  07/21/21 CSS
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

import sys
import time
import copy
import weakref
import numpy as np

from pyspec.css_logger import log, log_exception
from pyspec.utils import is_remote_host

from Constants import *

jsonok = False
try:
    import json
    jsonok = True
except ImportError:
    pass

if not jsonok:
    try:
        import simplejson as json
        jsonok = True
    except ImportError:
        log.log(2,
            "Cannot find json module. Only basic functionality will be provided")
        log.log(2,
            "Hint: Install json or simplejson python module in your system")

from pyspec.client.SpecConnection import QSpecConnection
from pyspec.client.SpecConnection import UPDATEVALUE, FIREEVENT

from pyspec.client.SpecCommand import SpecCommandA
from pyspec.client.SpecVariable import SpecVariable

try:
    from pyspec.client import spec_shm
    no_sharedmem = False
except ImportError:
    log.log(2, "cannot import spec_shm. shared memory not available") 
    no_sharedmem = True

from DataArrayInfo import DataArrayInfo

class SpecDataConnection(object):

    scand_var = "SCAN_D"
    point_var = "SCAN_PT"
    metadata_var = "SCAN_META"
    plotconfig_var = "SCAN_PLOTCONFIG"
    scan_status_var = "SCAN_STATUS"
    columns_var = "SCAN_COLS"
    ldt_var = "LDT"
    plotselect_var = "PLOT_SEL"
    hkl_var = "_hkl_col"

    def __init__(self, specapp, ignore_ports=None):

        self.connected = False
        self.conn_pending = True

        self.source = None

        self.host = None
        self.specname = None

        self.server_conn = None
        self.server_conn_ready = False

        self.shm_conn = None
        self.shm_conn_ready = False

        self.data = None
        self.info = None
        self.metadata = {}
        self.filename = None

        self.npts = 0
        self.status = "idle"
        self.columns = []
        self.slice_atpoint = None

        self.shmmeta_updated = True
        self.shmdata_updated = True

        self.arrayinfo = None

        self.plotconf = None

        # server
        self.hkl_columns = None

        # decide when do we have enough info for first scan (server mode)
        self.ptno = 0
        self.data_channel = None
        self.var_channels = {}

        self._oldmetadata = None
        self._oldcolumns = None
        self._oldstatus = None

        self.info_completed = False
        self.got_columns = False
        self.got_metadata = False
        self.got_plotselect = False
        self.got_status = False
        self.got_lastpoint = False

        self.motors_followed = {}
        self.followed_motor = None

        self.is_closed = False

        self.array_info = None

        self.ignore_ports = ignore_ports
        self.connect(specapp)

    def connect(self, spec_app):
        """ Connect parameters is a string with the format [host:]specname """

        if no_sharedmem:
            log.log(1,
                "Shared memory functionality not available. Trying to connect via server to localhost")

        self.variable = self.scand_var

        if not spec_app:
            log.log(1,"No specname provided.")
            return

        self._connectToServer(spec_app)

        if self.server_conn:
            self.specname = self.server_conn.get_specname()
            self.shm_conn = self._checkConnectToSHM(self.specname)

        self.checkRemote()
            
        if self.server_conn or self.shm_conn:
            self.connected = True

    def set_source(self,source):
        self.source = source
        if self.server_conn_ready:
            self.source.server_connected()

    # server
    def disconnect(self):
        if self.server_conn:
            self.server_conn.disconnect()

    # server
    def is_remote(self):
        return self.is_remote_host

    def checkRemote(self):
        self.is_remote_host = is_remote_host(self.host)

    # shm
    def _checkConnectToSHM(self, specname):

        if no_sharedmem:
            return False

        if self.variable not in spec_shm.getarraylist(specname):
            return False

        arrinfo = spec_shm.getarrayinfo(specname, self.variable)
        self.arrayinfo = DataArrayInfo( spec_shm.getarrayinfo(specname, self.variable) )
    
        self.shm_conn_ready = True
        return True

    # shm
    def checkConnection(self):
        self.shm_conn = self._checkConnectToSHM(self.specname)
        return self.shm_conn_ready or self.server_conn_ready

    # both
    def isImage(self):
        if not self.arrayinfo: 
            return False

        return self.arrayinfo.isImage()

    # both
    def getMaxPoints(self):
        return self.arrayinfo.getNbRows()

    # both
    def isConnected(self):
        return self.shm_conn or self.server_conn

    # both
    def isSharedMemory(self):
        return self.shm_conn

    # both
    def isServerMode(self):
        return self.server_conn_ready

    # both
    def getVariable(self):
        return self.variable

    # both
    def getName(self):
        return self.specname

    # both
    def getHost(self):
        return self.host

    # both
    def getStatus(self):
        return self.status

    # both
    def getDataColumns(self):
        return self.columns

    # both
    def getLastPointNo(self):
        return self.npts + 1

    # both
    def updateData(self):
        if self.shm_conn_ready:
            if self.shmdata_updated:
                self.updateDataSHM()
        elif self.server_conn_ready:
            self.updateDataServer()

    def get_data_variable(self, varname):
        # this is the code to get data from variables other
        # than scan data. In fact we should try, when creating those
        # variables to check if it is possible to create an shm connection
        # to them so that we can be more efficient:
        #    - data updated only if spec says it has been updated
        #    - transfer of data through shm and not socket
        metadata = None
        if self.shm_conn_ready:
            data = np.array(spec_shm.getdata(self.specname, varname))
            metadata = spec_shm.getmetadata(self.specname, varname)
            if metadata:
                metadata = json.loads(metadata)
        elif self.server_conn_ready:
            if varname not in self.var_channels:
                var_channel = SpecVariable(self.server_conn, varname)
            else:
                var_channel = self.var_channels[var_channel]

            data = var_channel.getValue()

        # Make it column wise if we have only one row
        if data.any() and data.shape[0] == 1:  
            data = data.transpose()

        return data, metadata

    def getData(self, noinfo=False):

        # By default all arrays are bidimensional. With the second dimension index referring
        # to column number.  Row wise, col wise operation are not supported for now.
        # Still for one dimensional arrays special treatment is necessary.

        self.updateData()

        if self.data.any():
            if self.data.shape[0] == 1:  # Make it column wise if we have only one row
                self.data = self.data.transpose()

            if self.isImage():
                return self.data

        if noinfo:
            if self.data.any():
                # index of lastpoint that was not zero
                self.npts = self.data[:, 0].nonzero()[0][-1] 
            else:
                self.npts = 0
            self.metadata = {}

        try:
            return self.data[:self.npts + 1]
        except:
            return self.data

    # shm 
    def getDataPoint(self, ptidx):
        if self.shm_conn_ready:
            return self.getDataPointSHM(ptidx)
        else:
            log.log(1,"Wrong connection mode")
            return []

    # both
    def getFilePath(self):
        return self.getMeta("datapath")

    # both
    def getScanNumber(self):
        return self.getMeta("scanno")

    # both
    def getMeta(self, keyw):

        if self.shm_conn_ready:
            if self.shmmeta_updated:
                self.updateMeta()

        try:
            return self.metadata[keyw]
        except TypeError:
            return ""
        except KeyError:
            return ""
        except AttributeError:
            return ""

    # shm
    def hasNewData(self, variable=None):
        if self.shm_conn_ready:
            if spec_shm.is_updated(self.specname, self.variable, self.source.getSourceName()):
                self.shmmeta_updated = True
                return True
            else:
                return False

    # shm
    def updateMeta(self):

        if not jsonok:
            return

        _meta = spec_shm.getmetadata(self.specname, self.variable)

        self._mcols = []

        if (_meta.strip()):
            uncoded_meta = json.loads(_meta)

            if type(uncoded_meta) is list:

                if len(uncoded_meta) >= 2:
                    self._mcols = uncoded_meta[0]
                    self.metadata = uncoded_meta[1]

                if len(uncoded_meta) >= 3:
                    plotconfig = uncoded_meta[2]
                    if plotconfig != self.plotconf:
                        self.source.updatePlotConfig(plotconfig)
                        self.plotconf = copy.copy(plotconfig)

            elif type(uncoded_meta) is dict:
                self.metadata = uncoded_meta
            else:
                log.log(3," cannot decode metadata")

            self.shmmeta_updated = False
            self.source.updateMeta()

    # shm
    def updateDataSHM(self):
        self.data = np.array(spec_shm.getdata(self.specname, self.variable))

    # shm
    def getDataPointSHM(self, ptidx):
        if self.data.shape[1] == 1:
            return np.array(spec_shm.getdatacol(self.specname, self.variable, ptidx))
        else:
            return np.array(spec_shm.getdatarow(self.specname, self.variable, ptidx))

    # shm 
    def updateInfo(self):

        if not jsonok:
            return False

        if self.shmmeta_updated:
            self.updateMeta()

        _jinfo = spec_shm.getinfo(self.specname, self.variable).strip()

        infoOk = False

        self.columns = []

        if _jinfo:
            try:
                uncoded_info = json.loads(_jinfo)
                if type(uncoded_info) is list:
                    if len(uncoded_info) >= 3:
                        _npts,_status = uncoded_info[0:2]
                        _g3 = uncoded_info[2]  # mesh slice size
                        _cols = self._mcols
                        if _g3 != self.slice_atpoint:
                            self.meshSliceStarted(_g3)
                            
                self.npts = int(_npts)
                self.status = _status
                for idx in range(len(_cols)):
                    self.columns.append(_cols[str(idx)])
                infoOk = True
            except:
                import traceback
                log.log(3,"cannot decode info.  %s " % traceback.format_exc())

        return infoOk

    # shm
    def getSHMVariableList(self):
        if no_sharedmem:
            return []
        else:
            varlist = spec_shm.getarraylist(self.specname)
            return varlist

    # server
    def _connectToServer(self, specapp):
        try:
            log.log(2, "CONNECTING to %s" % specapp)
            self.server_conn = QSpecConnection(specapp)
            self.server_conn.set_ignore_ports(self.ignore_ports)
            self.server_conn.connect_event('connected', self.server_connected)
            self.server_conn.connect_event('disconnected', self.server_disconnected)
            self.server_conn.run()
        except:
            import traceback
            log.log(2, traceback.format_exc())

    def is_server_connected(self):
        return self.server_conn_ready

    def get_host(self):
        if self.server_conn:
            return self.server_conn.get_host()

    def get_specname(self):
        if self.server_conn:
            return self.server_conn.get_specname()

    def update_events(self):
        self.server_conn.update_events()
        #self.server_conn._update()

    def close_connection(self):
        if self.server_conn is not None: 
            self.server_conn.close_connection()

        return True

    # server
    def server_connected(self):
        try:
            log.log(2, "spec %s server conected" % self.specname)

            self.server_conn_ready = True
            self.conn_pending = True

            self.server_conn.registerChannel('status/ready', self.statusReady,
                                             dispatchMode=UPDATEVALUE)
            self.server_conn.registerChannel('status/shell', self.statusShell,
                                             dispatchMode=UPDATEVALUE)

            host = self.host is None and "localhost" or self.host
    
            self.conn_vars = [
                    [self.columns_var, self.columnsChanged, UPDATEVALUE, False],
                    [self.metadata_var, self.metadataChanged, UPDATEVALUE, False],
                    [self.plotconfig_var, self.plotconfigChanged,
                        UPDATEVALUE, False],
                    [self.scan_status_var, self.statusChanged, FIREEVENT, False],
                    [self.point_var, self.gotScanPoint, FIREEVENT, False],
            ]

            log.log(2, " creating data channel")
            self.data_channel = SpecVariable( self.server_conn, self.scand_var )

            if self.conn_pending:
                self.checkVariables()
    
            if self.source:
                self.source.server_connected()

        except:
            log_exception()

    # server
    def server_disconnected(self):
        self.server_conn_ready = False
        self.source.server_disconnected()

    # server
    def server_close(self):
        if self.server_conn_ready:
            self.is_closed = True

    # server
    def checkVariables(self):
        self.connect_vars()
        self.conn_pending = False

    # server
    def connect_vars(self):
        for varinfo in self.conn_vars:
            varname, varcb, varupdmode, varstat = varinfo
            if not varstat:
                try:
                    self.server_conn.register(
                        'var/%s' % varname,    varcb, dispatchMode=varupdmode)
                    varinfo[3] = True
                except:
                    import traceback
                    logmsg = traceback.format_exc()
                    log.log(1,"Cannot register with variable %s." %
                           varname)
                    log.log(1,logmsg)
                    self.conn_pending = True
                    varinfo[3] = False
                    break
            else:
                pass

    def getVariableData(self, varname):
        if varname in spec_shm.getarraylist(self.specname):
            data = np.array(spec_shm.getdata(self.specname, varname))
        elif self.server_conn_ready:
            data = SpecVariable(self.server_conn, varname)

        # do stuff with the data
        sh = data.shape
        if len(sh) == 1:
            return data
        elif sh[0] == 1:
            data = data.reshape((sh[1],sh[0])) # change direction on 1D vector 

        return data

    # server
    def updateDataServer(self, variable=None):
        if self.data_channel:
            self.npts = self.server_conn.read_channel(self.ldt_var)
            self.data = self.data_channel.getValue()

    # server
    def getMotorPosition(self, mne):
        if not self.server_conn_ready:
            return

        try:
            motpos = self.server_conn.get_position(mne)
            return motpos
        except:
            return None

    # server
    def followMotor(self, mne):

        if not self.server_conn_ready:
            return

        channel_name = 'motor/%s/position' % mne
        self.server_conn.registerChannel(channel_name, self.scanMotorPositionChanged,
                                         dispatchMode=FIREEVENT)
        self.followed_motor = mne
        self.motors_followed[mne] = True

    # server
    def unfollowMotor(self, mne):
        if not self.server_conn_ready:
            return

        if mne in self.motors_followed and self.motors_followed[mne] == True:
            channel_name = 'motor/%s/position' % mne
            self.motors_followed[mne] = False

    # server
    def scanMotorPositionChanged(self, position):
        if self.is_closed:
            return

        self.source.scanMotorPositionChanged(self.followed_motor, position)

    # server
    def getHKLColumns(self):
        if not self.server_conn_ready:
            return -1

        try:
            if self.hkl_columns == None:
                self.hkl_columns = self.server_conn.read_channel(self.hkl_var)
            return self.hkl_columns
        except:
            return -1
             

    # server
    def metadataChanged(self, metadata):

        if self.shm_conn_ready or self.is_closed:
            return

        try:
            self.got_metadata = True
            if self._oldmetadata == metadata:
                return

            self._oldmetadata = metadata
            self.metadata = metadata

            self.source.updateMeta()

            if not self.info_completed:
                self.checkInfo()
        except Exception as e:
            import traceback
            log.log(2, traceback.format_exc())

    # server
    def plotconfigChanged(self, plotconfig):
        
        if self.shm_conn_ready or self.is_closed:
            return

        if plotconfig != self.plotconf:
            self.source.updatePlotConfig(plotconfig)
            self.plotconf = copy.copy(plotconfig)

    # server
    def columnsChanged(self, columns):

        if self.shm_conn_ready or self.is_closed:
            return

        if self._oldcolumns == columns:
            return

        self._oldcolumns = copy.copy(columns)

        self.got_columns = True

        self.columns = [0, ] * len(columns)
        for i in columns:
            try:
                self.columns[int(i)] = columns[i]
            except:
                import traceback
                log.log(3,"Problem with columns variable")
                log.log(3, traceback.format_exc())
                return

        if not self.info_completed:
            self.checkInfo()

        self.source.setColumnNames(self.columns)

    # server
    def statusChanged(self, newstatus):
        if self.shm_conn_ready or self.is_closed:
            return

        self.got_status = True
        if self._oldstatus == newstatus:
            return

        self._oldstatus = newstatus
        self.source.statusChanged(newstatus)

        if not self.info_completed:
            self.checkInfo()

    # server
    def gotScanPoint(self, pointval):

        if self.shm_conn_ready or self.is_closed:
            return

        self.ptno += 1

        if not jsonok:
            return

        try:
            pointval = json.loads(pointval)
            if len(pointval) >= 2:
                pointno, point = pointval[0:2]

            if len(pointval) >= 3:
                _g3 = pointval[2]
                if _g3 != self.slice_atpoint:
                    self.meshSliceStarted(_g3)
 
            self.source.addScanPoint(pointno+self.slice_atpoint, point)
        except:
            import traceback
            log.log(1, "Cannot decode scan point %s" % pointval)
            log.log(2, traceback.format_exc())
            return

        self.got_lastpoint = True
        if not self.info_completed:
            self.checkInfo()

    # both
    def meshSliceStarted(self, atpoint):
        self.slice_atpoint = atpoint
        self.source.meshSliceStarted(atpoint)   

    # server
    def statusReady(self, newstatus):
        if self.is_closed:
            return

        self.source.statusReady(newstatus)

        if self.conn_pending:
            self.checkVariables()

    # server
    def statusShell(self, newstatus):
        if self.is_closed:
            return

        self.source.statusShell(newstatus)

    # server
    def checkInfo(self):
        #                      self.got_plotselect  and
        self.info_completed = self.got_columns     and \
            self.got_metadata    and \
            self.got_status      and \
            self.got_lastpoint

        if self.info_completed:
            self.source.newScan()

    # server
    def abort(self):
        if not self.server_conn_ready:
            return

        self.server_conn.abort()

    # server
    def sendCommand(self, cmdstring):
        log.log(2, "running command %s" % cmdstring)
        if self.is_server_connected():
            answer = self.server_conn.run_cmd(cmdstring)
            log.log(2, "answer to command %s is %s" % (cmdstring,answer))
            return answer
        else:
            log.log(2, "cannot run command. server is not connected")
            return None

    # server
    def sendCommandA(self, cmdstring):
        
        if not self.server_conn_ready:
            return

        try:
            cmd = SpecCommandA(self.server_conn, cmdstring)
            cmd()
        except:
            import traceback
            log.log(2, traceback.format_exc())

def main(spec, host):

    import gevent

    specConn = SpecDataConnection(spec, host)
    ready = True
    log.log(1, "starting main")
    while True:
        gevent.wait(timeout=0.1, count=1)
        if ready != specConn.server_conn_ready:
            ready = specConn.server_conn_ready
            print(ready and "Connected" or "Disconnected")
            gevent.sleep(2)
            t0 = time.time()
            data = specConn.getVariableData('farr')
            print("Data read in %3.3f secs" % (time.time() -t0))

    print("   SHM: ", specConn.shm_conn)
    print("SERVER: ", specConn.server_conn_ready)
    print(specConn.getDataColumns())

if __name__ == "__main__":

    import sys

    log.start()

    if not (1 < len(sys.argv) < 4):
        print("Usage: %s spec [host]" % sys.argv[0])
        sys.exit(0)

    spec = sys.argv[1]

    if len(sys.argv) > 2:
        host = sys.argv[2]
    else:
        host = None

    main(spec, host)
