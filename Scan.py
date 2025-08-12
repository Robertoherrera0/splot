#******************************************************************************
#
#  @(#)Scan.py	3.5  10/30/20 CSS
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

#
# ScanTypes as defined in standard.mac
#

from pyspec.css_logger import log


# flags as defined in standard.mac

scanType_MotorScan  = 0x1      # motor scan
scanType_HKL_Scan   = 0x2      # hkl scan
scanType_TempScan   = 0x4      # temp scan
scanType_MeshScan   = 0x8      # mesh scan
scanType_TimeScan   = 0x10     # time scan
scanType_WithGeo    = 0x20     # motor scan includes a geo motor
scanType_Continuous = 0x40     # continuous scan (count while moving)
scanType_ScanActive = 0x80     # scanning active
                                        # don't use 0x0F00 bits for flags
scanType_FileScan   = 0x1000   # scan from motor positions in a file
scanType_Parametric = 0x2000   # scan with parameter such as radius or length
scanType_ArrayTimes = 0x4000   # take scan times from SCAN_TIMES[] for each point
scanType_EnergyScan = 0x8000   # energy scan
scanType_Multi      = 0x10000  # save multiple values in X_L2[]

# splot flags
scanType_Relative   = 0x100000 # relative position scans
scanType_Extended   = 0x200000 # x-type scans

class WrongScan(Exception):
    pass

class scan_parser(object):
    def __init__(self, cmdstr=None, args=None):

        self.motors = []
        self.ranges = {}
        self.ivals = 0

        self.slow_ivals = 0
        self.slow_positions = []

        self.params = {}
        self.scantime = None
        self.scantype = 0

        self.cmdstr = cmdstr

        if args is not None:
            self.nb_motors = int(args)
        else:
            self.nb_motors = 0
 
        if self.cmdstr:
            _parts = cmdstr.split()
            self.cmdname = _parts[0]
            self.cmdpars = _parts[1:]

            self._parse()

    def _parse(self):
        pass
 
    def getMotors(self):
        return self.motors

    def getMotorRange(self, motor):
        return self.ranges.get(motor,None)

    def getCommand(self):
        return self.cmdstr

    def getCommandName(self):
        return self.cmdname

    def getScanType(self):
        return self.scantype

    def isMotorScan(self):
        return (self.scantype & scanType_MotorScan) and True or False

    def isMesh(self):
        return (self.scantype & scanType_MeshScan) and True or False

    def isTimeScan(self):
        return (self.scantype & scanType_TimeScan) and True or False

    def isEnergyScan(self):
        return (self.scantype & scanType_EnergyScan) and True or False

class _mesh(scan_parser):
    def _parse(self):
        self.scantype = scanType_MeshScan | scanType_MotorScan

        _pars = self.cmdpars
        for motno in range(self.nb_motors):
            if len(_pars) > 4:
                mne, _start, _end, _ivals = _pars[:4]
                self.motors.append(mne)
                self.ranges[mne] = float(_start), float(_end)
                if motno == 0:
                     self.ivals = int(_ivals)
                elif motno == 1:
                     self.slow_ivals = int(_ivals)
                _pars = _pars[4:]       
            else:
                raise WrongScan("Wrong number of parameters for mesh")
         
        if len(_pars) != 1:
            raise WrongScan("Wrong number of parameters for mesh")

        self.scantime = _pars[0]
        self._calc_positions()

    def _calc_positions(self):
        slowmot = self.motors[1]

        mstart, mend = self.ranges[slowmot]
        idist = abs(mend-mstart) / self.slow_ivals
        posl = [mstart + idist*j for j in range(self.slow_ivals+1)]          
        self.slow_positions = posl

    def getSlowMotor(self):
        return self.motors[1]

    def getSlowMotorPositions(self):
        return self.slow_positions

class _dmesh(_mesh):
    def _parse(self):
        _mesh._parse(self)
        self.scantype |= scanType_Relative

class _cmesh(_mesh):
    def _parse(self):
        _pars = self.cmdpars

        log.log(3,"parsing cmesh /  %s " %  _pars)
        if len(_pars) >= 8:
            mne1, _start1, _end1, _stime = _pars[:4]
            _pars = _pars[4:]
            mne2, _start2, _end2, _ivals = _pars[:4]
            _pars = _pars[4:]
            self.motors = [mne1, mne2]
            self.ranges[mne1] = float(_start1), float(_end1)
            self.ranges[mne2] = float(_start2), float(_end2)
            self.slow_ivals = int(_ivals)
        else:
            raise WrongScan("Wrong number of parameters for cmesh1")

        log.log(3,"parsing cmesh2 /  %s " %  _pars)
        if len(_pars) == 1:
            self.sleeptime = float(_pars[0])
        elif len(_pars) == 2:
            self.sleeptime = float(_pars[1]) # this is because of wrong HEADING creation
        elif len(_pars) > 2:
            raise WrongScan("Wrong number of parameters for cmesh")
        else:
            self.sleeptime = 0

        self.scantype = scanType_MeshScan | scanType_MotorScan
        self.scantype |= scanType_Continuous

        self._calc_positions()

