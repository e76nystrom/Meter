#!/cygdrive/c/Python39/python.exe
#******************************************************************************

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageOps, ImageColor
from time import sleep
from platform import system

import urllib.request
import socket
import io
from datetime import datetime
from pytz import timezone
from http.client import IncompleteRead
from urllib.error import URLError

# from collections import namedtuple

LINUX = system() == 'Linux'
R_PI = False
if LINUX:
    R_PI = os.uname().machine.startswith('arm')

URL = "http://192.168.42.70/capture"

socket.setdefaulttimeout(2)

if LINUX:
    print("Linux")
    import cMeter as cm
    cm.decodeInit()
# else:
#     sys.path.append("C:\\Development\\Python\\Meter\\x64\\Release\\")
#     print('\n'.join(sys.path))
#     import cMeter as cm
#     cm.decodeInit()
#     LINUX = True

WHITE_FILL = 255
BLACK_FILL = 0
GRAY_FILL  = 192

MAX_PIXEL = 255

TOP_SEG = 0.3
BOTTOM_SEG = 0.6
MARK_HEIGHT = 0.375

DIGIT_THRESHOLD = 100
SUM_THRESHOLD = 90
DELTA_OFS = 5

TARGET_COLUMN_RANGE = 0.05
TARGET_ROW_RANGE = 0.20

MAX_COL = 24
INITIAL_COLUMN_INDEX = 3
DIGIT_COLUMNS = 3

MAX_DIGITS = 6
SEG_ROWS = 6
SEGMENTS = 7

FALSE = 0
TRUE = 1

dirConv = \
(
  99,				# 0x00
  99,                           # 0x01
  99,                           # 0x02
  0,                            # 0x03
  99,                           # 0x04
  99,                           # 0x05
  1,                            # 0x06
  99,				# 0x07
  99,				# 0x08
  99,				# 0x09
  99,				# 0x0A
  99,				# 0x0B
  2,				# 0x0C
  99,				# 0x0D
  99,				# 0x0E
  99,				# 0x0F
  99,				# 0x10
  99,				# 0x11
  99,				# 0x12
  99,				# 0x13
  99,				# 0x14
  99,				# 0x15
  99,				# 0x16
  99,				# 0x17
  3,				# 0x18
  99,				# 0x19
  99,				# 0x1A
  99,				# 0x1B
  99,				# 0x1C
  99,				# 0x1D
  99,				# 0x1E
  99,				# 0x1F
  99,				# 0x20
  5,				# 0x21
  99,                           # 0x22
  99,                           # 0x23
  99,                           # 0x24
  99,                           # 0x25
  99,                           # 0x26
  99,				# 0x27
  99,				# 0x28
  99,				# 0x29
  99,				# 0x2A
  99,				# 0x2B
  99,				# 0x2C
  99,				# 0x2D
  99,				# 0x2E
  99,				# 0x2F
  4,				# 0x30
)

tz = timezone("America/New_York")

def timeStr():
    now = datetime.now(tz=tz)
    return(now.strftime("%b_%d_%Y_%H-%M-%S"))

DUMP_COL = 16

def dumpBuf(array):
    col = 0;
    for i in range(len(array)):
        if col == 0:
            print("%3d  " % (i), end="")
        print(" %4d" % (array[i]), end="")
        col += 1
        if col == DUMP_COL:
            col = 0
            print()
    if col != 0:
        print()

def coord(loc, w):
    row = loc // w
    col = loc % w
    return (col, row)


def cmGetData():
    cmShape = LcdShape()
    cmShape.cmGet()

    cmData = []
    for index in range(MAX_DIGITS):
        data = DigitData(0, 0)
        cmData.append(data)
        data.cmGet(index)
    return (cmShape, cmData)

class LcdShape():
    def __init__(self, array=None, dbg=False):
        self.dbg = dbg
        if array is not None:
            self.rArray = array
            self.rArrayH= len(array)
            self.rArrayW = len(array[0])
            if self.dbg:
                print("setRef w %3d h %3d" % (self.rArrayW, self.rArrayH))

        self.tArray = None
        self.tArrayW = 0
        self.tArrayH = 0

        self.top = 0
        self.bottom = 0

        self.width = 0
        self.height = 0

        self.topRow = 0
        self.botRow = 0

        self.left = 0
        self.right = 0

    def setTarget(self, array):
        self.tArray = array
        self.tArrayH = len(array)
        self.tArrayW = len(array[0])
        if self.dbg:
            print("setTarg w %3d h %3d" % (self.tArrayW, self.tArrayH))

    def setRows(self, top, bottom, prt=True):
        self.top = top
        self.bottom = bottom
        if prt and self.dbg:
            print("setRows t %3d b %3d" % (self.top, self.bottom))

    def setColumns(self, left, right, prt=True):
        self.left = left
        self.right = right
        if prt and self.dbg:
            print("setCols l %3d r %3d" % (self.left, self.right))

    def setSize(self, prt=True):
        self.height = h = (self.bottom - self.top) + 1
        self.width = (self.right - self.left) + 1
        self.topRow = int(TOP_SEG * h)
        self.botRow = int(BOTTOM_SEG * h)
        if prt and self.dbg:
            print("setSize w %3d h %3d tr %3d br %3d" % \
                  (self.width, self.height, self.topRow, self.botRow))

    def set(self, rows, cols):
        print("lcdShape set")
        self.print()
        (l, r) = rows
        self.setRows(l, r, False)
        (t, b) = cols
        self.setColumns(t, b, False)
        self.setSize(False)
        self.print()

    def cmSet(self):
        cm.setRef(self.rArray.ravel(), len(self.rArray[0]), \
                  len(self.rArray))
        cm.setSize(self.width, self.height)
        cm.setRows(self.top, self.bottom)
        cm.setColumns(self.left, self.right)

    def cmGet(self):
        (self.top, self.bottom) = cm.getRows()
        (self.left, self.right) = cm.getColumns()
        (self.height, self.width, self.topRow, self.botRow) = cm.getSize()

    def print(self):
        print("p t %3d b %3d l %3d r %3d w %3d h %3d s %5d tr %3d br %3d" % \
              (self.top, self.bottom, self.left, self.right, \
	       self.width, self.height, self.width * self.height, \
               self.topRow, self.botRow))

class DigitData():
    def __init__(self, strCol, endCol):
        self.strCol = [0, 0]
        self.endCol = [0, 0]
        self.col = [0, 0]
        self.colRange = [0, 0]
        self.setCol(strCol, endCol, 0)

        self.segRows = None
        self.topRow = 0
        self.botRow = 0
        self.rowRange = 0
        self.dirStart = 0
        self.dirEnd = 0

        self.py = None
        self.segData = None

    def setCol(self, strCol, endCol, index):
        self.strCol[index] = strCol
        self.endCol[index] = endCol
        self.col[index] = (strCol + endCol) // 2
        self.colRange[index] = (endCol - strCol) // 2

    def setSegRows(self, segRows):
        self.segRows = segRows
        self.topRow = (segRows[1] + segRows[2]) // 2
        self.botRow = (segRows[3] + segRows[4]) // 2
        self.rowRange = (self.topRow - segRows[1] + \
                         int(1.5 * (segRows[1] - segRows[0])))
        self.rrT = self.topRow - segRows[0];
        self.rrC = segRows[3] - self.topRow;
        self.rrB = segRows[5] - self.botRow;

    def setDirRows(self, dirStart, dirEnd):
        self.dirStart = dirStart
        self.dirEnd = dirEnd

    def setSegData(self, n, segData):
        if self.segData is None:
            self.segData = [None for i in range(SEGMENTS)]
        self.segData[n] = segData

    def cmGet(self, index):
        for i in range(2):
            (strCol, endCol) = cm.getDigitCol(index, i)
            self.setCol(strCol, endCol, i)
        segRows = np.empty(SEG_ROWS, np.int32)
        cm.getSegRows(segRows, index)
        self.setSegRows(list(segRows))
        (dirStart, dirEnd) = cm.getDirRows(index)
        self.setDirRows(dirStart, dirEnd)

    def print(self):
        print("st %3d %3d en %3d %3d seg %2d %2d %2d dir %2d %2d " % \
	      (self.strCol[0], self.strCol[1], \
	       self.endCol[0], self.endCol[1], \
	       self.segRows[0], self.segRows[1], self.segRows[2], \
	       self.dirStart, self.dirEnd), end="")

    def printC(self):
        print("col %3d %3d cr %2d %2d tr %2d br %2d rr %2d dir %2d %2d" % \
	      (self.col[0], self.col[1], self.colRange[0], self.colRange[1],
	       self.topRow, self.botRow, self.rowRange, \
	       self.dirStart, self.dirEnd))

