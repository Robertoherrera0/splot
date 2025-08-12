#******************************************************************************
#
#  @(#)Preferences.py	3.4  10/30/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2020
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

import os
import re

from pyspec.css_logger import log

class _Preferences(object):
    """ Single instance (Singleton) maintaining a table of preferences through the application """

    defdirname = ".splot"
    deffilename = "prefs"

    def __init__(self):
        self._prefs = {}
        self.filename = None
        self.splotdir = os.path.join(os.path.expanduser("~"), self.defdirname)
        self.homefile = os.path.join(self.splotdir, self.deffilename)

    def findFile(self):
        if not self.filename:
            if os.path.exists(self.homefile):
                self.filename = self.homefile

    def get(self, *args):
        return self._prefs.get(*args)

    def __getitem__(self, ky):
        if ky in self._prefs:
            return self._prefs[ky]
        else:
            return None

    def __setitem__(self, ky, value):
        self._prefs[ky] = value

    def load(self, filename=None):

        if not filename:
            self.findFile()
        else:
            if os.path.isfile(filename) and os.access(filename, os.W_OK):
                self.filename = filename

        if not self.filename:
            return

        buf = open(self.filename).read()
        self._prefs = self.loadFromString(buf)

        log.log(2,"Application preferences loaded from %s " %
               self.filename)

    def keys(self):
        return self._prefs.keys()

    def setValue(self,key,value):
        self._prefs[key] = value
    def getValue(self,key, default=None):
        return self._prefs.get(key,default)
    def removeValue(self,key):
        if key in self._prefs:
            del self._prefs[key]

    def save(self, filename=None):

        if not filename:
            self.findFile()

        log.log(2,"Saving preferences to %s " % self.filename)
        outfile = filename
        if (not outfile) and self.filename:
            outfile = self.filename

        if outfile and os.path.isfile(outfile):
            if os.access(outfile, os.W_OK):
                writeok = True
            else:
                writeok = False
        else:  # try creating directory and file
            if filename:  # file is given but does not exist
                writeok = True
            else:  # try to create default file only if filename not provided
                if os.path.isdir(self.splotdir):
                    dirok = True
                else:
                    try:
                        os.makedirs(self.splotdir)
                        dirok = True
                    except OSError:
                        dirok = False

                if dirok:
                    preffile = os.path.join(self.splotdir, self.deffilename)
                    if not os.path.exists(preffile):
                        try:
                            open(preffile, "w").write("")
                            outfile = preffile
                            writeok = True
                        except OSError:
                            writeok = False
                    else:
                        if os.access(preffile, os.W_OK):
                            writeok = True
                        else:
                            writeok = False

        if writeok and outfile:
            open(outfile, "w").write(self.asString(self._prefs))
        else:
            log.log(2,"Cannot save preferences ")

    def getItems(self):
        return

    def asString(self, prefs):
        outstr = ""
        for ky in prefs:
            outstr += "%s: %s\n" % (ky, prefs[ky])
        return outstr

    def loadFromString(self, buffer):
        prefs = {}
        lines = buffer.split("\n")
        for line in lines:
            parts = line.split(":")
            ky = parts[0]
            val = ":".join(parts[1:]).strip()
            prefs[ky] = val

        return prefs

    def __str__(self):
        return self.asString(self._prefs)


class Preferences(_Preferences):

    def __new__(cls):
        if not hasattr(cls, '_inst'):
            cls._inst = super(Preferences, cls).__new__(cls)
        else:
            def init_pass(self, *dt, **mp): pass
            cls.__init__ = init_pass

        return cls._inst

if __name__ == '__main__':
    prefs = Preferences()
    prefs.load('prefs.exp')
    print(prefs)
