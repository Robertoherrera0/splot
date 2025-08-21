#!/usr/bin/env python

#******************************************************************************
#
#  @(#)splot.py	3.25  01/12/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2019,2020,2021,2023,2024
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
import os
import time
import getopt
import signal
import logging
import platform
import struct
import threading

# set pypsec path  
SPECD=os.getenv("SPECD", "/usr/local/lib/spec.d")
sys.path.insert(0, "..")
sys.path.append(SPECD)

try:
    from pyspec.graphics.QVariant import *
    from pyspec.graphics import qt_variant
except:
    sys.exit(0)

from pyspec.utils import is_windows, is_macos
from Preferences import Preferences

try:
   from xraise import xraise_id
except ImportError:
   def xraise_id(*args):
       pass

# logging and messages
import warnings
warnings.simplefilter("ignore")

from pyspec.css_logger import log, addFileHandler, addStdOutHandler
from pyspec.client.SpecServer import SpecServer
from pyspec.client.spec_updater import spec_updater
from pyspec.utils import async_loop
#from pyspec.utils import async_loop, is_centos8

from allio_redirector import allio_redirector

loglevels = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}
# logging and messages end


global win
global win_id
win=None

# possible running threads
global cmdsrv
global watcher

cmdsrv=None
watcher=None

win=None
win_id=None

Preferences.ignoreraise = False

from VERSION import getFullVersion

from Constants import *

#if is_centos8():
    # from pyspec.graphics.QVariant import check
    # print( check(fix_wayland=True) )
#    pass

#def fix_wayland_warning():
    #xdg_session = os.getenv('XDG_SESSION_TYPE', None)
    #xdg_desktop = os.getenv('XDG_SESSION_DESKTOP', None)
#
    #if xdg_session == 'wayland' and xdg_desktop == 'gnome':
        #os.environ['XDG_SESSION_TYPE'] = 'x11'

class watchdog(threading.Thread):
    def __init__(self, pid, *args):
        self.pid = pid
        self.stop_it = False
        threading.Thread.__init__(self, *args)
        self.daemon = True # will concede to quit on app control-C

    def request_stop(self):
        self.stop_it = True

    def run(self):
        while True:
            if not pid_runs(self.pid):
                log.log(2, "watchdog lost sight of parent process. Bye")
                # send control-c like signal to main thread
                import _thread
                _thread.interrupt_main()
                break

            if self.stop_it:
                break

            time.sleep(0.02)

