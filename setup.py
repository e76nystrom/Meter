#! /usr/bin/env python

# System imports
from distutils.core import *
from distutils      import sysconfig

# Third-party modules - we depend on numpy for everything
import numpy

# Obtain the numpy include directory.  This logic works across numpy versions.
try:
        numpy_include = numpy.get_include()
except AttributeError:
        numpy_include = numpy.get_numpy_include()

# cMeter extension module
_cMeter = Extension("_cMeter",
                    ["cMeter.i","cMeter.c"],
                    include_dirs = [numpy_include],
)

# NumyTypemapTests setup
setup(  name        = "cMeter function",
        description = "cMeter c functions for meter reading",
        author      = "Eric Nystrom",
        version     = "1.0",
        ext_modules = [_cMeter]
)
