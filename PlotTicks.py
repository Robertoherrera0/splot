#******************************************************************************
#
#  @(#)PlotTicks.py	3.3  06/13/21 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017
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
import math
import numpy as np
import math

from pyspec.css_logger import log

def nice_number(value):
    if value <= 0:
        return value

    exponent = math.floor(math.log(value, 10))
    fraction = value / pow(10,exponent)

    if fraction < 1.5: nice_fraction = 1.
    elif fraction < 2.5: nice_fraction = 2.
    elif fraction < 5.: nice_fraction = 4.
    elif fraction < 7.: nice_fraction = 6.
    else: nice_fraction = 10.

    return nice_fraction * pow(10,exponent)

def calc_ticks(it0, it1, nb_ivals, log=False):
    if log is True:
        return calc_log_ticks(it0, it1, nb_ivals)
    else:
        return calc_linear_ticks(it0, it1, nb_ivals)
 
def calc_linear_ticks(minval, maxval, nb_ivals=5):

    range_ = maxval - minval
    ticks = []

    if range_ == 0:
        i0 = 0.95 * minval
        i1 = 1.05 * maxval
        ticks = [i0,minval,i1]
        nice_range = nice_number(0)
        tick_space = nice_number(0)
    else:
        nice_range = nice_number(range_)
        tick_space = nice_number(nice_range/float(nb_ivals-1))
        i0 = math.floor(minval / tick_space) * tick_space
        i1 = math.ceil(maxval / tick_space) * tick_space

        tick = i0
        ticks = [tick]
        while math.fabs(i1-tick) > 10e-6:
           tick += tick_space
           ticks.append(float("%g" % tick))

    return i0, i1, ticks

def calc_log_ticks(minval, maxval, nb_ivals):
    # calculate ticks for both positive and negative 
    # shown by matplotlib using set_yscal("symlog")

    log.log(2, "calculating log ticks for {} {}".format(minval,maxval))

    pmin = nmin = None
    if maxval > 0: 
        max_val = maxval
        if minval >= 0:
            min_val = minval
        else:
            min_val = 0
        pmin, pmax, posit_ticks = calc_range_log_ticks(min_val, max_val)  

    #if minval < 0:
        #max_val = -minval
        #if maxval >= 0:
           #min_val = 0
        #else:
            #min_val = -maxval
        #calc_negat = True
        #nmin, nmax, negat_ticks = calc_range_log_ticks(min_val, max_val)  


    ticks = []
    min2show = max2show = None

    if nmin is not None:
        print("Calculated negative ticks for:")
        print( nmin, nmax, negat_ticks )

        negat_ticks.reverse()
        negat_ticks = [-x for x in negat_ticks]

        ticks += negat_ticks
        min2show = -nmax
        max2show = -nmin

    if pmin is not None:
        if ticks:
            ticks += [0]

        if pmin is not None:
             print("Calculated positive ticks for:")
             print( pmin, pmax, posit_ticks )

        ticks += posit_ticks
        if min2show is None:
            min2show = pmin
        max2show = pmax

    log.log(2,"{} {} {}".format(min2show, max2show, ticks ))
    return min2show, max2show, ticks

def calc_range_log_ticks(minval, maxval):

    rangemax = math.log10(maxval)
    rangemax = int(math.ceil(rangemax))

    if minval > 0:
        rangemin = math.log10(minval)
        rangemin = int(math.floor(rangemin))
    else:
        rangemin = 0

    majticks = []  # major
    medticks = []  # extra labels
    minticks = []  # minor ticks

    # First calculate to hold the range in exact decades
    for i in range(rangemin, rangemax + 1):
        majticks.append(pow(10, i))

        nb_majors = len(majticks)

        if nb_majors <= 2:
            for i in range(nb_majors - 1):
                majval = majticks[i]
                for j in range(2, 10):  # the first one is already a major
                    medticks.append(majval * j)
                for j in range(2, 10):
                    minticks.append(majval * j)
        elif nb_majors <= 4:  # at 2 and 5
            for i in range(nb_majors - 1):
                majval = majticks[i]
                medticks.append(majval * 2)
                medticks.append(majval * 5)
        elif nb_majors < 6:  # medium ticks at 5
            for i in range(nb_majors - 1):
                majval = majticks[i]
                medticks.append(majval * 5)
        else:  # show only majors
            pass
   
    if medticks:

       stickidx = None
       btickidx = None

       for tickidx in range(len(medticks)):
           tick = medticks[tickidx]
           if tick < minval:
               stickidx = tickidx
           if tick > maxval:
               btickidx = tickidx
               break

       if stickidx is not None:
           min2show = medticks[stickidx]
           majticks[0] = min2show
       else:
           min2show = majticks[0]
           stickidx = -1

       if btickidx is not None:
           max2show = medticks[btickidx]
           majticks[-1] = max2show
       else:
           max2show = majticks[-1]
           btickidx = len(medticks)
           medticks = medticks[stickidx + 1:btickidx]
    else:
        min2show = rangemin
        max2show = rangemax

    return min2show, max2show, majticks


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: %s minval maxval nbival" % sys.argv[0])
        sys.exit(0)

    it0, it1 = map(float,sys.argv[1:3])
    nb_ivals = int(sys.argv[3])
    print( calc_ticks(it0, it1, nb_ivals, log=True) )