class _cdmesh(_cmesh):
    def _parse(self):
        _cmesh._parse(self)
        self.scantype |= scanType_Relative

class _ascan(scan_parser):
    def _parse(self):
        self.scantype = scanType_MotorScan

        _pars = self.cmdpars
        for motno in range(self.nb_motors):
            if len(_pars) > 3:
                mne, _start, _end = _pars[:3]
                self.motors.append(mne)
                self.ranges[mne] = float(_start), float(_end)
                _pars = _pars[3:]       
            else:
                raise WrongScan("Wrong number of parameters for scan")
         
        if len(_pars) != 2:
            raise WrongScan("Wrong number of parameters for scan")

        _ivals = _pars[0]
        self.ivals = int(_ivals)
        self.scantime = _pars[1]

class _dscan(_ascan):
    def _parse(self):
        _ascan._parse(self)
        self.scantype |= scanType_Relative

class _cscan(scan_parser):
    def _parse(self):
        self.scantype = scanType_MotorScan | scanType_Continuous

        _pars = self.cmdpars
        for motno in range(self.nb_motors):
            if len(_pars) > 3:
                mne, _start, _end  = _pars[:3]
                self.motors.append(mne)
                self.ranges[mne] = float(_start), float(_end)
                _pars = _pars[3:]       
            else:
                raise WrongScan("Wrong number of parameters for cscan")
         
        if len(_pars) == 0 or len(_pars) > 2:
            raise WrongScan("Wrong number of parameters for cscan")

        self.scantime = _pars[0]
        if len(_pars) == 2:
            self.sleeptime = _pars[1]

class _cdscan(_cscan):
    def _parse(self):
        _cscan._parse(self)
        self.scantype |= scanType_Relative

class _xascan(_ascan):
    def _parse(self):
        self.scantype = scanType_MotorScan

        _pars = self.cmdpars
        for motno in range(self.nb_motors):
            if len(_pars) > 3:
                mne, _start, _end = _pars[:3]
                self.motors.append(mne)
                self.ranges[mne] = float(_start), float(_end)
                _pars = _pars[3:]       
            else:
                raise WrongScan("Wrong number of parameters for xascan")
         
        if len(_pars) == 0:
            raise WrongScan("Wrong number of parameters for xascan")

        self.scantime = _pars[0]
        if len(_pars) > 1:
            self.params['expansion'] = _pars[1]
        if len(_pars) > 2:
            self.params['ratio'] = _pars[2]

class _xdscan(_xascan):
    def _parse(self):
        _xascan._parse(self)
        self.scantype |= scanType_Relative

class _rscan(_ascan):
    def _parse(self):
        self.scantype = scanType_MotorScan 

        _pars = self.cmdpars
        for motno in range(self.nb_motors):
            if len(_pars) > 3:
                mne, _start, _end = _pars[:3]
                self.motors.append(mne)
                self.ranges[mne] = float(_start), float(_end)
                _pars = _pars[3:]       
            else:
                raise WrongScan("Wrong number of parameters for rscan")
         
        if len(_pars) == 0:
            raise WrongScan("Wrong number of parameters for rscan")

        self.scantime = _pars[0]
        if len(_pars) > 1:
            self.params['expansion'] = _pars[1]
        if len(_pars) > 2:
            self.params['ratio'] = _pars[2]

class _vscan(scan_parser):
    def _parse(self):
        self.scantype = scanType_MotorScan 

class _fscan(scan_parser):
    def _parse(self):
        self.scantype = scanType_FileScan 

class _hklscan(scan_parser):
    def _parse(self):
        self.scantype = scanType_HKL_Scan  

class _hkscan(_hklscan):
    def _parse(self):
        self.scantype = scanType_HKL_Scan  

class _hscan(_hklscan):
    def _parse(self):
        self.scantype = scanType_HKL_Scan  

class _kscan(_hklscan):
    def _parse(self):
        self.scantype = scanType_HKL_Scan  

class _lscan(_hklscan):
    def _parse(self):
        self.scantype = scanType_HKL_Scan  

