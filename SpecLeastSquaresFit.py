#******************************************************************************
#
#  @(#)SpecLeastSquaresFit.py	3.1  12/17/16 CSS
#
#  "splot" Release 3
#
#/*##########################################################################
# Copyright (C) 2004-2006 European Synchrotron Radiation Facility
#
# This file is part of the PyMCA X-ray Fluorescence Toolkit developed at
# the ESRF by the Beamline Instrumentation Software Support (BLISS) group.
#
# This toolkit is free software; you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) 
# any later version.
#
# PyMCA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# PyMCA; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
# Suite 330, Boston, MA 02111-1307, USA.
#
# PyMCA follows the dual licensing model of Trolltech's Qt and Riverbank's PyQt
# and cannot be used as a free plugin for a non-free program. 
#
# Please contact the ESRF industrial unit (industry@esrf.fr) if this license 
# is a problem to you.
#############################################################################*/

#
# Revised to be used without oldnumeric module. Not supported from numpy 1.9
#   (V. Rey  txo@txolutions.com )
#
import copy

import numpy as np
from numpy.linalg import inv as npinv

__author__ = "V.A. Sole <sole@esrf.fr>"
__revision__ = "$Revision: 1.17 $"

# codes understood by the routine
CFREE       = 0
CPOSITIVE   = 1
CQUOTED     = 2
CFIXED      = 3
CFACTOR     = 4
CDELTA      = 5
CSUM        = 6
CIGNORED    = 7

def LeastSquaresFit(model, 
                    parameters0, 
                    data=None, 
                    maxiter = 100,
                    constrains=None,
                    weightflag = 0,
                    model_deriv=None,
                    deltachi=None,
                    fulloutput=0,
                    xdata=None,
                    ydata=None,
                    sigmadata=None,
                    linear=False):

    parameters = np.array(parameters0, float)

    if deltachi is None:
        deltachi = 0.01
    
    if xdata is None:
        x=np.array(map(lambda y:y[0],data))
    else:
        x=xdata

    if constrains is None:
        nbpars = len(parameters0)
        constrains = [[0,]*nbpars]*3
                                    
    # Choose which method to use

    if linear:
           return LinearLeastSquaresFit(model,
                                        parameters0,
                                        data,
                                        maxiter,
                                        constrains,
                                        weightflag,
                                        model_deriv=model_deriv,
                                        deltachi=deltachi,
                                        fulloutput=fulloutput,
                                        xdata=xdata,
                                        ydata=ydata,
                                        sigmadata=sigmadata)   

    try:
        model(parameters,x)
    except TypeError:
        print("You should reconsider how to write your function")
        raise TypeError()
    
    return RestreinedLeastSquaresFit(model,
                              parameters0,
                              data,
                              maxiter,
                              constrains,
                              weightflag,
                              model_deriv=model_deriv,
                              deltachi=deltachi,
                              fulloutput=fulloutput,
                              xdata=xdata,
                              ydata=ydata,
                              sigmadata=sigmadata)

