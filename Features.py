#******************************************************************************
#
#  @(#)Features.py	3.4  12/13/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2016,2017,2020
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

import copy
from pyspec.utils import is_macos

all_features = ["2D"]

features = {}

features['2D'] = True
features['embed_xterm'] =  False
if is_macos():
    features['embed_xterm'] =  False

def setFeature(feature_name, flag, forced=False):

    if flag not in (True, False):
        return

    if feature_name in features.keys():
        # can only turn off, not on (unless forced)
        if flag is True and forced is False: 
            if features[feature_name] is False:
                return

    features[feature_name] = flag

def haveFeature(feature_name):
    if feature_name not in features.keys():
        return False

    return features[feature_name] and True or False
