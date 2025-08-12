#******************************************************************************
#
#  @(#)__init__.py	3.1  10/01/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2020
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

# usage :
#    import icons
#    icons.get_icon('zoom') #  returns QIcon("zoom.png")
#

import os
import glob
from QVariant import QIcon

_basedir = os.path.dirname(__file__)
_extensions = ["*png", "*jpg"]

_icond = {}

for _extn in _extensions:
    _files = glob.glob(os.path.join(_basedir,_extn)) 
    for _iconfile in _files:
        _iconname = os.path.splitext(os.path.basename(_iconfile))[0]
        if _iconname not in _icond:
            _icond[_iconname] = [_iconfile, None]

def get_icon(name):
    if name in _icond:
        if _icond[name][1] is None: 
            _icond[name][1] = QIcon(_icond[name][0])
        return _icond[name][1]

    raise BaseException("IconNotFound")