def LinearLeastSquaresFit(model,parameters0,data0,maxiter,
                                constrains0,
                                weightflag,
                                model_deriv=None,
                                deltachi=0.01,
                                fulloutput=0,
                                xdata=None,
                                ydata=None,
                                sigmadata=None):

    #get the codes:
    #  0 = Free       1 = Positive     2 = Quoted
    #  3 = Fixed      4 = Factor       5 = Delta
    #  6 = Sum        7 = ignored


    #
    constrains=copy.copy(constrains0)

    #for i in range(len(parameters0)):
        #constrains[0].append(constrains0[0][i])
        #constrains[1].append(constrains0[1][i])
        #constrains[2].append(constrains0[2][i])

    for i in range(len(parameters0)):
        if type(constrains[0][i]) == type('string'):
            
            if constrains[0][i] == "FREE":
                constrains[0][i] = CFREE
            elif constrains[0][i] == "POSITIVE":
                constrains[0][i] = CPOSITIVE 
            elif constrains[0][i] == "QUOTED":
                constrains[0][i] = CQUOTED
            elif constrains[0][i] == "FIXED":
                constrains[0][i] = CFIXED 
            elif constrains[0][i] == "FACTOR":
                constrains[0][i] = CFACTOR 
                constrains[1][i] = int(constrains[1][i]) 
            elif constrains[0][i] == "DELTA":
                constrains[0][i] = CDELTA 
                constrains[1][i] = int(constrains[1][i]) 
            elif constrains[0][i] == "SUM":
                constrains[0][i] = CSUM 
                constrains[1][i] = int(constrains[1][i]) 
            elif constrains[0][i] == "IGNORED":
                constrains[0][i] = CIGNORED 
            elif constrains[0][i] == "IGNORE":
                constrains[0][i] = CIGNORED 
            else:
                raise ValueError("Unknown constraint %s" % constrains[0][i])

        if (constrains[0][i] == CQUOTED):
            raise ValueError("Linear fit cannot handle quoted constraint")

    parameters = np.array(parameters0)

    if data0 is not None:
        selfx = np.array(map(lambda x:x[0],data0))
        selfy = np.array(map(lambda x:x[1],data0))
    else:
        selfx = xdata
        selfy = ydata

    selfweight = np.ones(selfy.shape,float)

    nr0 = len(selfy)

    if data0 is not None:
        nc =  len(data0[0])
    else:
        if sigmadata is None:
            nc = 2
        else:
            nc = 3

    if weightflag == 1:
        if nc == 3:
            if data0 is not None:
                dummy = np.abs(np.array(map(lambda x:x[2],data0)))
            else:
                dummy = np.abs(np.array(sigmadata)) 
            selfweight = 1.0 / (dummy + np.equal(dummy,0))
            selfweight = selfweight * selfweight
        else:
            selfweight = 1.0 / (np.abs(selfy) + np.equal(np.abs(selfy),0))            

    n_param = len(parameters)

    x = selfx
    y = selfy
    weight = selfweight
    iteri = maxiter
    niter = 0
    newpar = np.copy( parameters )

    while (iteri>0):
        niter+=1
        chisq0, alpha0, beta,\
        n_free, free_index, noigno, fitparam, derivfactor = ChisqAlphaBeta(
                                                 model,newpar,
                                                 x,y,weight,constrains,
                                                 model_deriv=model_deriv,
                                                 linear=1)
        nr, nc = alpha0.shape
        fittedpar = np.dot(beta, npinv(alpha0))

        #check respect of constraints (only positive is handled -force parameter to 0 and fix it-)
        error = 0

        for i in range(n_free):
            if constrains [0] [free_index[i]] == CPOSITIVE:
                if fittedpar[0,i] < 0:
                    #fix parameter to 0.0 and re-start the fit
                    newpar[free_index[i]] = 0.0
                    constrains[0][free_index[i]] = CFIXED
                    error = 1

        if error:continue

        for i in range(n_free):
            newpar[free_index[i]] = fittedpar[0,i]  
        newpar=np.array(getparameters(newpar,constrains))
        iteri=-1

    yfit = model(newpar,x)
    chisq = np.sum( weight * (y-yfit) * (y-yfit))
    sigma0 = np.sqrt(np.abs(np.diagonal(npinv(alpha0))))
    sigmapar = getsigmaparameters(newpar,sigma0,constrains)
    lastdeltachi = chisq

    if not fulloutput:
        return newpar.tolist(), chisq/(len(y)-len(sigma0)), sigmapar.tolist()    
    else:
        return newpar.tolist(), chisq/(len(y)-len(sigma0)), sigmapar.tolist(),niter,lastdeltachi

