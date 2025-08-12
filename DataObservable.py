#******************************************************************************
#
#  @(#)DataObservable.py	3.1  12/17/16 CSS
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


"""
This module implements the Observer pattern for multiple Observers on
one or several Observables for the splot application.

One class are implemented:

    DataObservable
        subscribe( subscriber, eventid )
        emit(eventid)

"""

from collections import deque
from weakref import ref, proxy

class DataObservable(deque):
    def __init__(self):
        super(DataObservable,self).__init__()

    def emit (self, eventid, *args):
        '''Pass parameters to all observers and update states.'''
        todel = []
        for elem in self:
            objref,eid,cbt,cbm = elem

            # clean up queue if references has been deleted
            if objref() is None:
                todel.append(elem)
            elif eid == eventid:
                cbm(cbt,*args)

        if len(todel):
            self.cleanup(todel)
  
    def subscribe(self, obj,eventid,callb):
        '''Add a new subscriber to self.'''
        objref = ref(obj)
        cb_target = proxy(callb.__self__)
        cb_method = proxy(callb.__func__)
        elem = [objref,eventid,cb_target, cb_method]  
        if elem not in self:
            self.append(elem)

    def unsubscribe(self, subscriber, eventid=None):
        todel = []
        for elem in self: 
            objref,evid,cbt,cbm = elem
            obj = objref()
            if obj is None:
                todel.append(elem)
            elif obj() is subscriber:
                if eventid is None or eventid == evid:
                    todel.append(elem)

        if len(todel):
            self.cleanup(todel)

    def cleanup(self,objs=None):
        if objs is None:
            objlist = []
            for elem in self:
                if elem[0]() is None:
                    objlist.append(elem)
        else:
            objlist = objs

        for obj in objlist:
            self.remove(obj)
  
