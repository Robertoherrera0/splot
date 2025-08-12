#******************************************************************************
#
#  @(#)FunctionModels.py	3.1  12/17/16 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2016
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

import numpy as np
from abc import abstractmethod

class FunctionModel(object):
    def __init__(self):
        self.__added = []
          
    def is_lineal(self):
        return False

    def get_description(self):
        return "No description"

    def get_mnemonic(self):
        # very short fit model id
        return "fit"

    def get_param_names(self):
        return "nada"

    def __add__(self,other):
        print("Adding "+other.get_description()+" to "+self.get_description())
        self.__added.append(other)

    @abstractmethod
    def __call__(self,pararr, xarr):
        pass

class GaussianModel(FunctionModel):

    def get_description(self):
        return "Gauss function + linear background"

    def get_formula_description(self):
        return "y = a + bx + c * exp (-(x-xo)^2/2*sigma^2)"

    def get_mnemonic(self):
        # very short fit model id
        return "gauss"

    def get_param_names(self):
        return ['backgr_x0','backgr_slope', 'height', 'pos', 'fwhm']

    def __call__(self, pararr, xarr):
        dummy=2.3548200450309493*(xarr-pararr[3])/pararr[4]
        return pararr[0] + pararr[1] * xarr + pararr[2] * self.__exp(-0.5 * dummy * dummy)

    def estimate_parameters(self,xdata,ydata,stats=None,tail=5):

        if len(ydata) > 12:
            first_tail_avg = np.average(ydata[:5])
            last_tail_avg = np.average(ydata[-5:])
        elif len(ydata) > 5:
            first_tail_avg = np.average(ydata[:2])
            last_tail_avg = np.average(ydata[-2:])
        else:
            first_tail_avg = ydata[0]
            last_tail_avg = ydata[-1]

        a0 = (first_tail_avg + last_tail_avg) / 2.0
        a1 = 0

        return [a0,a1, stats['peak'][1], stats['peak'][0], stats['fwhm'][0]]
              
    def result_message(self,pararr):
        p0,p1,p2,p3,p4 = pararr
        msg = "peak is %3.2f at %3.2f / fwhm is %3.2f - bckg(a+bx) with a=%3.2f and b=%3.2f " % (p2,p3,p4,p0,p1)
        return msg

    def __exp(self, xarr):
        return np.exp(xarr*np.less(np.abs(xarr),250))-1.0*np.greater_equal(np.abs(xarr),250)

class LorentzianModel(FunctionModel):
    def get_description(self):
        return "Lorentz distribution + linear background"

    def get_formula_description(self):
        return "y = a + bx + c * 1 / ((pi*hwhm)*(1- ((x-x0)/hwhm)^2))"

    def get_param_names(self):
        return ['backgr_x0','backgr_slope', 'height', 'pos', 'fwhm']

    def get_mnemonic(self):
        # very short fit model id
        return "lotz"

    def __call__(self, parr, xarr):
        fwhm = parr[4]
        peakpos = parr[3]
        peakhgt = parr[2]
        back_x0 = parr[0]
        back_slope = parr[1]

        background = back_x0 + back_slope * xarr
        hwhm = parr[4]/2.0
        dummy = (xarr -  peakpos) / hwhm
        lorbody =  np.pi *  (1 + dummy * dummy) 

        return background + 2 * peakhgt / lorbody

    def estimate_parameters(self,xdata,ydata,stats=None,tail=5):

        if len(ydata) > 12:
            first_tail_avg = np.average(ydata[:5])
            last_tail_avg = np.average(ydata[-5:])
        elif len(ydata) > 5:
            first_tail_avg = np.average(ydata[:2])
            last_tail_avg = np.average(ydata[-2:])
        else:
            first_tail_avg = ydata[0]
            last_tail_avg = ydata[-1]

        a0 = (first_tail_avg + last_tail_avg) / 2.0
        a1 = 0

        return [a0,a1, stats['peak'][1], stats['peak'][0], stats['fwhm'][0]]
              
    def result_message(self,pararr):
        p0,p1,p2,p3,p4 = pararr
        msg = "peak is %3.2f at %3.2f / fwhm is %3.2f - bckg(a+bx) with a=%3.2f and b=%3.2f " % (p2,p3,p4,p0,p1)
        return msg

class LinearModel(FunctionModel):
    def is_lineal(self):
        return True

    def get_description(self):
        return "Linear"

    def get_formula_description(self):
        return "y = x0 + slope*x"

    def get_param_names(self):
        return ['x0','slope']

    def get_mnemonic(self):
        # very short fit model id
        return "line"

    def __call__(self,pararr, xarr):
        return pararr[0] + pararr[1]*xarr

    def result_message(self,pararr):
        p0, p1 = pararr
        msg = "x0 is %3.2f / slope is %3.2f" % (p0, p1)
        return msg

    def estimate_parameters(self,xdata,ydata,stats=None,tail=5):
        if len(ydata) > 12:
            y1 = np.average(ydata[:5])
            y2 = np.average(ydata[-5:])
            x1 = np.average(xdata[:5])
            x2 = np.average(xdata[-5:])
        elif len(ydata) > 5:
            y1 = np.average(ydata[:2])
            y2 = np.average(ydata[-2:])
            x1 = np.average(xdata[:2])
            x2 = np.average(xdata[-2:])
        else:
            y1 = ydata[0]
            y2 = ydata[-1]
            x1 = xdata[0]
            x2 = xdata[-1]

      
        slope = (y2 - y1) / (x2 - x1)
        x0 = ((y2 - slope * x2) + (y1 - slope*x1)) / 2.0
        return [x0, slope]


class IdentityModel(FunctionModel):
    def get_description(self):
        return "same"

    def __call__(self,parr,xarr):
        xarr = 1/0.0
        return xarr

FunctionModels = [GaussianModel, LorentzianModel, LinearModel]

if __name__ == '__main__':
   try:
       model = IdentityModel() 
       print(model.get_description())
       xarr = np.array([3,6,9,12,2,34])
       print(model([4,0.5], xarr))
   except:
       print("Implementation problem in user model")
       
