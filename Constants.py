#******************************************************************************
#
#  @(#)Constants.py	3.8  03/28/21 CSS
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
#
# Intervals for some for some Qt timers
# (all in msec)
#
CMDSERVER_INTERVAL = 5  # time to check for new client commands in splot command server
WATCHDOG_INTERVAL = 500  # time to check for parent pid running
PENDING_INTERVAL = 30  # time to check for pending graphics requests
PENDING_INTERVAL_INACTIVE = 400  # time to check for pending graphics requests on inactive sources
UPDATEFILE_INTERVAL = 1000  # time to check whether an opened file has been modified
# time to check for data modified if scan is idle (shared mem mode)
UPDATE_IDLE = 200
# time to check for data modified if if scan is active (shared mem mode)
UPDATE_ACTIVE = 50
# time to update plot with all events received (server mode)
UPDATE_SERVER = 5 
UPDATE_VARIABLE = 1000  # time to check for data modified when following a spec variable

"""
DataType constants.  Can be
   DATA_STATIC:  Data is fixed in time. It will not change
   DATA_LIVE:    Data is currently being produced.  Some other metadata may affect representation.
                 For example the directory "ranges" in metadata may show the expected limits for the
                 data that is being produced. Example: to dimension the range of the x-axis during a motor scan
   DATA_TREND:   Data is coming continuously. The application may then configure the amount of data to show at any
                 one time, for example: show only the latest 100 points of the dataset.
   DATA_FILE:    Data is coming from a file. 
"""
DATA_UNKNOWN = 0
DATA_STATIC = 1
DATA_LIVE = 2
DATA_TREND = 3
DATA_FILE = 4

# DATA_1D_ROW = 0
# DATA_1D_COLUMN = 1
# DATA_2D = 2

DATA_SCAN = 0
DATA_MCA = 1
# 
#
# Events emitted by DataBlock
#
COLUMNS_CHANGED = 1
DATA_CHANGED = 2
TITLE_CHANGED = 3
DATACONFIG_CHANGED = 4
NEW_SCAN = 8
SELECTION_CHANGED = 10
X_SELECTION_CHANGED = 11
Y_SELECTION_CHANGED = 15
Y1_SELECTION_CHANGED = 16
Y2_SELECTION_CHANGED = 17
STATS_UPDATED = 21
ACTIVECOLUMN_CHANGED = 22
SLICES_CHANGED = 24
PLOT2D_CHANGED = 31

#
# Flags for plot configuration from spec
#
PL_YLOG = 0x00020  # logarithmic y axis
PL_YZERO = 0x00010  # force y min to zero
PL_BG_SUB = 0x00040  # subtract background
PL_NO_DOTS = 0x00100  # don't plot with big dots
PL_NO_LINES = 0x00200  # don't plot with lines
PL_NO_EBARS = 0x00400  # don't draw error bars
PL_RAISE_1 = 0x01000  # raise plot at each point
PL_RAISE_2 = 0x02000  # raise plot at the end of the scan
PL_GRID = 0x10000  # draw a background grid
PL_FULL_RANGE = 0x20000  # show full range of x axis during scans
PL_MULTI_SPLOT = 0x80000  # use multiple windows

#
# Plot Modes
#
PlotNormalMode, PlotMeshMode, PlotTimeMode = (0, 1, 2)

PLOT_1D, PLOT_2D = (1,2)

#
# Array types
#    DATA_1D = One or two columns representing a set of X,Y
#    DATA_1DS = Set of 1D columns allowing selection of X and Ys
#    DATA_2D = 2D type data
#
DATA_1D, DATA_1DS, DATA_2D = (1,2,3)

#
#
# AXIS Identification
#
X_AXIS = 0
Y1_AXIS = 1
Y2_AXIS = 2

#
# Source Types
#
SOURCE_ANY = 0x1
SOURCE_SPEC = 0x2
SOURCE_FILE = 0x4 
SOURCE_USER = 0x8 
SOURCE_1D = 0x10
SOURCE_2D = 0x20
SOURCE_MCA = 0x100 # it is also a 1D

# 
# Possible source states
# 
STATUS_READY = 0x1
STATUS_BUSY = 0x2
STATUS_OFF = 0x4

#
# Marker Types
#
MARKER_VERTICAL = 0
MARKER_TEXT = 1
MARKER_SEGMENT = 2

#
# Some color settings
#
CROSSHAIRS_COLOR = "#00c000"
REGIONLINE_COLOR = "#c00000"
REGIONBKG_COLOR = "#ececdd"
ZOOM_RUBBERBAND_COLOR = "#666666"

#
# Zoom modes
#
ZOOM_MODE = 0
CROSSHAIRS_MODE = 1
REGIONZOOM_MODE = 2

#
# Default Z level (display order) for some items
#
ZLEVEL_SELECTED = 700
ZLEVEL_CURVE = 500
ZLEVEL_MARKER = 400
ZLEVEL_GRID = 200