def RestreinedLeastSquaresFit(model,parameters0,data0,maxiter,
                constrains0,weightflag,model_deriv=None,deltachi=0.01,fulloutput=0,
                                    xdata=None,
                                    ydata=None,
                                    sigmadata=None):
    #get the codes:
    # 0 = Free       1 = Positive     2 = Quoted
    # 3 = Fixed      4 = Factor       5 = Delta
    # 6 = Sum        7 = ignored

    constrains = copy.copy(constrains0)

    for i in range(len(parameters0)):
        if type(constrains[0][i]) == type('string'):
            #get the number
            if   constrains[0][i] == "FREE":
                 constrains[0][i] = CFREE
            elif constrains[0][i] == "POSITIVE":
                 constrains[0][i] = CPOSITIVE 
            elif constrains[0][i] == "QUOTED":
                 constrains[0][i] = CQUOTED 
            elif constrains[0][i] == "FIXED":
                 constrains[0][i] = CFIXED 
            elif constrains[0][i] == "FACTOR":
                 constrains[0][i] = CFACTOR 
                 constrains[1][i] = int(constrains[1][i]) 
            elif constrains[0][i] == "DELTA":
                 constrains[0][i] = CDELTA 
                 constrains[1][i] = int(constrains[1][i]) 
            elif constrains[0][i] == "SUM":
                 constrains[0][i] = CSUM 
                 constrains[1][i] = int(constrains[1][i]) 
            elif constrains[0][i] == "IGNORED":
                 constrains[0][i] = CIGNORED 
            elif constrains[0][i] == "IGNORE":
                 constrains[0][i] = CIGNORED 
            else:
                raise ValueError("Unknown constraint %s" % constrains[0][i])


    parameters = np.array(parameters0)
    fittedpar = np.array(parameters0)

    flambda = 0.001

    iteri = maxiter
    niter = 0

    if data0 is not None:
        selfx = np.array(map(lambda x:x[0],data0))
        selfy = np.array(map(lambda x:x[1],data0))
    else:
        selfx = xdata
        selfy = ydata
    selfweight = np.ones(selfy.shape,float)
    nr0 = len(selfy)
    if data0 is not None:
        nc =  len(data0[0])
    else:
        if sigmadata is None:
            nc = 2
        else:
            nc = 3
            
    if weightflag == 1:
            if nc == 3:
                if data0 is not None:
                    dummy = np.abs(np.array(map(lambda x:x[2],data0)))
                else:
                    dummy = np.abs(np.array(sigmadata)) 
                selfweight = 1.0 / (dummy + np.equal(dummy,0))
                selfweight = selfweight * selfweight
            else:
                selfweight = 1.0 / (np.abs(selfy) + np.equal(np.abs(selfy),0))            
    n_param = len(parameters)
    selfalphazeros = np.zeros((n_param, n_param),float)
    selfbetazeros = np.zeros((1,n_param),float)
    index = np.arange(0,nr0,2)
    while (iteri > 0):
        niter = niter + 1
        if (niter < 2) and (n_param*3 < nr0):
                x=np.take(selfx,index)
                y=np.take(selfy,index)
                weight=np.take(selfweight,index)
        else:
                x=selfx
                y=selfy
                weight = selfweight       
                
        chisq0, alpha0, beta,\
        n_free, free_index, noigno, fitparam, derivfactor = ChisqAlphaBeta(
                                                 model,fittedpar,
                                                 x,y,weight,constrains,model_deriv=model_deriv)
        nr, nc = alpha0.shape
        flag = 0
        lastdeltachi = chisq0
        while flag == 0:
            newpar = np.copy( parameters )
            alpha = alpha0 + flambda * np.identity(nr) * alpha0
            deltapar = np.dot(beta, npinv(alpha))
            pwork = np.zeros(deltapar.shape, float)
            for i in range(n_free):
                if constrains [0] [free_index[i]] == CFREE:
                    pwork [0] [i] = fitparam [i] + deltapar [0] [i]
                elif constrains [0] [free_index[i]] == CPOSITIVE:
                    pwork [0] [i] = fitparam [i] + deltapar [0] [i]
                elif constrains [0] [free_index[i]] == CQUOTED:
                    pmax=max(constrains[1] [free_index[i]],
                            constrains[2] [free_index[i]])            
                    pmin=min(constrains[1] [free_index[i]],
                            constrains[2] [free_index[i]])
                    A = 0.5 * (pmax + pmin)
                    B = 0.5 * (pmax - pmin)
                    if (B != 0):
                        pwork [0] [i] = A + \
                                    B * np.sin(np.arcsin((fitparam[i] - A)/B)+ \
                                    deltapar [0] [i])
                    else:
                        print( "Error processing constrained fit")
                        print( "Parameter limits are",pmin,' and ',pmax)
                        print( "A = ",A,"B = ",B)
                newpar [free_index[i]] = pwork [0] [i]
            newpar=np.array(getparameters(newpar,constrains))
            workpar = np.take(newpar,noigno)
            yfit = model(workpar,x)
            chisq = np.sum( weight * (y-yfit) * (y-yfit))
            if chisq > chisq0:
                flambda = flambda * 10.0
                if flambda > 1000:
                    flag = 1
                    iteri = 0
            else:
                flag = 1 
                fittedpar = np.copy( newpar )
                lastdeltachi = (chisq0-chisq)/(chisq0+(chisq0==0))
                if (lastdeltachi) < deltachi:
                    iteri = 0
                chisq0 = chisq
                flambda = flambda / 10.0
                
            iteri -= 1

    sigma0 = np.sqrt(np.abs(np.diagonal(npinv(alpha0))))
    sigmapar = getsigmaparameters(fittedpar,sigma0,constrains)
    if not fulloutput:
        return fittedpar.tolist(), chisq/(len(yfit)-len(sigma0)), sigmapar.tolist()    
    else:
        return fittedpar.tolist(), chisq/(len(yfit)-len(sigma0)), sigmapar.tolist(),niter,lastdeltachi