def pid_runs(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

class CaptureApplication(QApplication):

    def __init__(self, winname, *args):
        self.take_focus = 0
        self.winname = winname
        # fix_wayland_warning()
        QApplication.__init__(self, *args)

    def x11EventFilter(self, event):
        import event_types

        if Preferences.ignoreraise:
            return False

        if os.environ.get("DESKTOP_SESSION", None) in ["ubuntu", "ubuntu-2d"]:
            return False

        # from Xlib.h
        # typedef struct {
        #    int type;
        #    unsigned long serial;   /* # of last request processed by server */
        #    Bool send_event;        /* true if this came from a SendEvent request */
        #    Display *display;/* Display the event was read from */
        #    Window window;  /* window on which event was requested in event mask */
        #} XAnyEvent;

        # for unpack
        #  i - int
        #  L - unsigned long
        #  Q - unsigned long long

        is64bit = (sys.maxsize > 2**32)
        if is64bit:
            # display is a pointer - unsigned long long in 64 bit
            estr = event.asstring(40)
            etype, serial, sende, dpy, wind = struck.unpack("iLiQL", estr)
        else:
            estr = event.asstring(20)
            etype, serial, sende, dpy, wind = struck.unpack("iLiLL", estr)

        if etype == event_types.ButtonPress:
            self.take_focus = 1
        elif etype == event_types.KeyPress:
            self.take_focus = 1
        elif etype == event_types.LeaveNotify:
            self.take_focus = 0
        elif etype == event_types.EnterNotify:
            self.take_focus = 1

        if etype == event_types.ButtonPress or etype == event_types.KeyPress or \
                etype == event_types.LeaveNotify or etype == event_types.EnterNotify \
                or etype == event_types.FocusIn:
            #xraise(self.winname, self.take_focus, serial, win)
            xraise_id(win_id, self.take_focus, wind)
            pass

        return False

def appQuit(qt_end=False):
    global cmdsrv
    global watcher
    global win

    try:
        if watcher is not None:
            watcher.request_stop()

        # allow threads to go through their loop and finish
        time.sleep(0.05)
    
        if win:
            win.savePreferences()
            win.closeConnections()
            win = None
    except:
        import traceback
        log.log(2, traceback.format_exc())

    log.log(2, "bye")
    sys.exit(0)

def sig_handler(*args):
    """ Signal handler for SIGINT and SIGTERM signals """
    appQuit()

def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.
    
    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    try:
       from cStringIO import StringIO
    except ImportError:
       from io import StringIO
    import time
    import traceback

    import VERSION

    separator = '-' * 80
    notice = \
        """An unhandled exception occurred. If you wish you can report the problem\n"""\
        """via email to <%s>.\n\n"""\
        """Error information:\n""" % \
        ("splot_support@txolutions.com", )
    versionInfo=VERSION.getFullVersion()
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")
    
    tbinfofile = StringIO()
    try:
        traceback.print_tb(tracebackobj, None, tbinfofile)
        tbinfofile.seek(0)
        tbinfo = tbinfofile.read()
        errmsg = '%s: \n%s' % (str(excType), str(excValue))
        sections = [separator, timeString, separator, errmsg, separator, tbinfo]
        msg = '\n'.join(sections)

        logmsg = str(notice)+str(msg)+str(versionInfo)
        log.log(logging.CRITICAL, logmsg)
    except:
        pass

def get_system_info():
    if is_macos():
        sysinfo = "macos: %s" % str(platform.mac_ver())
    else: # linux
        try:
            import distro
            sysinfo = "linux: %s" % str(distro.linux_distribution())
        except ImportError:
            try:
                sysinfo = "linux: %s" % str(platform.dist())
            except AttributeError:  # python 3.9 without distro module
                u = platform.uname()
                sysinfo = "linux: %s (%s)" % (u.node, u.version)

    return sysinfo

def log_app_info():
    vers_info =  getFullVersion()
    lib_info = app_libraries()

    log.log(2,"")     
    log.log(2,"Starting splot. version is: %s" % vers_info)
    log.log(2,"     Running on %s" % get_system_info())
    log.log(2,"     Using: ")
    log.log(2,"         python: %s" % lib_info['python'])
    log.log(2,"         qt: %s" % lib_info['qt'])
    log.log(2,"         graphics: %s" % lib_info['graphics'])
    log.log(2,"         pyspec: %s" % lib_info['pyspec'])

if is_macos():
    global last_time_repaint 
    last_time_repaint = time.time()

def update_cmdserver():
    global cmdsrv

    if cmdsrv is not None:
        cmdsrv._update() 

    if is_macos():
        # fix for bug in macos if no focus on windows
        #   forcing a repaint solves the issue.  After 10 seconds is enough
        global last_time_repaint
        if (time.time() - last_time_repaint) > 10.0:  
            win.repaint()
            last_time_repaint = time.time()


def main(mode, connectpars, varname, filename, scanno, cmdserver, servkey, winname):

    from SPlotMain import SPlotMain

    global win
    global win_id

    global cmdsrv
    global watcher

    log_app_info()

    try:
        # create a thread to call async_loop on all socket objects
        # both SpecConnections and SpecServer
        # and even before the application is running
        updater = spec_updater()
        updater.start()

        app = CaptureApplication(winname, ['splot'])

        splash_pix = QPixmap('splash.png')
        flag = Qt.WindowStaysOnTopHint 
        splash = QSplashScreen(splash_pix, flag)
        splash.setMask(splash_pix.mask())
        splash.show()
        time.sleep(0.1)
        app.processEvents()

        prefs = Preferences()
        prefs.load()

        """ To allow signal handler to work with Qt in any condition (dialogs, focus...)
           we give a call to a dummy function so that Qt gets out of the loop regularly """
        timer = QTimer()
        timer.timeout.connect(update_cmdserver)
        timer.start(CMDSERVER_INTERVAL)

        signal.signal(signal.SIGTERM, sig_handler)
        signal.signal(signal.SIGINT, sig_handler)

        # command server
        if cmdserver:
            #
            # watchdog if cmdsrv is provided in command line
            #    example:    -C  vicente_13001  (13001 being parent pid)
            parent_link = False
            mat = re.match(r"(?P<name>\w+)\_(?P<pid>\d+)", servkey)
            if mat:
                ppid = int(mat.group('pid'))
                if pid_runs(ppid):
                    log.log(1,"starting watchdog on parent process with pid=%d" % ppid)
                    watcher = watchdog(ppid)
                    watcher.start()
                    parent_link=True

            cmdsrv = SpecServer(name=servkey, allow_name_change=False, auto_update=False)
        else:
            # do not start if -C not in command line. only use saved key if present
            servkey = prefs.getValue("cmd_server")
            if not servkey:
                servkey = "splot_%s" % os.getpid()
            cmdsrv = SpecServer(name=servkey, auto_update=False)

        # main splot window
        win = SPlotMain(winname)
        win.set_command_server(cmdsrv)
        win_id = win.winId()

        if prefs["geometry"]:
            x, y, width, height = map(int, prefs["geometry"].split(","))
        else:
            x, y, width, height = 200, 100, 1000, 600
        win.setGeometry(x, y, width, height)
        win.show()

        if mode == "fileonly":
            win.openFile(filename, fromSpec=False)
            if scanno is not None:
                win.selectScan(scanno)
        elif connectpars:
            win.connectToSpec(connectpars, varname, check_datafile=True)

        APP_RUNNING = 1
        splash.finish(win)
        app.processEvents()

        while APP_RUNNING:
            if qt_variant() in ["PyQt6", "PySide6"]:
                exec_ = getattr(app, "exec")
            else:
                exec_ = getattr(app, "exec_") 
            exit_code = exec_()

            log.log(2,"Qt loop ended")
            appQuit(qt_end=True)
    except Exception:
        log.log(2,"an exception occurred")
        import traceback
        log.log(1,traceback.format_exc())
    #except SystemExit:
        #log.log(2,"system exit")

    #appQuit(qt_end=False)

def chooseWindowName(filename, specparts):
    root = "splot for spec"

    if filename:
        base = os.path.basename(filename)
        winname = "%s (%s)" % (root, base)
    elif specparts:
        bases = specparts.split(":")
        if len(bases) == 1:
            base = bases[0]
        else:
            base = bases[1]
        winname = "%s (%s)" % (root, base)
    else:
        winname = root

    return winname


def printVersion():
    import VERSION
    print(VERSION.getFullVersion())

def printUsage(progname):
    print( """
%(progname)s [ options ] [ [hostname:]spec [varname] ]  

where options are:

   -f filename 
       Opens "filename", which should be a spec data file.

   -s scannumber 
       When opening a data file, selects a scan number.

   -C servkey
       Starts a command server in splot. The command server will
       respond to requests identified by servkey only.

   -d debuglevel
       Prints messages to the standard output filtered by "debuglevel".
       Messages with level equal to or greater than "debuglevel" will
       be printed. The debug levels in order of decreasing verbosity
       are: "debug", "info", "warning", "error" and "critical".

   -D [debuglevel:]filename
       Prints messages to "filename" during execution filtered by
       "debuglevel".  Debug levels are the same as for the -d option.
       If no debug level is specified, "debug" is used.

   -h          
       Prints this help and exits.

   -V 
       Prints version info and exits.

If hostname:spec is specified %(progname)s will connect to the
"spec" application on "hostname". If "hostname" is not specfied,
"localhost" will be used.

With no arguments, %(progname)s will try to connect to "fourc"
on "localhost".

If a "varname" is provided, the connection will follow a data
array by that name, rather than the standard SCAN_D data array.

""" % {'progname': progname } )
# in splot.py

def run_app(servkey="splot_embedded", connectpars="localhost:fourc", winname="SPlot Embedded", host_menubar=None):
    """
    Embedded splot that mimics: splot -C <servkey> <connectpars>
    Returns (central QWidget, QApplication instance).
    If host_menubar is provided, SPlot will mount all its menus there.
    """
    import re
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from SPlotMain import SPlotMain
    from Preferences import Preferences
    from pyspec.client.SpecServer import SpecServer
    from pyspec.client.spec_updater import spec_updater

    global win, win_id, cmdsrv, watcher

    updater = spec_updater()
    updater.start()

    app = QApplication.instance() or CaptureApplication(winname, ['splot'])

    prefs = Preferences(); prefs.load()

    watcher = None
    mat = re.match(r"(?P<name>\w+)\_(?P<pid>\d+)", servkey)
    if mat:
        ppid = int(mat.group('pid'))
        if pid_runs(ppid):
            log.log(1, f"starting watchdog on parent process with pid={ppid}")
            watcher = watchdog(ppid); watcher.start()

    cmdsrv = SpecServer(name=servkey, allow_name_change=False, auto_update=False)

    win = SPlotMain(winname)
    win.set_command_server(cmdsrv)
    win_id = win.winId()

    # mount menus onto host menubar if provided
    if host_menubar is not None:
        try:
            win.use_external_menubar(host_menubar)
        except Exception:
            import traceback; log.log(2, traceback.format_exc())

    if prefs["geometry"]:
        x, y, width, height = map(int, prefs["geometry"].split(","))
    else:
        x, y, width, height = 200, 100, 1000, 600
    win.setGeometry(x, y, width, height)

    # Connect to SPEC (or change to your default)
    win.connectToSpec(connectpars, varname=None, check_datafile=True)

    timer = QTimer()
    timer.timeout.connect(update_cmdserver)
    timer.start(CMDSERVER_INTERVAL)

    return win.centralWidget(), app, win



if __name__ == '__main__':

    """ 
    By default spec starts in 'connection' mode.  Expected parameters
    are spec application name and optionally host where the application is
    running.

    The application can be started in file-only mode with the switch -f
    followed by the file name
    """

    # Default values
    host = None
    spec = "fourc"
    mode = "spec"
    filename = ""
    varname = None
    scannumber = None
    logstdout = False
    logtofile = False
    cmdserver = False
    servkey = None
    embedded_mode = False

    progname = os.path.basename(sys.argv[0])

    try:
        optlist, args = getopt.getopt(sys.argv[1:], "f:s:C:D:d:hrV", [
                                      'help', 'pyqt4', 'pyqt5', 'pyside', 'pyside2', 
                                      'matplotlib', 'qwt', 'embedded'])
    except:
        print("wrong usage\n")
        printUsage(progname)
        sys.exit(1)

    for o, a in optlist:
        if o == "-V":
            printVersion()
            sys.exit(0)
        elif o == "-f":
            mode = "fileonly"
            filename = a
        elif o == "-s":
            scannumber = int(a)
        elif o == "-C":
            cmdserver = True
            servkey = a
        elif o in ["-h", "--help"]:
            printUsage(progname)
            sys.exit(0)
        elif o == "-d":
            logstdout = True
            logoutlevel = a
        elif o == "-D":
            logtofile = True
            logfile = a
        elif o == "-r":
            Preferences.ignoreraise = True
        elif o == "--embedded":
            embedded_mode = True
        elif o in ["--pyqt4", "--pyqt5", "--pyside", "--pyside2", "--matplotlib", "--qwt"]:
            pass
        else:
            print("unknown option\n")
            printUsage(progname)
            sys.exit(1)

    if args:
        specparts = args[0]
        if len(args) > 1:
            varname = args[1]
    else:
        specparts = None

    loglevel = 2 # default

    if logstdout:
        if logoutlevel in loglevels:
            loglevel = loglevels[logoutlevel]
        else:  # log everything
            try:
                loglevel = int(logoutlevel)
            except:
                pass
        addStdOutHandler()
        no_output = False
    else:
        no_output = True

    if logtofile:
        parts = logfile.split(":")

        level = None

        if len(parts) == 2:
            level = parts[0]
            logfile = parts[1]

        if level and level in loglevels:
            loglevel = loglevels[level]
        else:  # log everything
            try:
                loglevel = int(loglevel)
            except:
                pass

        addFileHandler(logfile)

    log.setLevel(loglevel)

    # always add additional log to /tmp/splot.py
    #    addFileHandler("/tmp/splot.log")

    winname = chooseWindowName(filename, specparts)

    sys.excepthook = excepthook

    try:
        if no_output:
            if is_windows():
                main(mode, specparts, varname, filename,
                    scannumber, cmdserver, servkey, winname)
            else:
                with open("/dev/null", "w") as nullout:
                    with allio_redirector(nullout):
                        main(mode, specparts, varname, filename,
                            scannumber, cmdserver, servkey, winname)
        else:
            #import cProfile
            #cProfile.run("main(mode, specparts, varname, filename,"
               #"scannumber, cmdserver, servkey, winname)")
            main(mode, specparts, varname, filename,
               scannumber, cmdserver, servkey, winname)
    except Exception as e:
        log.log(1,"Error while executing. %s" % str(e))
        if logstdout:
            import traceback
            logmsg = traceback.format_exc()
            log.log(1,logmsg)
        else:
            print(
                "splot quit on error condition. Start splot with -d option to get debug info .")
        appQuit()
