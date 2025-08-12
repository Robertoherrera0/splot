#******************************************************************************
#
#  @(#)allio_redirector.py	3.4  10/01/20 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2013,2014,2015,2016,2017,2018,2019,2020
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

# the following tries to catch all IO coming from libraries and system
# and not managed by the application. IO will be sent to temporary
# file and forgotten

from contextlib import contextmanager
try:
    from io import SEEK_SET
except:
    SEEK_SET = 0
import os
import sys
import ctypes
import tempfile
import platform

if platform.system() != "Windows":
    libc = ctypes.CDLL(None)
    
    # get pointers to C-level stdout and stderr
    if platform.system() == 'Darwin':
       c_stdout = ctypes.c_void_p.in_dll(libc,'__stdoutp')
       c_stderr = ctypes.c_void_p.in_dll(libc,'__stderrp')
    else:  # Linux
       c_stdout = ctypes.c_void_p.in_dll(libc,'stdout')
       c_stderr = ctypes.c_void_p.in_dll(libc,'stderr')
    
    # In case null logging. this function will redirect ALL
    # stderr output (including C-level stderr) to /dev/null
    @contextmanager
    def allio_redirector(stream):
        original_stderr_fd = sys.stderr.fileno()
        original_stdout_fd = sys.stdout.fileno()
    
        def _redirect_stdout(to_fd):
            libc.fflush(c_stdout)
            sys.stdout.close()
            os.dup2(to_fd, original_stdout_fd)
            sys.stdout = os.fdopen(original_stdout_fd, 'w')
    
        def _redirect_stderr(to_fd):
            libc.fflush(c_stderr)
            sys.stderr.close()
            os.dup2(to_fd, original_stderr_fd)
            sys.stderr = os.fdopen(original_stderr_fd, 'w')
    
        saved_stdout_fd = os.dup(original_stdout_fd)
        saved_stderr_fd = os.dup(original_stderr_fd)
    
        try:
            tfile = tempfile.TemporaryFile(mode='w+')
            _redirect_stdout(tfile.fileno())
            _redirect_stderr(tfile.fileno())

            yield

            _redirect_stdout(saved_stdout_fd)
            _redirect_stderr(saved_stderr_fd)
        
            tfile.flush()
            tfile.seek(0, SEEK_SET)

            if sys.version_info.major == 3:
                stream.write(tfile.read())
            else:
                stream.write(unicode(tfile.read()))
        finally:
            tfile.close()
            os.close(saved_stdout_fd)
            os.close(saved_stderr_fd)
else:
    def allio_redirector(stream):
        pass