def ChisqAlphaBeta(model, parameters, x,y,weight, constrains,model_deriv=None,linear=False):
    
    n_param = len(parameters)
    n_free = 0
    fitparam = []
    free_index = []
    noigno = []
    derivfactor = []

    for i in range(n_param):
        if constrains[0] [i] != CIGNORED:
            noigno.append(i)
        if constrains[0] [i] == CFREE:
            fitparam.append(parameters [i])
            derivfactor.append(1.0)
            free_index.append(i)
            n_free += 1
        elif constrains[0] [i] == CPOSITIVE:
            fitparam.append(np.abs(parameters[i]))
            derivfactor.append(1.0)
            free_index.append(i)
            n_free += 1
        elif constrains[0] [i] == CQUOTED:
            pmax=max(constrains[1] [i],constrains[2] [i])            
            pmin=min(constrains[1] [i],constrains[2] [i])
            if ((pmax-pmin) > 0) & \
               (parameters[i] <= pmax) & \
               (parameters[i] >= pmin):
                A = 0.5 * (pmax + pmin)
                B = 0.5 * (pmax - pmin)
                if 1:
                    fitparam.append(parameters[i])
                    derivfactor.append(B*np.cos(np.arcsin((parameters[i] - A)/B)))
                else:
                    help0 = np.arcsin((parameters[i] - A)/B)
                    fitparam.append(help0)
                    derivfactor.append(B*np.cos(help0))
                free_index.append(i)
                n_free += 1                        
    fitparam = np.array(fitparam, float)
    alpha = np.zeros((n_free, n_free),float)
    beta = np.zeros((1,n_free),float)
    delta = (fitparam + np.equal(fitparam,0.0)) * 0.00001
    nr  = x.shape[0]
    ##############
    # Prior to each call to the function one has to re-calculate the
    # parameters
    pwork = np.copy( parameters )
    for i in range(n_free):
        pwork [free_index[i]] = fitparam [i]
    newpar = getparameters(pwork.tolist(),constrains)
    newpar = np.take(newpar,noigno)    
    for i in range(n_free):
        if model_deriv is None:
            pwork [free_index[i]] = fitparam [i] + delta [i]
            newpar = getparameters(pwork.tolist(),constrains)
            newpar=np.take(newpar,noigno)
            f1 = model(newpar, x)
            pwork [free_index[i]] = fitparam [i] - delta [i]
            newpar = getparameters(pwork.tolist(),constrains)
            newpar=np.take(newpar,noigno)
            f2 = model(newpar, x)
            help0 = (f1-f2) / (2.0 * delta [i])
            help0 = help0 * derivfactor[i] 
            pwork [free_index[i]] = fitparam [i]       
        else:
            newpar = getparameters(pwork.tolist(),constrains)
            help0 = model_deriv(pwork,free_index[i],x)
            help0 = help0 * derivfactor[i]        
        
        if i == 0 :
            deriv = help0
        else:
            deriv = np.concatenate ((deriv,help0), 0)

    #line added to resize outside the loop

    #deriv=np.resize(deriv,(n_free,nr))
    deriv.shape = (n_free, nr)

    if linear:
        pseudobetahelp = weight * y
    else:
        yfit = model(newpar, x)
        deltay = y - yfit
        help0 = weight * deltay
    for i in range(n_free):
        derivi = np.resize(deriv [i,:], (1,nr))
        if linear:
            if i==0:
                beta = np.resize(np.sum((pseudobetahelp * derivi),1),(1,1))
            else:
                beta = np.concatenate((beta, np.resize(np.sum((pseudobetahelp * derivi),1),(1,1))), 1)        
        else:
            help1 = np.resize(np.sum((help0 * derivi),1),(1,1))
            if i == 0:
                beta = help1
            else:
                beta = np.concatenate ((beta, help1), 1)

        help1 = np.dot(deriv, np.transpose(weight*derivi))

        if i == 0:
            alpha = help1
        else:
            alpha = np.concatenate((alpha, help1),1)

    if linear:
        chisq = 0.0
    else:
        chisq = np.sum(help0 * deltay)

    return chisq, alpha, beta, \
           n_free, free_index, noigno, fitparam, derivfactor

