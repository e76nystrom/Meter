#!/cygdrive/c/Python39/python.exe
#*******************************************************************************

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageOps
from time import sleep, time_ns
from platform import system

import urllib.request
import io
from datetime import datetime
from pytz import timezone
# from collections import namedtuple

LINUX = system() == 'Linux'
R_PI = False
if LINUX:
    R_PI = os.uname().machine.startswith('arm')

URL = "http://192.168.42.70/capture"

if LINUX:
    print("Linux")
    import cMeter as cm

WHITE_FILL = 255
BLACK_FILL = 0
GRAY_FILL  = 192

MAX_PIXEL = 255

TOP_SEG = 0.3
BOTTOM_SEG = 0.6
MARK_HEIGHT = 0.375

DELTA_THRESHOLD = 50
COL_DELTA_THRESHOLD = 100
REF_DELTA_THRESHOLD = 60
SEG_COL_THRESHOLD = 30
SEG_ROW_THRESHOLD = 60
DIGIT_THRESHOLD = 75

INITIAL_COLUMN_INDEX = 2
DIGIT_COLUMNS = 3

MAX_DIGITS = 6 - 1
SEG_ROWS = 3

dirConv = \
( \
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

# LcdRows = namedtuple('LcdRows', ['top', 'bottom'])
# LcdCols = namedtuple('LcdCols', ['left', 'right'])

tz = timezone("America/New_York")

def timeStr():
    now = datetime.now(tz=tz)
    return(now.strftime("%b_%d_%Y_%H-%M-%S"))

class LcdShape():
    def __init__(self, array, dbg=False):
        self.dbg = dbg
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

    def setRows(self, top, bottom):
        self.top = top
        self.bottom = bottom
        if self.dbg:
            print("setRows t %3d b %3d" % (self.top, self.bottom))

    def setColumns(self, left, right):
        self.left = left
        self.right = right
        if self.dbg:
            print("setCols l %3d r %3d" % (self.left, self.right))

    def setSize(self):
        self.height = h = (self.bottom - self.top) + 1
        self.width = (self.right - self.left) + 1
        self.topRow = int(TOP_SEG * h)
        self.botRow = int(BOTTOM_SEG * h)
        if self.dbg:
            print("setSize w %3d h %3d tr %3d br %3d" % \
                  (self.width, self.height, self.topRow, self.botRow))

class DigitData():
    def __init__(self, strCol, endCol):
        self.strCol = strCol
        self.endCol = endCol
        self.col = (strCol + endCol) // 2
        self.colRange = (endCol - strCol) // 2

        self.segRows = None
        self.maxRow = 0
        self.topRow = 0
        self.botRow = 0
        self.rowRange = 0
        self.dirStart = 0
        self.dirEnd = 0

    def setSegRows(self, segRows, maxRow):
        self.segRows = segRows
        self.maxRow = maxRow
        self.topRow = (segRows[0] + segRows[1]) // 2
        self.botRow = (segRows[1] + segRows[2]) // 2
        self.rowRange = (segRows[1] - segRows[0]) // 2 + 2

    def setDirRows(self, dirStart, dirEnd):
        self.dirStart = dirStart
        self.dirEnd = dirEnd

class Meter():
    def __init__(self):
        self.plot1 = False          # row histogram
        self.plot2 = False          # row sum array
        self.plot3 = False          # upper and lower row
        self.plot4 = False          # reference rows
        self.plot5 = False          # digit columns
        self.plot6 = False          # direction
        self.plot7 = False          # target center column
        self.plot8 = False          # target bounds
        self.save = False           # save figure

        self.dbg0 = False           # general debug
        self.dbg1 = False           # top and bottom
        self.dbg2 = False           # right and left
        self.dbg3 = False

        self.draw = False           # drawing on images
        self.capture = False
        self.loop = False
        self.retry = False

        self.update = False
        self.cDbg0 = False
        self.cDbg1 = False
        self.cDbg2 = False

        self.refFile = None
        self.targetFile = None

        self.refGray = None
        self.refArray = None
        self.rowArray = None
        self.targetImage = None
        self.targetGray = None

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
                        self.plot1 = True
                    elif val == 2:
                        self.plot2 = True
                    elif val == 3:
                        self.plot3 = True
                    elif val == 4:
                        self.plot4 = True
                    elif val == 5:
                        self.plot5 = True
                    elif val == 6:
                        self.plot6 = True
                    elif val == 7:
                        self.plot7 = True
                    elif val == 8:
                        self.plot8 = True
                elif ch == 'd':
                    val = int(val[1:])
                    if val == 0:
                        self.dbg0 = True
                    elif val == 1:
                        self.dbg1 = True
                    elif val == 2:
                        self.dbg2 = True
                    elif val == 3:
                        self.dbg3 = True
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
                elif ch == 'y':
                    self.retry = True
                elif  ch == 'u':
                    self.update = True
            elif self.refFile is None:
                self.refFile = val
            elif self.targetFile is None:
                self.targetFile = val
            n += 1

        if self.refFile is None:
            self.refFile = "cRef-800x600-1.jpg"

    def openRef(self):
        refImage = Image.open(self.refFile)
        self.refGray = ImageOps.grayscale(refImage)
        refImage.close()
        self.refArray = np.asarray(self.refGray)
        if self.dbg0:
            print(len(self.refArray), len(self.refArray[0]),
                  self.refArray[0][0])

        self.rowArray = np.rint(self.refArray.sum(axis=1) / \
                                len(self.refArray[0])).astype(int)

    def histogram(self):
        if self.plot1:
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

    # find upper and lower bound of LCD display
    def verticalBounds(self, lcdShape):
        if self.dbg1:
            print("verticalBounds threshold %3d" % (DELTA_THRESHOLD))
        negDelta = True
        deltaTotal = 0
        lastSum = self.rowArray[0]
        strMin = MAX_PIXEL
        endMin = MAX_PIXEL
        hyst = 0
        blank = False
        char = '<'
        for row, rSum in enumerate(self.rowArray):
            delta = rSum - lastSum
            if delta != 0:
                if negDelta:
                    if rSum < strMin:
                        strMin = rSum
                        start = row

                    if delta < 0:
                        minVal = rSum
                        deltaTotal -= delta
                    else:
                        if deltaTotal > DELTA_THRESHOLD:
                            negDelta = False
                            deltaTotal = 0
                            hyst = 0
                            if self.dbg1:
                                blank = True
                                char = '>'
                        else:
                            deltaTotal = 0
                            strMin = MAX_PIXEL
                else:
                    if rSum < endMin:
                        endMin = rSum
                        end = row

                    if delta > 0:
                        maxVal = rSum
                        deltaTotal += delta
                        if deltaTotal > DELTA_THRESHOLD:
                            break
                        hyst = 0
                    else:
                        if hyst >= 2:
                            deltaTotal = 0
                            endMin = MAX_PIXEL
                        else:
                            deltaTotal += delta
                            hyst += 1
                if self.dbg1:
                    print("%crow %3d rSum %3d delta %3d dTotal %3d h %d" % \
                          (char, row, rSum, delta, deltaTotal, hyst))
                    if blank:
                        blank = False
                        print()
            lastSum = rSum

        lcdShape.setRows(start, end)

        if self.dbg0:
            print("str %3d minVal %3d" % (start, minVal))
            print("end %3d maxVal %3d" % (end, maxVal))
            print("top %3d bottom %3d" % (lcdShape.top, lcdShape.bottom))

        if self.plot2:
            plt.plot(self.rowArray)
            plt.title("Row Array %3d -> %3d" % (start, end))
            plt.plot([lcdShape.top, lcdShape.bottom], [minVal, maxVal])
            if self.save:
                plt.gcf().savefig("plot2.png")
            else:
                plt.show()
            plt.close()

    # find left and right bound of LCD display
    def horizontalBounds(self, lcdShape):
        left = 0
        right = 0
        if self.plot3:
            fig, axs = plt.subplots(2, sharex=True)
            fig.suptitle('Horizontal Bounds')
            n = 0
        for row in (lcdShape.top, lcdShape.bottom):
            deltaMin = 0
            deltaMax = 0
            negDelta = True
            deltaTotal = 0
            lastPixel = int(self.refArray[row][0])
            startMin = MAX_PIXEL
            endMin = MAX_PIXEL
            for col, pixel in enumerate(self.refArray[row]):
                if col < 200:
                    continue
                pixel = int(pixel)
                delta = pixel - lastPixel
                if delta != 0:
                    if negDelta:
                        if delta < 0:
                            deltaTotal -= delta
                        else:
                            if deltaTotal > COL_DELTA_THRESHOLD:
                                left = col
                                if self.dbg0:
                                    print("start %3d" % (left))
                                negDelta = False
                                deltaTotal = 0
                                deltaMin = pixel
                                if self.dbg2:
                                    print()
                            else:
                                deltaTotal = 0
                        if self.dbg2:
                            print("<col %3d pixel %3d delta %3d dTotal %3d" % \
                                  (col, pixel, delta, deltaTotal))
                    else:
                        if delta > 0:
                            deltaTotal += delta
                        else:
                            if deltaTotal > COL_DELTA_THRESHOLD:
                                if self.dbg0:
                                    print("end %3d" % (right))
                                deltaMax = pixel
                                break
                            else:
                                deltaTotal = 0
                                right = col
                        if self.dbg2:
                            print(">col %3d pixel %3d delta %3d dTotal %3d" % \
                                  (col, pixel, delta, deltaTotal))
                lastPixel = pixel

            if self.plot3:
                axs[n].plot(self.refArray[row])
                axs[n].set_title("Row %3d %3d -> %3d" % (row, left, right))
                axs[n].plot((left, right), [deltaMin, deltaMax])
                n += 1

            if self.dbg0:
                print("left %3d right %3d" % (left, right))

        if self.plot3:
            if self.save:
                plt.gcf().savefig("plot3.png")
            else:
                plt.show()
        lcdShape.setColumns(left, right)
        
    def targetBounds(self, lcdShape):
        array = np.asarray(self.targetGray)
        cr = int(lcdShape.width * 0.05)
        lc = lcdShape.left
        rc = lcdShape.right
        rr = int(lcdShape.height * 0.20)
        tr = lcdShape.top
        br = lcdShape.bottom
        if self.dbg0:
            print("\ntargetBounds")
            print("left %3d right %3d top %3d bottom %3d" % \
                  (lcdShape.left, lcdShape.right, \
                   lcdShape.top, lcdShape.bottom))
            print("lc %3d rc %3d cr %3d tr %3d br %3d rr %3d" % \
                  (lc, rc, cr, tr, br, rr))
        if self.draw:
            targetDraw = self.targetGray.copy()
            draw1 = ImageDraw.Draw(targetDraw)
            d = draw1.line
            d(((lc - cr, tr - rr), (rc + cr, tr - rr)), fill=BLACK_FILL)
            d(((rc + cr, tr - rr), (rc + cr, br + rr)), fill=BLACK_FILL)
            d(((rc + cr, br + rr), (lc - cr, br + rr)), fill=BLACK_FILL)
            d(((lc - cr, br + rr), (lc - cr, tr - rr)), fill=BLACK_FILL)
        if self.plot8:
            fig, axs = plt.subplots(2)
            # axs = list(np.concatenate(axs).flat)
            fig.set_figheight(2 * fig.get_figheight())
            # fig.set_figwidth(2 * fig.get_figwidth())
            fig.suptitle("target bounds")
            n = 0

        rows = []
        cols = []
        for r in (tr, br):
            if self.dbg2:
                print()
            minSum = MAX_PIXEL
            for row in range(r - rr, r + rr):
                rSum = 0
                for col in range(lc - cr, rc + cr):
                    rSum += array[row][col]
                rSum = int(rSum / (rc - lc + 2 * cr))
                if rSum < minSum:
                    minSum = rSum
                    r0 = row
                if self.dbg2:
                    print("row %3d rSum %3d minSum %3d" % (row, rSum, minSum))
            rows.append(r0)
            if self.dbg2:
                print()

            deltaMin = 0
            deltaMax = 0
            negDelta = True
            deltaTotal = 0
            lastPixel = int(self.refArray[row][0])
            startMin = MAX_PIXEL
            endMin = MAX_PIXEL
            for col in range(lc - cr, rc + cr):
                pixel = int(array[r0][col])
                delta = pixel - lastPixel
                if delta != 0:
                   if negDelta:
                        if delta < 0:
                            deltaTotal -= delta
                        else:
                            if deltaTotal > COL_DELTA_THRESHOLD:
                                left = col
                                negDelta = False
                                deltaMin = pixel
                                if self.dbg2:
                                    print()
                            deltaTotal = 0
                   else:
                        if delta > 0:
                            deltaTotal += delta
                        else:
                            if deltaTotal > COL_DELTA_THRESHOLD:
                                deltaMax = pixel
                                break
                            else:
                                deltaTotal = 0
                                right = col
                   if self.dbg2:
                        print("%scol %3d pixel %3d delta %3d dTotal %3d" % \
                              ((">","<")[negDelta], col, pixel, \
                               delta, deltaTotal))
                lastPixel = pixel
            cols.append((left, right))

            if self.dbg0:
                print("row %3d cols %3d %3d" % (r0, left, right))

            if self.plot8:
                axs[n].plot(array[r0])
                axs[n].plot([left, right], [deltaMin, deltaMax])
                axs[n].set_title("row %3d col %3d %3d" % (r0, left, right))
                n += 1

        if self.draw:
            if (len(cols) == 2) and (len(rows) == 2):
                (l, r) = cols[0]
                (t, b) = rows
                d(((l, t), (r, t)), fill=WHITE_FILL)
                d(((r, t), (r, b)), fill=WHITE_FILL)
                d(((r, b), (l, b)), fill=WHITE_FILL)
                d(((l, b), (l, t)), fill=WHITE_FILL)
            targetDraw.save("targetDraw1.png", "PNG")
        if self.plot8:
            plt.show()

    def cropRef(self, lcdShape):
        if self.draw:
            self.refGray.save("ref.png", "PNG")
            drawImg = ImageDraw.Draw(self.refGray)
            l = lcdShape.left
            r = lcdShape.right
            t = lcdShape.top
            b = lcdShape.bottom
            drawImg.line(((l, t), (r, t)), fill=WHITE_FILL)
            drawImg.line(((r, t), (r, b)), fill=WHITE_FILL)
            drawImg.line(((r, b), (l, b)), fill=WHITE_FILL)
            drawImg.line(((l, b), (l, t)), fill=WHITE_FILL)

        if self.dbg0:
            print("width %3d height %3d pixels %5d, top %3d bottom %3d" % \
                  (lcdShape.width, lcdShape.height, \
                   lcdShape.width * lcdShape.height, \
                   lcdShape.topRow, lcdShape.botRow))
        return(lcdShape)
    
    def rowScan0(self, rowNum, lcdShape):
        maxPixel = 0
        minPixel = MAX_PIXEL
        findMin = True
        segColumn = []
        # for col in range(lcdShape.width - 3, 0, -1):
        #     pixel = row[col + x0]
        for col in range(3, lcdShape.width):
            pixel = row[x0 - col]
            if findMin:
                if pixel < minPixel:
                    minPixel = pixel
                    minLoc = col
                else:
                    delta = pixel - minPixel
                    if delta > SEG_COL_THRESHOLD:
                        segColumn.append(col)
                        maxPixel = 0
                        findMin = False
            else:
                if pixel > maxPixel:
                    maxPixel = pixel
                    maxLoc = col
                else:
                    delta = maxPixel - pixel
                    if delta > SEG_COL_THRESHOLD:
                        segColumn.append(col)
                        minPixel = MAX_PIXEL
                        findMin = True
        return segColumn

    def rowScan1(self, rowNum, lcdShape):
        if self.dbg0:
            print("rowScan %3d" % (rowNum))
            change = ""
            w = lcdShape.width
        x0 = lcdShape.right
        negDelta = True
        deltaTotal = 0
        hyst = 0
        segColumn = []
        row = self.refArray[rowNum]
        lastPixel = int(row[x0 - 2])
        for col in range(3, lcdShape.width):
            pixel = int(row[x0 - col])
            delta = pixel - lastPixel
            if negDelta:
                if delta < 0:
                    deltaTotal -= delta
                    hyst = 0
                else:
                    if deltaTotal > REF_DELTA_THRESHOLD:
                        negCol = col
                        segColumn.append(negCol)
                        negDelta = False
                        deltaTotal = 0
                        hyst = 0
                        if self.dbg3:
                            change = "neg %3d\n" % (negCol)
                    else:
                        if hyst >= 1:
                            stCol = col
                            deltaTotal = 0
                        else:
                            deltaTotal -= delta
                            hyst += 1
            else:
                if delta > 0:
                    deltaTotal += delta
                    hyst = 0
                else:
                    if deltaTotal > REF_DELTA_THRESHOLD:
                        posCol = col
                        segColumn.append(posCol)
                        negDelta = True
                        deltaTotal = 0
                        hyst = 0
                        if self.dbg0:
                            change = "pos %3d\n" % (posCol)
                    else:
                        if hyst >= 2:
                            stCol = col
                            deltaTotal = 0
                        else:
                            deltaTotal += delta
                            hyst += 1
            if self.dbg3:
                print("%ccol %3d %3d pixel %3d delta %3d dTotal %3d h %d %s" % \
                      ((">", "<")[negDelta], col, w - col, pixel, \
                       delta, deltaTotal, hyst, change))
                change = ""
            lastPixel = pixel
        return segColumn

    def rowScan(self, rowNum, lcdShape):
        if self.dbg0:
            print("rowScan %3d" % (rowNum))
        x0 = lcdShape.right
        negDelta = True
        segColumn = []
        row = self.refArray[rowNum]
        lastPixel = int(row[x0 - 2])
        for col in range(3, lcdShape.width):
            pixel = int(row[x0 - col])
            delta = pixel - lastPixel
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
        return segColumn

    # find location of segments on the reference array
    def findRefSegments(self, lcdShape):
        x0 = lcdShape.right
        y0 = lcdShape.top
        l = x0 - lcdShape.width
        r = x0
        t = lcdShape.topRow + y0
        b = lcdShape.botRow + y0

        if self.plot4:
            fig, axs = plt.subplots(2, sharex=True)
            fig.set_figwidth(3 * fig.get_figwidth())
            fig.set_figheight(2 * fig.get_figheight())
            n = 0

        if self.draw:
            refDraw = self.refGray.copy()
            draw1 = ImageDraw.Draw(refDraw)
            draw1.line(((l, t), (r, t)), fill=BLACK_FILL)
            draw1.line(((l, b), (r, b)), fill=BLACK_FILL)
            refDraw.save("refDraw0.png", "PNG")

            refDraw = self.refGray.copy()
            draw1 = ImageDraw.Draw(refDraw)

        mark = int(lcdShape.height * MARK_HEIGHT)
        for (rowNum, markStart, markEnd) in \
            ((t, 0, mark), (b, mark, lcdShape.height)):
            if self.dbg0:
                print("findRefSegments row %2d" % (rowNum))
            row = self.refArray[rowNum]

            if self.plot4:
                axs[n].plot(row[lcdShape.left:x0])
                axs[n].set_title("Ref Row %d" % (rowNum))
                axs[n].plot([0, lcdShape.width], \
                            [DIGIT_THRESHOLD, DIGIT_THRESHOLD])

            segColumn = self.rowScan(rowNum, lcdShape)

            if self.plot4 and False:
                xVal = []
                yVal = []
                w = lcdShape.width
                xVal.append(w)
                val = 255
                yVal.append(val)
                for col in segColumn:
                    xVal.append(w - col)
                    yVal.append(val)
                    val = 255 if val == 0 else 0
                    xVal.append(w - col)
                    yVal.append(val)
                axs[n].plot(xVal, yVal)        

            j = 0
            flag = INITIAL_COLUMN_INDEX
            dig = 0
            last = 0
            digitData= []
            for col in segColumn:
                if (j & 1) == 0:
                    fill = WHITE_FILL
                    color = 'w'
                else:
                    fill = BLACK_FILL
                    color = 'b'
                if self.draw:
                    draw1.line(((x0 - col, markStart + y0), \
                                (x0 - col, markEnd + y0)), fill=fill)
                if flag == 0:
                    flag = DIGIT_COLUMNS
                    if dig <= MAX_DIGITS:
                        if dig < MAX_DIGITS:
                            gap = (segColumn[j+1] - col) // 2
                        st = segColumn[j-2] - gap
                        if dig < MAX_DIGITS:
                            en = segColumn[j+1] + gap
                            w = en - st
                        else:
                            en = st + w
                        digitData.append(DigitData(st, en))
                        
                        if self.dbg0:
                            m = "%d st %3d en %3d w %2d g %2d" % \
                                (dig, st, en, w, gap)
                        if (markStart == 0) and self.draw:
                            draw1.line(((x0 - st, markStart + y0), \
                                        (x0 - st, markEnd + y0)), \
                                       fill=GRAY_FILL)
                            if dig == MAX_DIGITS:
                                draw1.line(((x0 - en, markStart + y0), \
                                            (x0 - en, markEnd+ y0)), \
                                           fill=GRAY_FILL)
                        dig += 1
                else:
                    flag -= 1
                    if self.dbg0:
                        m = " "

                if self.dbg0:
                    deltaCol = col - last
                    print("j %2d col %3d %3d width %3d %s %d %s" % \
                          (j, col, x0-col, deltaCol, color, flag, m))
                j += 1
                last = col

            if self.dbg0:
                print()
                for i, data in enumerate(digitData):
                    print("%d st %3d en %3d" % (i, data.strCol, data.endCol))
                print()

            if self.plot4:
                w = lcdShape.width
                xVal = []
                yVal = []
                lo = 32
                hi = 255 - lo
                xVal.append(w)
                yVal.append(lo)
                for data in digitData:
                    xVal.append(w - data.strCol)
                    yVal.append(lo)
                    xVal.append(w - data.strCol)
                    yVal.append(hi)
                    xVal.append(w - data.endCol)
                    yVal.append(hi)
                    xVal.append(w - data.endCol)
                    yVal.append(lo)
                axs[n].plot(xVal, yVal)        
                n += 1    

        if self.plot4:
            if self.save:
                fig.savefig("plot4.png")
            else:
                plt.show()

        if self.draw:
            refDraw.save("refDraw1.png", "PNG")

            refDraw = self.refGray.copy()
            draw1 = ImageDraw.Draw(refDraw)

        if self.plot5:
            fig, axs = plt.subplots(3, 2, sharex=True)
            axs = list(np.concatenate(axs).flat)
            fig.set_figheight(2 * fig.get_figheight())
            fig.set_figwidth(2 * fig.get_figwidth())
            j = 0

        for n, data in enumerate(digitData):
            stCol = data.strCol
            enCol = data.endCol
            centerCol = data.col

            if self.draw:
                h = lcdShape.height
                draw1.line(((x0 - centerCol, 0 + y0), \
                            (x0 - centerCol, h + y0)), \
                           fill=BLACK_FILL)
                draw1.line(((x0 - stCol, 0 + y0), \
                            (x0 - stCol, h + y0)), fill=WHITE_FILL)
                draw1.line(((x0 - enCol, 0 + y0), \
                            (x0 - enCol, h + y0)), fill=WHITE_FILL)

            if self.dbg0:
                w0 = lcdShape.width
                print("%d st %3d %3d en %3d %3d c %3d %3d" % \
                      (n, stCol, w0-stCol, enCol, w0-enCol, \
                       centerCol, w0-centerCol), end="")

            if self.plot5:
                tmpCol = self.refArray[:,x0 - centerCol]
                axs[j].plot(tmpCol[lcdShape.top:lcdShape.bottom])
                axs[j].set_title("%d Column %d" % (n, centerCol))

            segRows = []
            lastPixel = 0
            findNeg = True
            for row in range(lcdShape.height):
                pixel = self.refArray[row + y0][x0 - centerCol]
                if findNeg:
                    if (pixel <= DIGIT_THRESHOLD and \
                        lastPixel >= DIGIT_THRESHOLD):
                        strRow = row
                        findNeg = False
                else:
                    h = lcdShape.height
                    if (pixel >= DIGIT_THRESHOLD and \
                        lastPixel <= DIGIT_THRESHOLD):
                        segRow = (strRow + row) // 2
                        segRows.append(segRow)
                        findNeg = True

                        if self.dbg0:
                            print(" %3d" % (segRow), end="")

                        if self.draw:
                            draw1.line(((lcdShape.left, y0 + segRow), \
                                        (lcdShape.right, y0 + segRow)), \
                                       fill=GRAY_FILL)

                        if self.plot5:
                            axs[j].plot([segRow, segRow], \
                                        [0, DIGIT_THRESHOLD])

                        if len(segRows) >= 3:
                            break
                lastPixel = pixel
                
            if len(segRows) == 3:
                data.setSegRows(segRows, lcdShape.height)

                dirStart = segRows[2]
                for row in range(dirStart, lcdShape.height):
                    pixel = self.refArray[row + y0][x0 - centerCol]
                    if pixel > DIGIT_THRESHOLD:
                        dirStart = row
                        break

                dirEnd = lcdShape.height
                lastPixel = MAX_PIXEL
                for row in range(dirEnd, dirStart, -1):
                    pixel = self.refArray[row + y0][x0 - centerCol]
                    if (pixel >= DIGIT_THRESHOLD) and \
                       (lastPixel <= DIGIT_THRESHOLD):
                        dirEnd = row - 1
                        break
                    lastPixel = pixel

                data.setDirRows(dirStart, dirEnd)
                    
            if self.dbg0:
                print()

            if self.plot5:
                j += 1

        if self.plot5:
            if self.save:
                fig.savefig("plot5.png")
            else:
                plt.show()
            
        if self.draw:
            refDraw.save("refDraw2.png", "PNG")

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
        col = x0 - data.col
        colRange = data.colRange
        
        topRow = data.topRow + y0
        botRow = data.botRow + y0
        rowRange = data.rowRange
        
        result = 0
        for i in range(colRange):
            c0 = col + i
            c1 = col - i
            pixel1 = imageArray[topRow][c0]
            if pixel1 < DIGIT_THRESHOLD:
                result |= 0x02

            pixel5 = imageArray[topRow][c1]
            if pixel5 < DIGIT_THRESHOLD:
                result |= 0x20

            pixel2 = imageArray[botRow][c0]
            if pixel2 < DIGIT_THRESHOLD:
                result |= 0x04

            pixel4 = imageArray[botRow][c1]
            if pixel4 < DIGIT_THRESHOLD:
                result |= 0x10

        for i in range(rowRange):
            r0 = topRow - i
            r1 = topRow + i
            r2 = botRow + i
            pixel0 = imageArray[r0][col]
            if pixel0 < DIGIT_THRESHOLD:
                result |= 0x01

            pixel6 = imageArray[r1][col]
            if pixel6 < DIGIT_THRESHOLD:
                result |= 0x40

            pixel3 = imageArray[r2][col]
            if pixel3 < DIGIT_THRESHOLD:
                result |= 0x08
        return result

    def readDirection(self, imageArray, lcdShape, data):
        col = lcdShape.right - data.col
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
                if lastPixel <= DIGIT_THRESHOLD and pixel >= DIGIT_THRESHOLD:
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

    def openTarget(self, targetFile, lcdShape):
        self.targetImage = Image.open(targetFile)
        self.targetGray = ImageOps.grayscale(self.targetImage)
        targetArray = np.asarray(self.targetGray)
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

    def readDisplay(self, targetArray, lcdShape, digitData):
        if self.plot6:
            fig, axs = plt.subplots(3, 2, sharex=True)
            axs = list(np.concatenate(axs).flat)
            fig.set_figheight(2 * fig.get_figheight())
            fig.set_figwidth(2 * fig.get_figwidth())
            n = 0

        if self.plot7:
            fig7, axs7 = plt.subplots(3, 2, sharex=True)
            axs7 = list(np.concatenate(axs7).flat)
            fig7.set_figheight(2 * fig7.get_figheight())
            fig7.set_figwidth(2 * fig7.get_figwidth())
            j = 0

        if self.draw:
            targetDraw = self.targetGray.copy()
            draw1 = ImageDraw.Draw(targetDraw)

        meterVal = 0
        meterMult = 1
        dirMask = 1
        dirVal = 0
        for i, data in enumerate(digitData):
            if self.plot7:
                x0 = lcdShape.right
                tmpCol = targetArray[:, x0 - data.col]
                axs7[j].plot(tmpCol[lcdShape.top:lcdShape.bottom])
                axs7[j].plot([0, data.maxRow], \
                             [DIGIT_THRESHOLD, DIGIT_THRESHOLD])
                axs7[j].set_title("%d Column %d" % (j, data.col))
                j += 1

            result = self.readSegments(targetArray, lcdShape, data, i)
            if self.dbg0:
                print("result %02x %d" % (result, self.decode(result)))
            meterVal += meterMult * self.decode(result)
            meterMult *= 10

            if self.plot6:
                x0 = lcdShape.right
                y0 = lcdShape.top
                axs[n].plot(targetArray[data.dirStart + y0:data.dirEnd + y0, \
                                        x0 - data.col])
                axs[n].plot([0, data.dirEnd - data.dirStart], \
                            [DIGIT_THRESHOLD, DIGIT_THRESHOLD])
                axs[n].set_title("Direction %d col %d" % (i, data.col))
                n += 1

            result = self.readDirection(targetArray, lcdShape, data)
            if result:
                dirVal |= dirMask
            dirMask <<= 1

            if self.draw:
                self.readDraw(draw1.line, lcdShape, data)

        if dirVal <= 0x30:
            dirVal = (dirVal, dirConv[dirVal])
        else:
            dirVal = (dirVal, 99)

        if self.plot6:
            if self.save:
                fig.savefig("plot6.png")
            else:
                plt.show()

        if self.plot7:
            if self.save:
                fig7.savefig("plot7.png")
            else:
                plt.show()

        if self.draw:
            targetDraw.save("targetDraw2.png", "PNG")

        return (meterVal, dirVal)

    def readDraw(self, d, lcdShape, data):
        y0 = lcdShape.top
        col = lcdShape.right - data.col
        colRange = data.colRange
        topRow = data.topRow + y0
        botRow = data.botRow + y0
        rowRange = data.rowRange
        dirT = data.dirStart + y0
        dirB = data.dirEnd + y0
        d(((col, topRow), (col+colRange, topRow)), fill=BLACK_FILL)
        d(((col, topRow), (col-colRange, topRow)), fill=WHITE_FILL)
        d(((col, botRow), (col+colRange, botRow)), fill=WHITE_FILL)
        d(((col, botRow), (col-colRange, botRow)), fill=BLACK_FILL)

        d(((col, topRow), (col, topRow-rowRange)), fill=BLACK_FILL)
        d(((col, topRow), (col, topRow+rowRange)), fill=WHITE_FILL)
        d(((col, botRow), (col, botRow+rowRange)), fill=BLACK_FILL)

        d(((col, dirT), (col, dirB)), fill=WHITE_FILL)

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
        self.initLoopVars()
        while True:
            contents = urllib.request.urlopen(URL).read()
            self.targetFile = io.BytesIO(contents)
            targetArray = self.openTarget(self.targetFile, lcdShape)

            if LINUX:
                # t0 = time_ns()
                update = cm.loopProcess(targetArray.ravel())
                if update:
                    cm.targetBounds(targetArray.ravel(), \
                                    len(targetArray[0]), len(targetArray))
                # tProc = time_ns() - t0
                # print("tProc %8d" % (tProc))
                sleep(.25)
                continue
            
            # t0 = time_ns()
            (val, (dirVal, dirIndex)) = \
                self.readDisplay(targetArray, lcdShape, digitData)
            # tRead = time_ns() - t0
            # print("tCheck %8d tRead %8d " % (tRead, tCheck), end="")
            # print("%d diff %6d " % (n, tmp), end="")

            if self.sync:
                # t0 = time_ns();
                self.updateReading(val)
                dirIndex = self.updateDirection(dirVal, dirIndex)
                # tRead = time_ns() - t0;
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

    def process(self):
        self.openRef()

        if self.plot1:
            self.histogram()

        # t0 = time_ns()
        lcdShape = LcdShape(self.refArray, self.dbg0)
        self.verticalBounds(lcdShape)
        self.horizontalBounds(lcdShape)
        # tSetup = time_ns() - t0
        # print("tSetup %d" % (tSetup))
        self.cropRef(lcdShape)
        lcdShape.setSize()
        digitData = self.findRefSegments(lcdShape)

        if LINUX:
            cm.cvar.dbg0 = int(self.cDbg0)
            cm.cvar.dbg1 = int(self.cDbg1)
            cm.cvar.updateEna = int(self.update)
            cm.setThresholds(COL_DELTA_THRESHOLD, DIGIT_THRESHOLD)
            cm.setSize(lcdShape.width, lcdShape.height)
            cm.setRows(lcdShape.top, lcdShape.bottom)
            cm.setColumns(lcdShape.left, lcdShape.right)
            for n, data in enumerate(digitData):
                cm.setDigitCol(data.strCol, data.endCol, n)
                cm.setSegRows(np.array(data.segRows, np.int32), n)
                cm.setDirRows(data.dirStart, data.dirEnd, n)
            cm.loopInit();
                           
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
            if LINUX and False:
                t0 = time_ns()
                cm.targetBounds(targetArray.ravel(), \
                                len(targetArray[0]), len(targetArray))
                tCBounds = time_ns() - t0
                print()
                cm.printShape();
                print()
            t0 = time_ns()
            self.targetBounds(lcdShape)
            tPBounds = time_ns() - t0
            if LINUX and False:
                print("targetBounds c %d ns python %d ns" % \
                      (tCBounds, tPBounds))
            if LINUX:
                val = 0
                dirVal = 0
                dirIndex = 0
                print("w %3d" % (len(targetArray[0])))
                (val, dirVal, dirIndex) = cm.readDisplay(targetArray.ravel())
                print("%6d 0x%02x %d" % (val, dirVal, dirIndex))
            # else:
            if True:
                t0 = time_ns()
                (val, (dirVal, dirIndex)) = \
                    self.readDisplay(targetArray, lcdShape, digitData)
                tRead = time_ns() - t0
                print("tRead %d ns" % (tRead))
            print("%6d 0x%02x %d" % (val, dirVal, dirIndex))

        # for val in vars(self).keys():
        #     print(val)
        
print(timeStr())

rm = 'rm -f '
os.system(rm + 'ref.png')
os.system(rm + 'refDraw*.png')
os.system(rm + 'targetDraw*.png')
os.system(rm + 'plot*.png')

meter = Meter()
meter.setup()
meter.process()
