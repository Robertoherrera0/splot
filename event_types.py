#******************************************************************************
#
#  @(#)event_types.py	3.1  12/17/16 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016
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

# From /usr/include/X11/X.h
Event0 = 0
Event1 = 1
KeyPress = 2
KeyRelease = 3
ButtonPress = 4
ButtonRelease = 5
MotionNotify = 6
EnterNotify = 7
LeaveNotify = 8
FocusIn = 9
FocusOut = 10
KeymapNotify = 11
Expose = 12
GraphicsExpose = 13
NoExpose = 14
VisibilityNotify = 15
CreateNotify = 16
DestroyNotify = 17
UnmapNotify = 18
MapNotify = 19
MapRequest = 20
ReparentNotify = 21
ConfigureNotify = 22
ConfigureRequest = 23
GravityNotify = 24
ResizeRequest = 25
CirculateNotify = 26
CirculateRequest = 27
PropertyNotify = 28
SelectionClear = 29
SelectionRequest = 30
SelectionNotify = 31
ColormapNotify = 32
ClientMessage = 33
MappingNotify = 34
GenericEvent = 35
LASTEvent = 36

eventNames = [
    'Event0',
    'Event1',
    'KeyPress',
    'KeyRelease',
    'ButtonPress',
    'ButtonRelease',
    'MotionNotify',
    'EnterNotify',
    'LeaveNotify',
    'FocusIn',
    'FocusOut',
    'KeymapNotify',
    'Expose',
    'GraphicsExpose',
    'NoExpose',
    'VisibilityNotify',
    'CreateNotify',
    'DestroyNotify',
    'UnmapNotify',
    'MapNotify',
    'MapRequest',
    'ReparentNotify',
    'ConfigureNotify',
    'ConfigureRequest',
    'GravityNotify',
    'ResizeRequest',
    'CirculateNotify',
    'CirculateRequest',
    'PropertyNotify',
    'SelectionClear',
    'SelectionRequest',
    'SelectionNotify',
    'ColormapNotify',
    'ClientMessage',
    'MappingNotify',
    'GenericEvent',
    'LASTEvent',
]