def getparameters(parameters,constrains):
    # 0 = Free       1 = Positive     2 = Quoted
    # 3 = Fixed      4 = Factor       5 = Delta
    newparam=[]
    #first I make the free parameters
    #because the quoted ones put troubles
    for i in range(len(constrains [0])):
        if constrains[0][i] == CFREE:
            newparam.append(parameters[i])
        elif constrains[0][i] == CPOSITIVE:
            #newparam.append(parameters[i] * parameters[i])
            newparam.append(abs(parameters[i]))
        elif constrains[0][i] == CQUOTED:
            if 1:
                newparam.append(parameters[i])
            else:
                pmax=max(constrains[1] [i],constrains[2] [i])            
                pmin=min(constrains[1] [i],constrains[2] [i])
                A = 0.5 * (pmax + pmin)
                B = 0.5 * (pmax - pmin)
                newparam.append(A + B * np.sin(parameters[i]))
        elif abs(constrains[0][i]) == CFIXED:
            newparam.append(parameters[i])
        else:
            newparam.append(parameters[i])
    for i in range(len(constrains [0])):
        if constrains[0][i] == CFACTOR:
            newparam[i] = constrains[2][i]*newparam[int(constrains[1][i])]
        elif constrains[0][i] == CDELTA:
            newparam[i] = constrains[2][i]+newparam[int(constrains[1][i])]
        elif constrains[0][i] == CIGNORED:
            newparam[i] = 0            
        elif constrains[0][i] == CSUM:
            newparam[i] = constrains[2][i]-newparam[int(constrains[1][i])]
    return newparam

