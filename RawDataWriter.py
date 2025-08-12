#******************************************************************************
#
#  @(#)RawDataWriter.py	3.1  12/12/17 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2017
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

class RawDataWriter:
    def __init__(self):
        pass

    def write(self, filename, data, labels=None, fmt="%.6f", delimiter=" ", mode="w"):
        fd = open(filename, mode=mode)

        header, d = self._prepare_data(data,labels, delimiter)
        np.savetxt(filename, d, fmt=fmt, delimiter=delimiter, header=header)

    def _prepare_data(self, data, labels, delimiter):

        nb_labels = None

        if labels and type(labels) is list:
            nb_labels = len(labels)
            header = delimiter.join(labels)

        if type(data) is list:  # list of data lists
            nb_cols = len(data)
            d = np.array(data).transpose()
        elif type(data) is np.ndarray:  # numpy array
            shape = data.shape
            if len(shape) != 2:
                raise(Exception("Cannot understand array type for saving. Cannot write data"))
  
            nb_cols = shape[1]
            d = data
        else:
            raise(Exception("Cannot understand data type for saving. Cannot write data"))
        
        if nb_labels and nb_cols != nb_labels:
            raise(Exception("Wrong number of labels/columns. Cannot write data"))

        return header,d

def test():
    c1 = range(7)
    c2 = [c*8 for c in c1]
    c3 = [c/10.0 for c in c1]

    writer = RawDataWriter()
    writer.write("/tmp/writer_col3.txt", [c1,c2,c3], delimiter="\t",labels=["Theta","Det", "Mon"])

    arr = np.array([c1,c2,c3]).transpose()
    writer.write("/tmp/writer_array.txt", arr, delimiter=", ",labels=["Theta","Det", "Mon"])


if __name__ == '__main__':
    test()
