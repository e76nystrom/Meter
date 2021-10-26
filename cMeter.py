# This file was automatically generated by SWIG (http://www.swig.org).
# Version 4.0.1
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
if _swig_python_version_info < (2, 7, 0):
    raise RuntimeError("Python 2.7 or later required")

# Import the low-level C/C++ module
if __package__ or "." in __name__:
    from . import _cMeter
else:
    import _cMeter

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)


def _swig_setattr_nondynamic_instance_variable(set):
    def set_instance_attr(self, name, value):
        if name == "thisown":
            self.this.own(value)
        elif name == "this":
            set(self, name, value)
        elif hasattr(self, name) and isinstance(getattr(type(self), name), property):
            set(self, name, value)
        else:
            raise AttributeError("You cannot add instance attributes to %s" % self)
    return set_instance_attr


def _swig_setattr_nondynamic_class_variable(set):
    def set_class_attr(cls, name, value):
        if hasattr(cls, name) and not isinstance(getattr(cls, name), property):
            set(cls, name, value)
        else:
            raise AttributeError("You cannot add class attributes to %s" % cls)
    return set_class_attr


def _swig_add_metaclass(metaclass):
    """Class decorator for adding a metaclass to a SWIG wrapped class - a slimmed down version of six.add_metaclass"""
    def wrapper(cls):
        return metaclass(cls.__name__, cls.__bases__, cls.__dict__.copy())
    return wrapper


class _SwigNonDynamicMeta(type):
    """Meta class to enforce nondynamic attributes (no new attributes) for a class"""
    __setattr__ = _swig_setattr_nondynamic_class_variable(type.__setattr__)



def piInit():
    return _cMeter.piInit()

def setRef(array, w, h):
    return _cMeter.setRef(array, w, h)

def setTarget(array, w, h):
    return _cMeter.setTarget(array, w, h)

def setSize(width, height):
    return _cMeter.setSize(width, height)

def setRows(top, bottom):
    return _cMeter.setRows(top, bottom)

def setColumns(left, right):
    return _cMeter.setColumns(left, right)

def getRows():
    return _cMeter.getRows()

def getColumns():
    return _cMeter.getColumns()

def getSize():
    return _cMeter.getSize()

def printShape():
    return _cMeter.printShape()

def getSegColumn(segCol, index):
    return _cMeter.getSegColumn(segCol, index)

def setDigitCol(strCol, endCol, index, n):
    return _cMeter.setDigitCol(strCol, endCol, index, n)

def setSegRows(segRows, index):
    return _cMeter.setSegRows(segRows, index)

def setDirRows(dirStart, dirEnd, index):
    return _cMeter.setDirRows(dirStart, dirEnd, index)

def getDigitCol(index, n):
    return _cMeter.getDigitCol(index, n)

def getSegRows(segRows, index):
    return _cMeter.getSegRows(segRows, index)

def getDirRows(index):
    return _cMeter.getDirRows(index)

def prtDigDat(index):
    return _cMeter.prtDigDat(index)

def prtDigDatC(index):
    return _cMeter.prtDigDatC(index)

def printData():
    return _cMeter.printData()

def targetUpdate():
    return _cMeter.targetUpdate()

def targetBounds(array, w, upd):
    return _cMeter.targetBounds(array, w, upd)

def findRefSegments(array, w):
    return _cMeter.findRefSegments(array, w)

def loopInit():
    return _cMeter.loopInit()

def decodeInit():
    return _cMeter.decodeInit()

def readDisplay(array):
    return _cMeter.readDisplay(array)

def loopProcess(array):
    return _cMeter.loopProcess(array)

def inplace(invec):
    return _cMeter.inplace(invec)

def arrayTest(array, w, row, col):
    return _cMeter.arrayTest(array, w, row, col)

def getSumArray(sumArray, index):
    return _cMeter.getSumArray(sumArray, index)

def getDeltaArray(deltaArray, index):
    return _cMeter.getDeltaArray(deltaArray, index)

def getIndexArray(indexArray, index):
    return _cMeter.getIndexArray(indexArray, index)

cvar = _cMeter.cvar