def getsigmaparameters(parameters,sigma0,constrains):
    # 0 = Free       1 = Positive     2 = Quoted
    # 3 = Fixed      4 = Factor       5 = Delta
    n_free = 0
    sigma_par = np.zeros(parameters.shape,float)
    for i in range(len(constrains [0])):
        if constrains[0][i] == CFREE:
            sigma_par [i] = sigma0[n_free]
            n_free += 1
        elif constrains[0][i] == CPOSITIVE:
            sigma_par [i] = sigma0[n_free]
            n_free += 1
        elif constrains[0][i] == CQUOTED:
            pmax = max(constrains [1] [i], constrains [2] [i])
            pmin = min(constrains [1] [i], constrains [2] [i])
            A = 0.5 * (pmax + pmin)
            B = 0.5 * (pmax - pmin)
            if (B > 0) & (parameters [i] < pmax) & (parameters [i] > pmin):
                sigma_par [i] = np.abs(B) * np.cos(parameters[i]) * sigma0[n_free]
                n_free += 1
            else:
                sigma_par [i] = parameters[i]
        elif abs(constrains[0][i]) == CFIXED:
            sigma_par[i] = parameters[i]
    for i in range(len(constrains [0])):
        if constrains[0][i] == CFACTOR:
            sigma_par [i] = constrains[2][i]*sigma_par[int(constrains[1][i])]
        elif constrains[0][i] == CDELTA:
            sigma_par [i] = sigma_par[int(constrains[1][i])]
        elif constrains[0][i] == CSUM:
            sigma_par [i] = sigma_par[int(constrains[1][i])]
    return sigma_par

def fitpar2par(fitpar,constrains,free_index):
    newparam = []
    for i in range(len(constrains [0])):
        if constrains[0][free_index[i]] == CFREE:
            newparam.append(fitpar[i])
        elif constrains[0][free_index[i]] == CPOSITIVE:
            newparam.append(fitpar[i] * fitpar [i])
        elif abs(constrains[0][free_index[i]]) == CQUOTED:
            pmax=max(constrains[1] [free_index[i]],constrains[2] [free_index[i]])            
            pmin=min(constrains[1] [free_index[i]],constrains[2] [free_index[i]])
            A = 0.5 * (pmax + pmin)
            B = 0.5 * (pmax - pmin)
            newparam.append(A + B * np.sin(fitpar[i]))
    return newparam
    
# A function provided for fitting model should received
#
#   In-args:   
#       pararr:   array with function parameters 
#       xarr:  array with values where function should be calculate
#
#   Out-args:
#       yarr:  array of values of the function at values xarr 
#       
class gaussmodel:
    def get_description(self):
        return "Gauss function"

    def get_param_names(self):
        return "nada"
        
    def __call__(self, pararr, xarr):
        dummy=2.3548200450309493*(xarr-pararr[3])/pararr[4]
        return pararr[0] + pararr[1] * xarr + pararr[2] * self.__exp(-0.5 * dummy * dummy)

    def __exp(self, xarr):
        return np.exp(xarr*np.less(np.abs(xarr),250))-1.0*np.greater_equal(np.abs(xarr),250)

def parabola(params, xx):
    return params[0]+params[1]*xx+params[2]*xx*xx

def test(npoints):

    import time

    from FunctionModels import GaussianModel, ParabolicModel

    xx = np.arange(npoints); xx.shape = (npoints,1)

    #func = GaussModel()
    #yy = func([10.5,2,1000.0,20.,15],xx); yy.shape = (npoints,1)
    #parameters = [0.0, 1.0, 900.0, 25., 10]
    #pars = func.estimate_parameters()

    func = ParabolicModel()
    yy = func([0,4,6],xx); yy.shape = (npoints,1)
    pars = func.estimate_parameters()
    pars = [0, 2.0, 3.0]

    sy = np.sqrt(abs(yy)); sy.shape = (npoints,1)

    data = np.concatenate((xx, yy, sy),1)

    stime = time.time()
    #fittedpar, chisq, sigmapar = LeastSquaresFit(func,pars,data,linear=func.is_lineal())
    fittedpar, chisq, sigmapar = LeastSquaresFit(func,pars,data, linear=True)
    etime = time.time()

    print("Took ",etime - stime, "seconds")
    print("Chi square  = ",chisq)
    print("Fitted pars = ",fittedpar)
    print("Sigma pars  = ",sigmapar)

if __name__ == "__main__":
  test(3000)
  #import profile
  #profile.run('test(10000)',"test")
  #import pstats
  #p=pstats.Stats("test")
  #p.strip_dirs().sort_stats(-1).print_stats()