def shapeCopy():
    shape = LcdShape()
    shape.cmGet()
    return shape

def digitDataCopy():
    tmpData = []
    for index in range(MAX_DIGITS):
        data = DigitData(0, 0)
        tmpData.append(data)
        data.cmGet(index)
    return tmpData

class Meter():
    def __init__(self):
        self.plot = [False for element in range(9 + 1)]

        self.save = False           # save figure

        self.dbg = [False for element in range(5 + 1)]

        self.draw = False           # drawing on images
        self.capture = False
        self.loop = False

        self.update = False
        self.cDbg0 = False
        self.cDbg1 = False
        self.cDbg2 = False

        self.refFile = None
        self.targetFile = None

        # self.refGray = None
        self.refArray = None
        self.rowArray = None
        self.targetImage = None
        # self.targetGray = None

        self.initLoopVars()

    def initLoopVars(self):
        self.meterVal = [888888, 0, 0, 0]
        self.lastVal = 0
        self.lastTmp = -1
        self.check = 0
        self.lastDir = 99
        self.sync = False
        self.ctr = 0
        self.dirSign = 0
        self.fwd = 0
        self.rev = 0
        self.net = 0
        self.errCtr = 0
        self.arrayDiffs = 0
        self.dirError = 0
        self.readError = 0

        self.drwUpdCnt = 0
        self.drwErrCnt = 0
        self.drwDbgCnt = 0
        self.segDrwCnt = 0

        self.maxUpdCnt = 100
        self.maxErrCnt = 100
        self.maxDbgCnt = 100
        self.maxSegCnt = 100

    def setup(self):
        n = 1
        while True:
            if n >= len(sys.argv):
                break
            val = sys.argv[n]
            if val.startswith('-'):
                val = val[1:]
                ch = val[0]
                if ch == 'p':
                    val = int(val[1:])
                    if val == 1:
                        self.plot[1] = True # row histogram
                    elif val == 2:
                        self.plot[2] = True # row sum array
                    elif val == 3:
                        self.plot[3] = True # upper and lower row
                    elif val == 4:
                        self.plot[4] = True # reference rows
                    elif val == 5:
                        self.plot[5] = True # digit columns
                    elif val == 6:
                        self.plot[6] = True # direction
                    elif val == 7:
                        self.plot[7] = True # target center column
                    elif val == 8:
                        self.plot[8] = True # target bounds
                    elif val == 9:
                        self.plot[9] = True # target bounds
                elif ch == 'd':
                    val = int(val[1:])
                    if val == 0:
                        self.dbg[0] = True # general debug
                    elif val == 1:
                        self.dbg[1] = True # top and bottom
                    elif val == 2:
                        self.dbg[2] = True # right and left
                    elif val == 3:
                        self.dbg[3] = True
                    elif val == 4:
                        self.dbg[4] = True # draw target updated
                    elif val == 5:
                        self.dbg[5] = True # draw on error
                elif ch == 'C':
                    val = int(val[1:])
                    if val == 0:
                        self.cDbg0 = True
                    elif val == 1:
                        self.cDbg1 = True
                    elif val == 2:
                        self.cDbg2 = True
                elif ch == 'c':
                    self.capture = True
                elif ch == 'r':
                    self.draw = True
                elif ch == 'l':
                    self.loop = True
                elif ch == 's':
                    self.save = True
                elif  ch == 'u':
                    print("udpate True")
                    self.update = True
            elif val == "?":
                print("meter.py [-option] [reference] [target]\n"\
                      "p[1-8] - plot\n"\
                      "d[0-3] - python debug\n"\
                      "C[0-2] - c debug\n"\
                      "c - capture one target\n"\
                      "r - draw\n"\
                      "l - loop\n"\
                      "s - save plots to file\n"\
                      "u - update reference\n"\
                      )
            elif self.refFile is None:
                self.refFile = val
            elif self.targetFile is None:
                self.targetFile = val
            n += 1

        if self.refFile is None:
            self.refFile = "ref.jpg"

        if LINUX:
            self.save = True

    def openRef(self):
        self.refImage = Image.open(self.refFile)
        refGray = ImageOps.grayscale(self.refImage)
        #refImage.close()
        self.refArray = np.asarray(refGray)
        if self.dbg[0]:
            print(len(self.refArray), len(self.refArray[0]),
                  self.refArray[0][0])

        self.rowArray = np.rint(self.refArray.sum(axis=1) / \
                                len(self.refArray[0])).astype(int)

    def histogram(self):
        if self.plot[1]:
            histogram = np.zeros(255)
            for val in self.rowArray:
                histogram[val] += 1
            plt.plot(histogram)
            plt.title("Row Histogram")
            if self.save:
                plt.gcf().savefig("plot1.png")
            else:
                plt.show()
            plt.close()

    def verticalBounds(self, lcdShape):
        if self.dbg[1]:
            print("verticalBounds")
        deltaArray = [0 for i in range(len(self.rowArray))]
        minVal = MAX_PIXEL
        minRow = 0
        maxVal = -MAX_PIXEL
        maxRow = 0
        rowLen = len(self.rowArray)
        rowLast = 0
        skip = 0
        for row in range(DELTA_OFS, rowLen):
            delta = self.rowArray[row] - self.rowArray[rowLast]
            deltaArray[row] = delta
            # print("%3d delta %3d" % (row, delta), end="")
            if delta < minVal:
                # print(" < delta %4d minVal %4d" % (delta, minVal), end="")
                minVal = delta
                minRow = row
                skip = 10
            if skip == 0:
                if delta > maxVal:
                    # print(" > delta %4d maxVal %4d" % \
                    #       (delta, maxVal), end="")
                    maxVal = delta
                    maxRow = row
            else:
                skip -= 1
            rowLast += 1
            # print()
        print("r %3d l %3d" % (minRow, maxRow))
        lcdShape.setRows(minRow, maxRow)

        if self.plot[2]:
            fig, axs = plt.subplots(2, sharex=True)
            fig.suptitle("Plot 2 verticalBounds")
            fig.set_figwidth(3 * fig.get_figwidth())
            fig.set_figheight(2 * fig.get_figheight())

            axis = axs[0]
            axis.plot(self.rowArray)
            y = self.rowArray[minRow]
            axis.plot((minRow, minRow), (y - 10, y + 50))
            y = self.rowArray[maxRow]
            axis.plot((maxRow, maxRow), (y - 10, y + 50))
            axis.set_title("Row Array Top %3d Bottom %3d" % (minRow, maxRow))

            axis = axs[1]
            axis.plot(deltaArray)
            axis.plot((minRow, minRow), (0, minVal))
            axis.plot((maxRow, maxRow), (0, maxVal))
            axis.set_title("Delta Array")
            if self.save:
                fig.savefig("plot2.png")
            else:
                plt.show()
            plt.close()

    def horizontalBounds(self, lcdShape):
        if self.plot[3]:
            fig, axs = plt.subplots(4, sharex=True)
            fig.suptitle("Plot 3 horizontalBounds")
            fig.set_figwidth(4 * fig.get_figwidth())
            fig.set_figheight(2 * fig.get_figheight())
            n = 0

        refMaxCol = len(self.refArray[0])
        refMidCol = refMaxCol // 2
        for row in (lcdShape.top, lcdShape.bottom - DELTA_OFS):
            sumArray = [0 for i in range(refMaxCol)]
            for r in range(row, row + DELTA_OFS):
                for col, pixel in enumerate(self.refArray[row]):
                    sumArray[col] += pixel
            for col in range(refMaxCol):
                sumArray[col] //= DELTA_OFS

            deltaArray = [0 for i in range(refMaxCol)]
            minVal = MAX_PIXEL
            minCol = 0
            maxVal = -MAX_PIXEL
            maxCol = 0
            colLast = 0
            for col in range(DELTA_OFS, refMaxCol):
                delta = sumArray[col] - sumArray[colLast]
                deltaArray[col] = delta
                if col < refMidCol:
                    if delta < minVal:
                        minVal = delta
                        minCol = col
                else:
                    if delta > maxVal:
                        maxVal = delta
                        maxCol = colLast
                colLast += 1

            if self.plot[3]:
                axs[n].plot(sumArray)
                axs[n].set_title("Row %3d Left %3d Right %3d" % \
                                 (row, minCol, maxCol))
                axs[n].plot((minCol, minCol), (0, MAX_PIXEL))
                axs[n].plot((maxCol, maxCol), (0, MAX_PIXEL))
                n += 1
                axs[n].plot(deltaArray)
                axs[n].plot((minCol, minCol), (0, minVal))
                axs[n].plot((maxCol, maxCol), (0, maxVal))
                n+= 1

            print("row %3d l %3d r %3d" % (row, minCol, maxCol))

        lcdShape.setColumns(minCol, maxCol)

        if self.plot[3]:
            if self.save:
                plt.gcf().savefig("plot3.png")
            else:
                plt.show()
                
    def drawPlot8(self, array, lcdShape, ttl="8"):
        (cr, lc, rc, rr, tr, br) = self.tbVars(lcdShape)

        fig, axs = plt.subplots(3)
        fig.suptitle("Plot " + ttl + " targetBounds")
        fig.set_figwidth(2 * fig.get_figwidth())
        fig.set_figheight(3 * fig.get_figheight())
        
        for i, r0 in enumerate((tr, br)):
            axs[i].plot(array[r0])
            axs[i].set_title("row %3d" % (r0))

        x = []
        y = []
        (r0, r1) = (tr, br)
        tRows = br - tr + 1
        for cs in (lc, rc):
            for col in range(cs - cr, cs + cr):
                cSum = 0
                for row in range(tr, br):
                    cSum += int(array[row][col])
                cSum //= tRows
                x.append(col)
                y.append(cSum)

        axs[2].plot(x, y)
        axs[2].set_title("Column Sums %3d %3d" % (lc, rc))
        axs[2].plot((lc, lc), (0, MAX_PIXEL))
        axs[2].plot((rc, rc), (0, MAX_PIXEL))
                
        if self.save:
            fig.savefig("plot" + ttl + ".png")
        else:
            plt.show()

    def drawPlot9(self, array, lcdShape, temps, ttl="9"):
        print("plot%s" % (ttl))
        (cr, lc, rc, rr, tr, br) = self.tbVars(lcdShape)

        fig, axs = plt.subplots(2, 4)
        fig.suptitle("Plot " + ttl + " targetBounds")
        fig.set_figwidth(4 * fig.get_figwidth())
        fig.set_figheight(3 * fig.get_figheight())
        
        for i, row in ((0, tr), (1, br)):
            (rowArray, sumArray, deltaArray) = temps[i]
            a = axs[0][i]
            a.set_title("Row %3d" % (row))
            a.plot(rowArray, sumArray)
            a.plot((row, row), (0, MAX_PIXEL))

            a = axs[1][i]
            a.plot(rowArray, deltaArray)
            a.plot((row, row), (-50, 50))

        for i, col in ((2, lc), (3, rc)):
            (colArray, sumArray, deltaArray) = temps[i]
            a = axs[0][i]
            a.set_title("Col %3d" % (col))
            a.plot(colArray, sumArray)
            a.plot((col, col), (0, MAX_PIXEL))
            
            a = axs[1][i]
            a.plot(colArray, deltaArray)
            a.plot((col, col), (-50, 50))
                
        if self.save:
            fig.savefig("plot" + ttl + ".png")
        else:
            plt.show()

    def tbDraw(self, array, lcdShape, rows, cols):
        (cr, lc, rc, rr, tr, br) = self.tbVars(lcdShape)
        rgbImage = self.rgbImage(array)
        rgbDraw = ImageDraw.Draw(rgbImage)
        d = rgbDraw.line
        fill = ImageColor.getrgb("red")
        d(((lc - cr, tr - rr), (rc + cr, tr - rr),
           (rc + cr, br + rr), (lc - cr, br + rr),
           (lc - cr, tr - rr)), fill=ImageColor.getrgb("red"))

        if (len(cols) == 2) and (len(rows) == 2):
            (t, b) = rows
            (l, r) = cols
            d(((l, t), (r, t), (r, b), (l, b),
               (l, t)), fill=ImageColor.getrgb("yellow"))

        rgbImage.save("targetDraw1.png", "PNG")

    def tbVars(self, lcdShape):
        cr = int(lcdShape.width * TARGET_COLUMN_RANGE)
        lc = lcdShape.left
        rc = lcdShape.right
        rr = int(lcdShape.height * TARGET_ROW_RANGE)
        tr = lcdShape.top
        br = lcdShape.bottom
        return (cr, lc, rc, rr, tr, br)

    def targetBounds(self, array, lcdShape, upd=True):
        (cr, lc, rc, rr, tr, br) = self.tbVars(lcdShape)

        if self.dbg[0]:
            print("\nmeter targetBounds w %3d" % (lcdShape.tArrayW))
            print("t %3d b %3d l %3d r %3d rr %3d cr %3d threshold %3d" % \
                  (tr, br, lc, rc, rr, cr, SUM_THRESHOLD))

        rows = [0, 0]
        temps = []
        top = True
        strVal = MAX_PIXEL
        endVal = MAX_PIXEL
        for r in (tr, br):
            if self.dbg[2]:
                print()
            sumArray = [0 for i in range(2 * rr + DELTA_OFS)]
            deltaArray = [0 for i in range(2 * rr + DELTA_OFS)]
            rowArray = [0 for i in range(2 * rr + DELTA_OFS)]
            i = 0
            for row in range(r - rr - DELTA_OFS, r + rr):
                rSum = 0
                for col in range(lc - cr, rc + cr):
                    rSum += array[row][col]
                sumArray[i] = int(rSum / (rc - lc + 2 * cr))
                rowArray[i] = row
                i += 1
                
            i = DELTA_OFS
            for row in range(r - rr, r + rr):
                delta = sumArray[i] - sumArray[i - DELTA_OFS]
                deltaArray[i] = delta
                if top:
                    if delta < strVal:
                        strVal = delta
                        rows[0] = row
                        if self.dbg[2]:
                            print("<%2d row %3d sum %3d delta %3d" % \
                                  (i, row, sumArray[i], delta))
                else:
                    if delta < endVal:
                        endVal = delta
                        rows[1] = row
                        if self.dbg[2]:
                            print(">%2d row %3d sum %3d delta %3d" % \
                                  (i, row, sumArray[i], delta))
                i += 1
            temps.append((rowArray, sumArray, deltaArray))
            top = False

        cols = [0, 0]
        left = True
        strVal = MAX_PIXEL
        endVal = -MAX_PIXEL
        for c in (lc, rc):
            if self.dbg[2]:
                print()
            sumArray = [0 for i in range(2 * cr + DELTA_OFS)]
            deltaArray = [0 for i in range(2 * cr + DELTA_OFS)]
            colArray = [0 for i in range(2 * cr + DELTA_OFS)]
            i = 0
            for col in range(c - cr - DELTA_OFS, c + cr):
                rSum = 0
                for row in range(rows[0], rows[1]):
                    rSum += array[row][col]
                sumArray[i] = int(rSum / (rows[1] - rows[0]))
                colArray[i] = col
                i += 1
                
            i = DELTA_OFS
            for col in range(c - cr, c + cr):
                delta = sumArray[i] - sumArray[i - DELTA_OFS]
                deltaArray[i] = delta
                if left:
                    if delta < strVal:
                        strVal = delta
                        cols[0] = col
                        if self.dbg[2]:
                            print("<%2d col %3d sum %3d delta %3d" % \
                                  (i, c, sumArray[i], delta))
                else:
                    if delta > endVal:
                        endVal = delta
                        cols[1] = col - DELTA_OFS
                        if self.dbg[2]:
                            print(">%2d col %3d sum %3d delta %3d" % \
                                  (i, c, sumArray[i], delta))
                i += 1
            temps.append((colArray, sumArray, deltaArray))
            left = False

        if upd:
            lcdShape.set(rows, cols)

        if self.dbg[0]:
            print("t %3d b %3d l %3d r %3d" % \
                  (rows[0], rows[1], cols[0], cols[1]))

        if self.plot[8]:
            self.drawPlot8(array, lcdShape)

        if self.plot[9]:
            self.drawPlot9(array, lcdShape, temps)

        if self.draw:
            self.tbDraw(array, lcdShape, rows, cols)
            
        return (rows, cols)

    def cropRef(self, lcdShape):
        # if self.draw:
        #     self.refGray.save("ref.png", "PNG")
        #     drawImg = ImageDraw.Draw(self.refGray)
        #     l = lcdShape.left
        #     r = lcdShape.right
        #     t = lcdShape.top
        #     b = lcdShape.bottom
        #     drawImg.line(((l, t), (r, t)), fill=WHITE_FILL)
        #     drawImg.line(((r, t), (r, b)), fill=WHITE_FILL)
        #     drawImg.line(((r, b), (l, b)), fill=WHITE_FILL)
        #     drawImg.line(((l, b), (l, t)), fill=WHITE_FILL)

        if self.dbg[0]:
            print("width %3d height %3d pixels %5d, top %3d bottom %3d" % \
                  (lcdShape.width, lcdShape.height, \
                   lcdShape.width * lcdShape.height, \
                   lcdShape.topRow, lcdShape.botRow))
        return(lcdShape)

    def drawPlot4(self, array, lcdShape, seg, digitData, avgRow, ttl="4"):
        x0 = lcdShape.right
        y0 = lcdShape.top
        l = x0 - lcdShape.width
        r = x0
        t = lcdShape.topRow + y0
        b = lcdShape.botRow + y0

        fig, axs = plt.subplots(2, sharex=True)
        title = "Plot "  + ttl + " findRefSegments Horizontal" + \
            (" Linux" if LINUX else "")
        fig.suptitle(title)
        fig.set_figwidth(3 * fig.get_figwidth())
        fig.set_figheight(2 * fig.get_figheight())

        for i, rowNum in enumerate((t, b)):
            if avgRow == None:
                row = self.refArray[rowNum]
            else:
                row = avgRow[i]
            axs[i].plot(row[lcdShape.left:x0])
            axs[i].set_title("Ref Row %d start %d end %d" % (rowNum, x0, l))
            axs[i].plot([0, lcdShape.width], \
                        [DIGIT_THRESHOLD, DIGIT_THRESHOLD])

            segColumn = seg[i]

            xVal = []
            yVal = []
            lo = 0
            hi = DIGIT_THRESHOLD - 5
            w = lcdShape.width
            xVal.append(w)
            val = hi
            yVal.append(val)
            for col in segColumn:
                xVal.append(w - col)
                yVal.append(val)
                val = hi if val == lo else lo
                xVal.append(w - col)
                yVal.append(val)
            axs[i].plot(xVal, yVal)

            w = lcdShape.width
            xVal = []
            yVal = []
            lo = DIGIT_THRESHOLD + 5
            hi = 255
            xVal.append(w)
            yVal.append(lo)
            for data in digitData:
                xVal.append(w - data.strCol[i])
                yVal.append(lo)
                xVal.append(w - data.strCol[i])
                yVal.append(hi)
                xVal.append(w - data.endCol[i])
                yVal.append(hi)
                xVal.append(w - data.endCol[i])
                yVal.append(lo)
            axs[i].plot(xVal, yVal)

        if self.save:
            fig.savefig("plot" + ttl + ".png")
        else:
            plt.show()

    def drawPlot5(self, array, lcdShape, digitData, ttl="5"):
        x0 = lcdShape.right

        fig, axs = plt.subplots(3, 2, sharex=True)
        title = "Plot " + ttl +  " findRefSegments Vertical" + \
            (" Linux" if LINUX else "")
        fig.suptitle(title)
        axs = list(np.concatenate(axs).flat)
        fig.set_figheight(2 * fig.get_figheight())
        fig.set_figwidth(2 * fig.get_figwidth())

        for n, data in enumerate(digitData):
            stCol = data.strCol[0]
            enCol = data.endCol[0]
            centerCol = data.col[0]

            tmpCol = array[:,x0 - centerCol]
            axs[n].plot(tmpCol[lcdShape.top:lcdShape.bottom])
            axs[n].set_title("%d Column %d" % (n, centerCol))

            for segRow in data.segRows:
                axs[n].plot([segRow, segRow], \
                            [0, DIGIT_THRESHOLD])

            axs[n].plot([data.dirStart, data.dirStart],
                        [DIGIT_THRESHOLD, MAX_PIXEL])
            axs[n].plot([data.dirEnd, data.dirEnd],
                        [DIGIT_THRESHOLD, MAX_PIXEL])

        if self.save:
            fig.savefig("plot" + ttl + ".png")
        else:
            plt.show()

    def refDraw(self, array, lcdShape, seg, digitData, name="refDraw"):
        x0 = lcdShape.right
        y0 = lcdShape.top
        l = x0 - lcdShape.width
        r = x0
        t = lcdShape.topRow + y0
        b = lcdShape.botRow + y0

        fill0 = ImageColor.getrgb("red")
        fill1 = ImageColor.getrgb("blue")
        fill2 = ImageColor.getrgb("green")
        fill3 = ImageColor.getrgb("yellow")

        image = self.rgbImage(array)
        refDraw = image.copy()
        d = ImageDraw.Draw(refDraw).line
        d(((l, t), (r, t)), fill=fill0)
        d(((l, b), (r, b)), fill=fill0)
        refDraw.save(name + "0.png", "PNG")

        refDraw = image.copy()
        d = ImageDraw.Draw(refDraw).line

        h = lcdShape.height
        mark = int(h * MARK_HEIGHT)
        for i, (ms, me) in enumerate(((0, mark), (mark, h))):
            segColumn = seg[i]
            for j, col in enumerate(segColumn):
                fill = fill1 if (j & 1) == 0 else fill0
                d(((x0 - col, ms + y0), \
                   (x0 - col, me + y0)), fill=fill)

            for dig, data in enumerate(digitData):
                st = data.strCol[i]
                en = data.endCol[i]

                if (ms == 0):
                    d(((x0 - st, ms + y0), \
                       (x0 - st, me + y0)), fill=fill2)
                    if dig == MAX_DIGITS - 1:
                        d(((x0 - en, ms + y0), \
                           (x0 - en, me+ y0)), fill=fill2)

        refDraw.save(name + "1.png", "PNG")

        refDraw = image
        d = ImageDraw.Draw(refDraw).line

        for dig, data in enumerate(digitData):
            segRows = data.segRows
            st = data.strCol[i]
            en = data.endCol[i]
            centerCol = data.col[i]
            d(((x0 - centerCol, segRows[0] + y0), \
               (x0 - centerCol, segRows[-1] + y0)), fill=fill0)

            d(((x0 - centerCol+2, data.dirStart + y0), \
               (x0 - centerCol+2, data.dirEnd + y0)), fill=fill3)

            d(((x0 - st, segRows[0] + y0), \
               (x0 - st, segRows[2] + y0)), fill=fill1)
            d(((x0 - en, segRows[3] + y0), \
               (x0 - en, segRows[5]+ y0)), fill=fill2)

            d(((x0 - st, data.topRow + y0), \
               (x0 - en, data.topRow + y0)), fill=fill0)
            d(((x0 - st, data.botRow + y0), \
               (x0 - en, data.botRow + y0)), fill=fill1)

            for seg, row in enumerate(segRows):
                fill = fill2 if ((seg ^ dig) & 1) == 0 else fill3
                d(((x0 - st, y0 + row), \
                   (x0 - en, y0 + row)), fill=fill)

        refDraw.save(name + "2.png", "PNG")

    def rowScan(self, rowNum, lcdShape):
        x0 = lcdShape.right
        if self.dbg[0]:
            print("rowScan %3d x0 %3d" % (rowNum, x0))
        negDelta = True
        segColumn = []
        # row = self.refArray[rowNum]
        # lastPixel = int(row[x0 - 2])

        avgPixel = [0 for i in range(len(self.refArray[rowNum]))]

        AVG_RANGE = 2
        AVG_SIZE = 2 * AVG_RANGE + 1
        SCAN_START = 3

        for j in range(rowNum - AVG_RANGE, rowNum + AVG_RANGE + 1):
            # print("row %d" % (j))
            row = self.refArray[j]
            for col in range(SCAN_START-1, lcdShape.width):
                avgPixel[x0 - col] += row[x0 - col]
                
        for col in range(SCAN_START-1, lcdShape.width):
            avgPixel[x0 - col] //= AVG_SIZE

        # dumpBuf(avgPixel)
        # print()

        lastPixel = int(avgPixel[x0 - (SCAN_START - 1)])
        for col in range(SCAN_START, lcdShape.width):
            # pixel = int(row[x0 - col])
            pixel = avgPixel[x0 - col]

            # tmp = self.refArray[rowNum][x0 - col];
            # colCount = len(segColumn)
            # print("%3d index %3d avg %3d pixel %3d d %4d colCount %2d" %\
	    #       (col, x0-col, pixel, tmp, pixel-tmp, colCount));

            if self.dbg[0] and False:
                print("%3d %3d p %3d %s " % \
                      (col, x0-col, pixel, str(negDelta)[0]))
            if negDelta:
                if (pixel <= DIGIT_THRESHOLD and \
                    lastPixel >= DIGIT_THRESHOLD):
                    segColumn.append(col)
                    negDelta = False
            else:
                if (pixel >= DIGIT_THRESHOLD and \
                    lastPixel <= DIGIT_THRESHOLD):
                    segColumn.append(col)
                    negDelta = True
            lastPixel = pixel
            if len(segColumn) >= MAX_COL:
                break;
        self.avgPixel.append(avgPixel)
        return segColumn

    # find location of segments on the reference array
    def findRefSegments(self, lcdShape):
        x0 = lcdShape.right
        y0 = lcdShape.top
        l = x0 - lcdShape.width
        r = x0
        t = lcdShape.topRow + y0
        b = lcdShape.botRow + y0

        if self.dbg[0]:
            print("\npy findRefSegments w %3d x0 %3d y0 %3d\n" %\
                  (lcdShape.width, x0 , y0))

        index = 0
        digitData = []
        seg = []
        self.avgPixel = []
        for i, rowNum in enumerate((t, b)):
            if self.dbg[0]:
                print("%d row %3d" % (i, rowNum))

            segColumn = self.rowScan(rowNum, lcdShape)

            flag = INITIAL_COLUMN_INDEX
            dig = 0
            last = 0
            for j, col in enumerate(segColumn):
                color = 'w' if (j & 1) == 0 else 'b'
                if flag == 0:
                    flag = DIGIT_COLUMNS
                    dig += 1
                    if dig < MAX_DIGITS:
                        c1 = segColumn[j+1]
                        gap = (c1 - col) // 2
                        st = segColumn[j-3] - gap
                        en = (col + c1) // 2
                        w0 = en - st
                    else:
                        st = segColumn[j-3] - gap
                        en = st + w0
                    if index == 0:
                        digitData.append(DigitData(st, en))
                    else:
                        digitData[dig-1].setCol(st, en, index)

                    if self.dbg[0]:
                        m = "%d st %3d en %3d w %2d g %2d" % \
                            (dig, st, en, w0, gap)
                else:
                    flag -= 1
                    if self.dbg[0]:
                        m = " "

                if self.dbg[0]:
                    deltaCol = col - last
                    print("j %2d col %3d %3d width %3d %s %d %s" % \
                          (j, col, x0-col, deltaCol, color, flag, m))

                if dig >= MAX_DIGITS:
                    break
                last = col

            if self.dbg[0]:
                print()
                for i, data in enumerate(digitData):
                    print("%d st %3d en %3d" % \
                          (i, data.strCol[index], data.endCol[index]))
                print()

            seg.append(segColumn)
            index += 1

        for n, data in enumerate(digitData):
            stCol = data.strCol[0]
            enCol = data.endCol[0]
            centerCol = data.col[0]

            if self.dbg[0]:
                w0 = lcdShape.width
                print("%d st %3d %3d en %3d %3d c %3d %3d" % \
                      (n, stCol, w0-stCol, enCol, w0-enCol, \
                       centerCol, w0-centerCol), end="")
                found = False

            segRows = []
            lastPixel = MAX_PIXEL
            findNeg = True
            skip = True
            for row in range(lcdShape.height):
                pixel = self.refArray[row + y0][x0 - centerCol]
                if skip:
                    if (pixel >= DIGIT_THRESHOLD and \
                        lastPixel <= DIGIT_THRESHOLD):
                        skip = False
                else:
                    if findNeg:
                        if (pixel <= DIGIT_THRESHOLD and \
                            lastPixel >= DIGIT_THRESHOLD):
                            segRows.append(row)
                            findNeg = False
                            if self.dbg[0]:
                                found = True
                    else:
                        if (pixel >= DIGIT_THRESHOLD and \
                            lastPixel <= DIGIT_THRESHOLD):
                            segRows.append(row)
                            findNeg = True
                            if self.dbg[0]:
                                found = True

                    if self.dbg[0] and found:
                        found = False
                        print(" %3d" % (row), end="")
                        
                    if len(segRows) >= SEG_ROWS:
                        break
                lastPixel = pixel

            if len(segRows) == SEG_ROWS:
                data.setSegRows(segRows)

                dirStart = segRows[SEG_ROWS-1]
                dirEnd = lcdShape.height
                for row in range(dirStart, dirEnd):
                    pixel = self.refArray[row + y0][x0 - centerCol]
                    if pixel > DIGIT_THRESHOLD:
                        dirStart = row
                        break

                # dirEnd = lcdShape.height
                # pixel = self.refArray[dirEnd + y0][x0 - centerCol]
                # if pixel < DIGIT_THRESHOLD:
                #     lastPixel = MAX_PIXEL
                #     for row in range(dirEnd, dirStart, -1):
                #         pixel = self.refArray[row + y0][x0 - centerCol]
                #         if (pixel >= DIGIT_THRESHOLD) and \
                #            (lastPixel <= DIGIT_THRESHOLD):
                #             dirEnd = row - 1
                #             break
                #         lastPixel = pixel

                lastPixel = MAX_PIXEL
                for row in range(dirStart, dirEnd):
                    pixel = self.refArray[row + y0][x0 - centerCol]
                    if (pixel <= DIGIT_THRESHOLD) and \
                       (lastPixel >= DIGIT_THRESHOLD):
                        dirEnd = row - 1
                    lastPixel = pixel

                data.setDirRows(dirStart, dirEnd)

            if self.dbg[0]:
                print()

        if self.draw:
            # self.refDraw(self.refGray, lcdShape, seg, digitData)
            self.refDraw(self.refArray, lcdShape, seg, digitData)

        if self.plot[4]:
            self.drawPlot4(self.refArray, lcdShape, seg, \
                           digitData, self.avgPixel)

        if self.plot[5]:
            self.drawPlot5(self.refArray, lcdShape, digitData)

        return digitData

    #   --0--
    #   |   |
    #   5   1
    #   |   |
    #   --6--
    #   |   |
    #   4   2
    #   |   |
    #   --3--
    #    6 5 4  3 2 1 0
    # 0  0 1 1  1 1 1 1  0x3f
    # 1  0 0 0  0 1 1 0  0x06
    # 2  1 0 1  1 0 1 1  0x5b
    # 3  1 0 0  1 1 1 1  0x4f
    # 4  1 1 0  0 1 1 0  0x66
    # 5  1 1 0  1 1 0 1  0x6d
    # 6  1 1 1  1 1 0 1  0x7d
    # 7  0 0 0  0 1 1 1  0x07
    # 8  1 1 1  1 1 1 1  0x7f
    # 9  1 1 0  0 1 1 1  0x67
    #    3 4 6  4 1 2 2
    #------------------------
    # 8  1 1 1  1 1 1 1  0x7f 0x20 0x10 0x40 0x0x2
    # 6  1 1 1  1 1 0 1  0x7d 0x20 0x10 0x40
    # 0  0 1 1  1 1 1 1  0x3f 0x20 0x10

    # 9  1 1 0  0 1 1 1  0x67 0x20     0x01 0x02
    # 5  1 1 0  1 1 0 1  0x6d 0x20     0x01
    # 4  1 1 0  0 1 1 0  0x66 0x20
    #    1 0 3  2 0 2 1

    # 3  1 0 0  1 1 1 1  0x4f      0x40 0x04
    # 2  1 0 1  1 0 1 1  0x5b      0x40

    # 7  0 0 0  0 1 1 1  0x07           0x01
    # 1  0 0 0  0 1 1 0  0x06
    #    2 4 3  2 1 0 1
    #------------------------

    def decode(self, result):
        if (result & 0x20) != 0:
            if (result & 0x10) != 0:
                if (result & 0x40) != 0:
                    if (result & 0x02) != 0:
                        val = 8     #
                    else:
                        val = 6     #
                else:
                    val = 0         #
            else:
                if (result & 0x01) != 0:
                    if (result & 0x02) != 0:
                        val = 9     #
                    else:
                        val = 5     #
                else:
                    val = 4         #

        else:
            if (result & 0x40) != 0:
                if (result & 0x04) != 0:
                    val = 3
                else:
                    val = 2
            else:
                if (result & 0x01) != 0:
                    val = 7
                else:
                    if (result & 0x02) != 0:
                        val = 1
                    else:
                        val = 0
        return(val)

    def testDecode(self):
        for i, result in enumerate((0x3f, 0x06, 0x5b, 0x4f, \
                                    0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x67)):
            val = self.decode(result)
            print("%d %02x %d %s" % (i, result, val, "*" if val == i else ""))

    def readSegments(self, imageArray, lcdShape, data, index):
        x0 = lcdShape.right
        y0 = lcdShape.top
        colT = x0 - data.col[0]
        colB = x0 - data.col[1]
        colRange = data.colRange[0]

        topRow = data.topRow + y0
        botRow = data.botRow + y0

        segData = [None for i in range(SEGMENTS)]
        data.py = True
        data.segData = segData
        result = 0
        for i in range(colRange):
            c0 = colT + i
            c1 = colT - i
            pixel1 = imageArray[topRow][c0]
            if pixel1 < DIGIT_THRESHOLD:
                result |= 0x02
                if segData[1] is None:
                    segData[1] = ((colT, topRow), (c0, topRow))

            pixel5 = imageArray[topRow][c1]
            if pixel5 < DIGIT_THRESHOLD:
                result |= 0x20
                if segData[5] is None:
                    segData[5] = ((colT, topRow), (c1, topRow))

            pixel2 = imageArray[botRow][c0]
            if pixel2 < DIGIT_THRESHOLD:
                result |= 0x04
                if segData[2] is None:
                    segData[2] = ((colT, botRow), (c0, botRow))

            pixel4 = imageArray[botRow][c1]
            if pixel4 < DIGIT_THRESHOLD:
                result |= 0x10
                if segData[4] is None:
                    segData[4] = ((colT, botRow), (c1, botRow))

        for i in range(data.rrT):
            r0 = topRow - i
            pixel0 = imageArray[r0][colT]
            if pixel0 < DIGIT_THRESHOLD:
                result |= 0x01
                if segData[0] is None:
                    segData[0] = ((colT, topRow), (colT, r0))

        for i in range(data.rrC):
            r0 = topRow + i
            pixel6 = imageArray[r0][colT]
            if pixel6 < DIGIT_THRESHOLD:
                result |= 0x40
                if segData[6] is None:
                    segData[6] = ((colT, topRow), (colT, r0))

        for i in range(data.rrB):
            r0 = botRow + i
            pixel3 = imageArray[r0][colB]
            if pixel3 < DIGIT_THRESHOLD:
                result |= 0x08
                if segData[3] is None:
                    segData[3] = ((colB, botRow), (colB, r0))
        return result

    def readDirection(self, imageArray, lcdShape, data):
        col = lcdShape.right - data.col[0]
        startRow = data.dirStart + lcdShape.top
        endRow = data.dirEnd + lcdShape.top
        skip = True
        lastPixel = 0
        result = 0
        for row in range(startRow, endRow):
            pixel = imageArray[row][col]
            # print("%2d pixel %3d skip %s" % (row, pixel, skip))
            if skip:
                if pixel > DIGIT_THRESHOLD:
                    skip = False
            else:
                if lastPixel <= DIGIT_THRESHOLD <= pixel:
                    result = 1
                    break
            lastPixel = pixel
        return result

    def saveError(self, image, ctr, dirError=False):
        self.errCtr += 1
        name = "err-%03d-%d-%s.png" % (self.errCtr, ctr, timeStr()[4:])
        image.save(name, 'PNG')
        print("errctr %3d " % (self.errCtr), end='')
        if dirError:
            self.dirError += 1
            print("dirError %3d " % (self.dirError), end='')
        else:
            self.readError += 1
            print("readError %3d " % (self.readError), end='')
        print(name)

    def saveDirError(self, array, lcdShape, digitData):
        self.errCtr += 1
        name = "dirErr-%03d-%s" % (self.errCtr, timeStr()[4:])
        self.tDraw(array, lcdShape, digitData, name)
        self.dirError += 1
        print("dirError %3d " % (self.dirError), end='')
        print(name)
        sys.stdout.flush()

    def openTarget(self, targetFile, lcdShape):
        self.targetImage = Image.open(targetFile)
        targetGray = ImageOps.grayscale(self.targetImage)
        targetArray = np.asarray(targetGray)
        lcdShape.setTarget(targetArray)
        if LINUX:
            cm.setTarget(targetArray.ravel(), \
                         len(targetArray[0]), len(targetArray))

        if self.draw:
            pass
            # targetDraw = self.targetImage.copy()
            # draw1 = ImageDraw.Draw(targetDraw)

            # stCol = digitData[0].strCol
            # enCol = digitData[-1].endCol
            # draw1.line(((stCol, topRow), (enCol, topRow)), fill=GRAY_FILL)
            # draw1.line(((stCol, botRow), (enCol, botRow)), fill=GRAY_FILL)

            # targetDraw.save("targetDraw0.png", "PNG")
        return targetArray

    def tDraw(self, array, lcdShape, digitData, name="targetDraw2"):
        rgbImage = self.rgbImage(array)
        rgbDraw = ImageDraw.Draw(rgbImage)

        l = lcdShape.left
        r = lcdShape.right
        t = lcdShape.top
        b = lcdShape.bottom

        d = rgbDraw.line
        fill = ImageColor.getrgb("yellow")
        d(((l, t), (r, t), (r, b), (l, b),
           (l, t)), fill=fill)

        y0 = lcdShape.top
        for data in digitData:
            colT = lcdShape.right - data.col[0]
            colB = lcdShape.right - data.col[1]
            colRangeT = data.colRange[0]
            topRow = data.topRow + y0
            botRow = data.botRow + y0
            rowRange = data.rowRange
            dirT = data.dirStart + y0
            dirB = data.dirEnd + y0

            fill0 = ImageColor.getrgb("red")
            fill1 = ImageColor.getrgb("blue")
            d(((colT, topRow), (colT+colRangeT, topRow)), fill=fill0)
            d(((colT, topRow), (colT-colRangeT, topRow)), fill=fill1)
            d(((colB, botRow), (colB+colRangeT, botRow)), fill=fill1)
            d(((colB, botRow), (colB-colRangeT, botRow)), fill=fill0)

            d(((colT, topRow), (colT, topRow-rowRange)), fill=fill0)
            d(((colT, topRow), (colT, topRow+rowRange)), fill=fill1)
            d(((colT, botRow), (colT, botRow+rowRange)), fill=fill0)

            d(((colT+1, dirT), (colT+1, dirB)), fill=fill1)

        rgbImage.save(name + ".png", "PNG")

    def segDraw(self, array=None, lcdShape=None, digitData=None, \
                name="segDraw"):
        if lcdShape is None:
            lcdShape = LcdShape(self.refArray)
            shape = LcdShape()
            shape.cmGet()
        
        if array is None:
            size = lcdShape.rArrayH * lcdShape.rArrayW
            cTarget = np.empty(size, np.uint8)
            cm.getArray(cTarget)
            cTarget = np.reshape(cTarget, (-1, lcdShape.rArrayW))

            rgbImage = self.rgbImage(cTarget)
        else:
            rgbImage = self.rgbImage(array)
            
        if digitData is None:
            digitData = []
            for index in range(MAX_DIGITS):
                data = DigitData(0, 0)
                data.py = False
                digitData.append(data)
                data.cmGet(index)
                for n in range(SEGMENTS):
                    segData = cm.getSegData(index, n)
                    data.setSegData(n, segData)

        w = lcdShape.rArrayW

        l = lcdShape.left
        r = lcdShape.right
        t = lcdShape.top
        b = lcdShape.bottom

        rgbDraw = ImageDraw.Draw(rgbImage)
        d = rgbDraw.line
        fill = ImageColor.getrgb("yellow")
        d(((l, t), (r, t), (r, b), (l, b),
           (l, t)), fill=fill)

        y0 = lcdShape.top
        fill = ImageColor.getrgb("red")
        for data in digitData:
            if data.py:
                for loc in data.segData:
                    if loc is not None:
                        d(loc, fill=fill)
            else:
                for (start, offset) in data.segData:
                    if start != 0:
                        (x0, y0) = coord(start, w)
                        (x1, y1) = coord(start + offset, w)
                        d(((x0, y0), (x1, y1)), fill=fill)

        rgbImage.save(name + ".png", "PNG")

    def drawPlot6(self, array, lcdShape, digitData):
        fig, axs = plt.subplots(3, 2, sharex=True)
        fig.suptitle("Plot 6 readDisplay Progress")
        axs = list(np.concatenate(axs).flat)
        fig.set_figheight(2 * fig.get_figheight())
        fig.set_figwidth(2 * fig.get_figwidth())
        
        x0 = lcdShape.right
        y0 = lcdShape.top
        for i, data in enumerate(digitData):
            axs[i].plot(array[data.dirStart + y0:data.dirEnd + y0, \
                                    x0 - data.col[0]])
            axs[i].plot([0, data.dirEnd - data.dirStart], \
                        [DIGIT_THRESHOLD, DIGIT_THRESHOLD])
            axs[i].set_title("Direction %d col %d" % (i, data.col[0]))

        if self.save:
            fig.savefig("plot6.png")
        else:
            plt.show()

    def drawPlot7(self, array, lcdShape, digitData):
        fig, axs = plt.subplots(3, 2, sharex=True)
        fig.suptitle("Plot 7 readDisplay Digits")
        axs = list(np.concatenate(axs).flat)
        fig.set_figheight(2 * fig.get_figheight())
        fig.set_figwidth(2 * fig.get_figwidth())

        x0 = lcdShape.right
        for i, data in enumerate(digitData):
                x0 = lcdShape.right
                tmpCol = array[:, x0 - data.col[0]]
                axs[i].plot(tmpCol[lcdShape.top:lcdShape.bottom])
                axs[i].plot([0, lcdShape.height], \
                             [DIGIT_THRESHOLD, DIGIT_THRESHOLD])
                axs[i].set_title("%d Column %d" % (i, data.col[0]))

        if self.save:
            fig.savefig("plot7.png")
        else:
            plt.show()

    def readDisplay(self, targetArray, lcdShape, digitData):
        if self.draw:
            self.tDraw(targetArray, lcdShape, digitData)

        if self.plot[6]:
            self.drawPlot6(targetArray, lcdShape, digitData)
            
        if self.plot[7]:
            self.drawPlot7(targetArray, lcdShape, digitData)

        meterVal = 0
        meterMult = 1
        dirMask = 1
        dirVal = 0
        for i, data in enumerate(digitData):
            result = self.readSegments(targetArray, lcdShape, data, i)
            if self.dbg[0]:
                print("result %02x %d" % (result, self.decode(result)))
            meterVal += meterMult * self.decode(result)
            meterMult *= 10

            result = self.readDirection(targetArray, lcdShape, data)
            if result:
                dirVal |= dirMask
            dirMask <<= 1

        if dirVal <= 0x30:
            dirVal = (dirVal, dirConv[dirVal])
        else:
            dirVal = (dirVal, 99)

        return (meterVal, dirVal)

    def updateReading(self, val):
        if val != self.lastVal:
            if val != self.lastTmp:
                self.lastTmp = val
                self.check = 0
                return
            else:
                self.check += 1
                if self.check < 2:
                    return

            self.lastTmp = -1
            nxtCtr = self.ctr + 1
            if nxtCtr >= 4:
                nxtCtr = 0
                if val == 888888:
                    self.ctr = nxtCtr
                else:
                    tmp = str(val)
                    count = 0
                    for i in range(len(tmp)):
                        if tmp[i] == "8":
                            count += 1
                    if count >= 3:
                        val = 888888
                        if nxtCtr == 0:
                            self.ctr = nxtCtr
                    else:
                        print("%s expected 888888 read %d" % \
                              (timeStr(), val))
                        self.saveError(self.targetImage, self.ctr)
                        self.sync = False
            else:
                meter = self.meterVal[nxtCtr]
                delta = 0 if meter == 0 else val - meter
                print("%s %d val %6d meter %6d delta %2d " \
                      "n %5d r %5d f %5d" % \
                      (timeStr(), nxtCtr, val, meter, delta, \
                       self.net, self.rev, self.fwd))
                if abs(delta) <= 1:
                    self.ctr = nxtCtr
                    self.meterVal[self.ctr] = val
                    if delta != 0:
                        if self.ctr == 1:
                            print("**net %d" % (self.net))
                            self.net = 0
                        elif self.ctr == 2:
                            print("**fwd %d" % (self.fwd))
                            self.fwd = 0
                        elif self.ctr == 3:
                            print("**rev %d" % (self.rev))
                            self.rev = 0
                else:
                    self.saveError(self.targetImage, self.ctr)
                    val = self.lastVal
        self.lastVal = val

    def updateDirection(self, dirVal, dirIndex):
        if dirIndex != self.lastDir:
            if dirIndex == 99:
                # self.saveError(self.targetImage, self.ctr, True)
                dirIndex = self.lastDir
                return dirIndex
            
                if self.dirSign > 0:
                    dirIndex += 1
                    if dirIndex > 5:
                        dirIndex = 0
                elif self.dirSign < 0:
                    dirIndex -= 1
                    if dirIndex < 0:
                        dirIndex = 5
                print("*+dirIndex %d lastDir %d" % \
                      (dirIndex, self.lastDir))

            delta = dirIndex - self.lastDir
            if self.dirSign > 0:
                if delta <= -3:
                    delta += 6
            elif self.dirSign < 0:
                if delta >= 3:
                    delta -= 6
            self.net += delta
            if delta > 0:
                self.rev += delta
                self.dirSign = 1
            else:
                self.fwd -= delta
                self.dirSign = -1
            self.delta = delta
            self.lastDir = dirIndex
        else:
            self.delta = 0
        return dirIndex

    def loopProcess(self, lcdShape, digitData):
        dirErrCount = 0
        self.initLoopVars()
        if LINUX:
            cm.cvar.updateEna = int(self.update)

        while True:
            retry = 100
            while True:
                try:
                    contents = urllib.request.urlopen(URL, data=None, \
                                                      timeout=5).read()
                    self.targetFile = io.BytesIO(contents)
                    break
                except IncompleteRead:
                    print("**%s!IncompleteRead retry %d" % (timeStr(), retry))
                except socket.timeout:
                    print("**%s!socket.timeout retry %d" % (timeStr(), retry))
                except URLError:
                    print("**%s!URLError retry %d" % (timeStr(), retry))
                sys.stdout.flush()
                retry -= 1
                if retry <= 0:
                    sys.exit()
                if LINUX:
                    cm.loopSync()
                sleep(10)
                    
            targetArray = self.openTarget(self.targetFile, lcdShape)

            if LINUX:
                lcdShape.cmSet()
                dirError = cm.loopProcess(targetArray.ravel())
                if dirError != 0:
                    if self.draw and (self.dirError < 100):
                        dirErrCount += 1
                        if dirErrCount == 1:
                            self.saveDirError(targetArray, lcdShape, digitData)
                else:
                    dirErrCount = 0

                if False:
                    self.segDraw(name="segDrawA-" + timeStr())

                if self.dbg[4] and cm.drawTargetUpd():
                    if (self.maxUpdCnt == 0) or \
                       (self.drwUpdCnt < self.maxUpdCnt):

                        (cmShape, cmData) = cmGetData()
                        self.tDraw(targetArray, cmShape, cmData,
                                   name=(("tUpd-%03d-" % (self.drwUpdCnt)) + \
                                         timeStr()))
                        self.drwUpdCnt += 1

                if self.dbg[5] and cm.drawTargetErr():
                    if (self.maxErrCnt == 0) or \
                       (self.drwErrCnt < self.maxErrCnt):

                        (cmShape, cmData) = cmGetData()
                        self.tDraw(targetArray, cmShape, cmData, \
                                   name=(("tErr-%03d-" % (self.drwErrCnt)) + \
                                         timeStr()))
                        self.drwErrCnt += 1

                if self.cDbg2 and cm.drawTargetDbg():
                    if (self.maxDbgCnt == 0) or \
                       (self.drwDbgCnt < self.maxDbgCnt):

                        (cmShape, cmData) = cmGetData()
                        self.tDraw(targetArray, cmShape, cmData,
                                   name=(("tDbg-%03d-" % (self.drwDbgCnt)) + \
                                         timeStr()))
                        self.drwDbgCnt += 1
                    
                sleep(.25)
                continue

            (val, (dirVal, dirIndex)) = \
                self.readDisplay(targetArray, lcdShape, digitData)

            if True or (self.segDrwCnt == 0) or \
               (self.segDrwCnt < self.maxSegCnt):
                self.segDraw(targetArray, lcdShape, digitData, \
                             name=("segDraw-%03d-" % (self.segDrwCnt)) + \
                             timeStr())
                self.segDrwCnt += 1

            if self.sync:
                self.updateReading(val)
                dirIndex = self.updateDirection(dirVal, dirIndex)
                print("%d %6d 0x%02x %d %2d" % \
                      (self.ctr, val, dirVal, dirIndex, self.delta))
            else:
                if val != self.lastVal:
                    print(val)

                if val == 888888:
                    print("sync")
                    self.sync = True
                    self.ctr = 0

                if (self.lastDir != 99) and (dirIndex != self.lastDir):
                    if dirIndex == 99:
                        dirIndex = self.lastDir
                    else:
                        delta = dirIndex - self.lastDir
                        if self.dirSign > 0:
                            if delta <= -3:
                                delta += 6
                        elif self.dirSign < 0:
                            if delta >= 3:
                                delta -= 6
                        self.dirSign = 1 if delta > 0 else -1
                        self.delta = delta
                    print("0x%02x %d" % (dirVal, dirIndex))
                self.lastVal = val
                self.lastDir = dirIndex

            self.targetImage.close()
            sys.stdout.flush()
            sleep(.25)

    def rgbImage(self, array):
        tImage = Image.fromarray(array)
        rgbImage = Image.new("RGB", tImage.size)
        rgbImage.paste(tImage)
        tImage.close();
        return rgbImage

    def cmTBDraw(self, array, shape, lcdShape, ttl):
        rgbImage = self.rgbImage(array)
        rgbDraw = ImageDraw.Draw(rgbImage)
        l = rgbDraw.line
        l(((shape.left,  shape.top),    (shape.right, shape.top), \
           (shape.right, shape.bottom), (shape.left,  shape.bottom), \
           (shape.left,  shape.top)),    fill=ImageColor.getrgb("yellow"))
        l(((lcdShape.right + 50,  lcdShape.top), \
           (lcdShape.right,  lcdShape.top), \
           (lcdShape.right,  lcdShape.top - 50)), \
          fill=ImageColor.getrgb("red"))
        l(((lcdShape.left - 50,  lcdShape.bottom), \
           (lcdShape.left,  lcdShape.bottom), \
           (lcdShape.left,  lcdShape.bottom + 50)), \
          fill=ImageColor.getrgb("blue"))
        rgbImage.save(ttl + ".png")

    def cmPlot9(self, array, shape, ttl):
        temps = []
        size = 2 * int(shape.height * TARGET_ROW_RANGE) + \
            DELTA_OFS
        for index in range(2):
            sumArray = np.zeros(size, np.int32)
            deltaArray = np.zeros(size, np.int32)
            indexArray = np.zeros(size, np.int32)
            cm.getSumArray(sumArray, index);
            cm.getDeltaArray(deltaArray, index);
            cm.getIndexArray(indexArray, index);
            temps.append((indexArray, sumArray, deltaArray))

        size = 2 * int(shape.width * TARGET_COLUMN_RANGE) + \
            DELTA_OFS
        for index in range(2, 4):
            sumArray = np.zeros(size, np.int32)
            deltaArray = np.zeros(size, np.int32)
            indexArray = np.zeros(size, np.int32)
            cm.getSumArray(sumArray, index);
            cm.getDeltaArray(deltaArray, index);
            cm.getIndexArray(indexArray, index);
            temps.append((indexArray, sumArray, deltaArray))

        self.drawPlot9(array, shape, temps, ttl)

    def process(self):
        if LINUX:
            cm.dbgSet(0, int(self.cDbg0))
            cm.dbgSet(1, int(self.cDbg1))
            cm.dbgSet(2, int(self.cDbg2))
            cm.cvar.TARGET_COLUMN_RANGE = TARGET_COLUMN_RANGE
            cm.cvar.TARGET_ROW_RANGE = TARGET_ROW_RANGE
            cm.cvar.SUM_THRESHOLD = SUM_THRESHOLD
            cm.cvar.DIGIT_THRESHOLD = DIGIT_THRESHOLD

        self.openRef()

        if self.plot[1]:
            self.histogram()

        lcdShape = LcdShape(self.refArray, self.dbg[0])
        self.verticalBounds(lcdShape)
        self.horizontalBounds(lcdShape)
        self.cropRef(lcdShape)
        lcdShape.setSize()

        if LINUX:
            if self.loop or self.capture:
                contents = urllib.request.urlopen(URL).read()
                tFile = io.BytesIO(contents)
                tArray = self.openTarget(tFile, lcdShape)
            else:
                # self.targetGray = self.refGray
                tArray = self.refArray

            print("call setup cm lcdShape")
            sys.stdout.flush()

            cm.setRef(self.refArray.ravel(), len(self.refArray[0]), \
                      len(self.refArray))
            cm.setSize(lcdShape.width, lcdShape.height)
            cm.setRows(lcdShape.top, lcdShape.bottom)
            cm.setColumns(lcdShape.left, lcdShape.right)

            # if True:
            #     cm.cvar.updateEna = int(True)
            #     print("call cm.targetBounds 1")
            #     sys.stdout.flush()
            #     cm.targetBounds(tArray.ravel(), len(tArray[0]), FALSE)
            #     if self.dbg[0]:
            #         cm.printShape()
            #         lcdShape.print()

            #     lcdShape.set(cm.getRows(), cm.getColumns())

            #     if self.dbg[0]:
            #         lcdShape.print()
            # cm.cvar.updateEna = int(self.update)
        else:
            # self.targetGray = self.refGray
            sys.stdout.flush()

        print("call self.targetBounds 1")
        self.targetBounds(self.refArray, lcdShape, False)

        print("call self.findRefSegments 1")
        digitData = self.findRefSegments(lcdShape)

        if LINUX:
            if True:
                lcdShape.print()
                
                cm.cvar.updateEna = 1
                refArray = self.refArray
                print("call cm.targetBounds 1")
                sys.stdout.flush()
                cm.targetBounds(refArray.ravel(), len(refArray[0]), FALSE)
                shape = LcdShape(refArray)
                shape.cmGet()
                if self.draw:
                    self.cmTBDraw(refArray, shape, lcdShape, "tb1")
                cm.targetUpdate();
                if self.dbg[0]:
                    shape.print()

                print("call cm.findRefSegments 1")
                cm.findRefSegments(refArray.ravel(), len(refArray[0]))

                tmpData = []
                print("compare digit data")
                sys.stdout.flush()
                for index in range(MAX_DIGITS):
                    data = DigitData(0, 0)
                    tmpData.append(data)
                    if self.dbg[0]:
                        cm.prtDigDat(index)
                        cm.prtDigDatC(index)
                    data.cmGet(index)

                    if self.dbg[0]:
                        print("cp %d " % (index), end="")
                        data.print()
                        data.printC()
                        print("py %d " % (index), end="")
                        digitData[index].print()
                        digitData[index].printC()
                        print()
                        sys.stdout.flush()
                
                if self.plot[9]:
                    self.cmPlot9(refArray, shape, "9a")

                if self.plot[4]:
                    seg = []
                    avgRows = []
                    for index in range(2):
                        segColumns = np.empty(MAX_COL, np.int32)
                        cm.getSegColumn(segColumns, index)
                        seg.append(list(segColumns))

                        avgPixel = np.empty(lcdShape.rArrayW, np.uint8)
                        cm.getAvgPixel(avgPixel, index)
                        avgRows.append(avgPixel)
                    self.drawPlot4(refArray, shape, seg, tmpData,
                                   avgRows, "4a")

                if self.plot[5]:
                    self.drawPlot5(refArray, shape, tmpData, "5a")

                if self.draw:
                    self.tDraw(refArray, shape, tmpData, "targetDrawL")

            if False:
                cm.findRefSegments(self.refArray.ravel(), \
                                   len(self.refArray[0]))
                for n, data in enumerate(digitData):
                    for j in (0, 1):
                        cm.setDigitCol(data.strCol[0], data.endCol[0], n, j)
                    cm.setSegRows(np.array(data.segRows, np.int32), n)
                    cm.setDirRows(data.dirStart, data.dirEnd, n)
            cm.loopInit()

        if self.loop:
            os.system(rm + 'err*.png')
            self.loopProcess(lcdShape, digitData)
        else:
            if self.capture:
                contents = urllib.request.urlopen(URL).read()
                self.targetFile = io.BytesIO(contents)
                if False:
                    f = open("input.jpg", "wb")
                    f.write(contents)
                    f.close()
            else:
                if self.targetFile is None:
                    self.targetFile = self.refFile

            targetArray = self.openTarget(self.targetFile, lcdShape)
            if LINUX:
                print("call cm.targetBounds 2")
                sys.stdout.flush()
                cm.targetBounds(targetArray.ravel(), \
                                len(targetArray[0]), FALSE)
                cm.printShape();
                if self.draw:
                    shape = LcdShape(targetArray)
                    shape.cmGet()
                    self.cmTBDraw(targetArray, shape, lcdShape, "tb2")

            print("call self.targetBounds 2")
            sys.stdout.flush()
            self.targetBounds(targetArray, lcdShape, False)

            if LINUX:
                val = 0
                dirVal = 0
                dirIndex = 0
                print("w %3d" % (len(targetArray[0])))
                (val, dirIndex, dirVal) = cm.readDisplay(targetArray.ravel())
                print("cm %6d 0x%02x %d" % (val, dirVal, dirIndex))
                if self.draw:
                    cm.printShape()
                    cm.printData()
                    self.tDraw(targetArray, shapeCopy(), digitDataCopy(), \
                               "targetDrawX")
                if True:
                    self.segDraw(name="segDrawA" + timeStr())

            # else:
            if True:
                (val, (dirVal, dirIndex)) = \
                    self.readDisplay(targetArray, lcdShape, digitData)
                if True:
                    self.segDraw(targetArray, lcdShape, digitData, \
                                 name="segDraw")
            print("py %6d 0x%02x %d" % (val, dirVal, dirIndex))

        # for val in vars(self).keys():
        #     print(val)

print(timeStr())

rm = 'rm -f '
os.system(rm + 'ref.png')
os.system(rm + 'refDraw*.png')
os.system(rm + 'targetDraw*.png')
os.system(rm + 'tb*.png')
os.system(rm + 'plot*.png')
os.system(rm + 'dirErr*.png')
os.system(rm + 'err*.png')
os.system(rm + 'tUpd*.png')
os.system(rm + 'tErr*.png')
os.system(rm + 'tDbg*.png')
os.system(rm + 'segDraw*.png')

meter = Meter()
meter.setup()
try:
    meter.process()
except KeyboardInterrupt:
    pass
    