class _hklmesh(_mesh):
    def _parse(self):
        _mesh._parse(self)
        self.scantype = scanType_MeshScan | scanType_HKL_Scan  

class _hkmesh(_hklmesh):
    def _parse(self):
        self.scantype = scanType_MeshScan | scanType_HKL_Scan  

class _timescan(scan_parser):
    def _parse(self):
        self.scantype = scanType_TimeScan 

class _loopscan(_timescan):
    def _parse(self):
        _timescan._parse(self)

class _tscan(scan_parser):
    def _parser(self):
        self.scantype = scanType_TempScan

class _escan(scan_parser):
    def _parser(self):
        self.scantype = scanType_EnergyScan

#
# Known scan commands
#


_parsers = {
   "ascan":  (_ascan, 1),
   "a2scan":  (_ascan, 2),
   "a3scan":  (_ascan, 3),
   "a4scan":  (_ascan, 4),
   "a5scan":  (_ascan, 5),
   "dscan":  (_dscan, 1),
   "d2scan":  (_dscan, 2),
   "d3scan":  (_dscan, 3),
   "d4scan":  (_dscan, 4),
   "d5scan":  (_dscan, 5),
   "cscan":  (_cscan, 1),
   "c2scan": (_cscan, 2),
   "c3scan": (_cscan, 3),
   "c4scan": (_cscan, 4),
   "cdscan": (_cdscan, 1),
   "cd2scan": (_cdscan, 2),
   "cd3scan": (_cdscan, 3),
   "cd4scan": (_cdscan, 4),
   "xascan": (_xascan, 1),
   "xa2scan": (_xascan, 2),
   "xa3scan": (_xascan, 3),
   "xa4scan": (_xascan, 4),
   "xdscan": (_xdscan, 1),
   "xd2scan": (_xdscan, 2),
   "xd3scan": (_xdscan, 3),
   "xa4scan": (_xdscan, 4),
   "rscan": (_rscan, 1),
   "lup": (_ascan, 1),
   "vscan": (_vscan, 1),
   "v2scan": (_vscan, 2),
   "mesh": (_mesh, 2),
   "dmesh": (_dmesh, 2),
   "cmesh": (_cmesh, 2),
   "cdmesh": (_cdmesh, 2),
   "hklscan": (_hklscan, 3),
   "hkscan": (_hkscan, 2),
   "hscan": (_hscan, 1),
   "kscan": (_kscan, 1),
   "lscan": (_lscan, 1),
   "hklmesh": (_hklmesh, 2),
   "hkmesh": (_hkmesh, 2),
   "timescan": (_timescan, None),
   "loopscan": (_loopscan, None),
   "tscan": (_tscan, None),
   "dtscan": (_tscan, None),
   "Escan": (_escan, None),
   "fscan": (_fscan, None),
}

def _Scan(cmdstr):
    if not cmdstr:    
        return scan_parser()

    cmdparts = cmdstr.split()
    cmd_name = cmdparts[0]

    if cmd_name not in _parsers: 
        return scan_parser()
    else:
        _parser, _args = _parsers[cmd_name]
        try:
            return _parser(cmdstr, _args)
        except WrongScan:
            raise WrongScan("Error parsing scan")
            return None

class Scan(object):

    def __init__(self, cmdstr=None):
        # 
        self._scan = _Scan(cmdstr)

    def __nonzero__(self):
        return (self._scan is not None)

    def getScanType(self):
        return self.scantype

    def getMotorRange(self, mne):
        return self._scan.getMotorRange(mne)

    def getSlowMotor(self):
        return self._scan.getSlowMotor()

    def getSlowMotorPositions(self):
        if not self.isMesh():
            return None

        return self._scan.getSlowMotorPositions()
 
    def getCommand(self):
        return self._scan.getCommand()

    def getMotors(self):
        return self._scan.getMotors()

    def isTimeScan(self):
        return self._scan.isTimeScan()

    def isMesh(self):
        return self._scan.isMesh()

def test():
    cmdstr = "cmesh th 9 10 1 chi 9 10 5 0.1"
    cmdstr = "hklmesh H 9 10 1 L 9 10 5 0.1"
    scanobj = Scan(cmdstr)
    print( scanobj.isMesh() )
    print( scanobj.getSlowMotorPositions())

def testfile():
    from pyspec.file.spec import FileSpec 
    sf = FileSpec("data/31oct98.dat")
    for scan in sf:
        scanobj = Scan(scan.getCommand()) 
        print( scanobj.getCommand()),
        print( scanobj.isMesh() ),
        print( scanobj.getMotors() ),
        print( scanobj.getMotorRange("tx3") )

if __name__ == '__main__':
    test()
