#!/cygdrive/c/Python39/python.exe
#*******************************************************************************

import sys
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageOps
from time import sleep

import urllib.request
import io
from datetime import datetime
from pytz import timezone

URL = "http://192.168.42.70/capture"

WHITE_FILL = 255
BLACK_FILL = 0
GRAY_FILL  = 192

MAX_PIXEL = 255

TOP_SEG = 0.3
BOTTOM_SEG = 0.6
MARK_HEIGHT = 0.375

DELTA_THRESHOLD = 40
COL_DELTA_THRESHOLD = 100
SEG_COL_THRESHOLD = 30
SEG_ROW_THRESHOLD = 50

INITIAL_COLUMN_INDEX = 4
DIGIT_COLUMNS = 3

MAX_DIGITS = 6 - 1
SEG_ROWS = 3

tz = timezone("America/New_York")

def timeStr():
    now = datetime.now(tz=tz)
    return(now.strftime("%a %b %d %Y %H:%M:%S"))

print(timeStr())

plot1 = False                   # row histogram
plot2 = False                   # row sum array
plot3 = False                   # upper and lower row
plot4 = False                   # reference rows
plot5 = False                   # digit columns
plot6 = False                   # direction

dbg0 = False                    # general debug
dbg1 = False                    # top and bottom
dbg2 = False                    # right and left

draw = False                    # drawing on images

capture = False

loop = False

refFile = None
targetFile = None
n = 1
while True:
    if n >= len(sys.argv):
        break
    val = sys.argv[n]
    if val.startswith('-'):
        val = val[1:]
        if val.startswith('p'):
            val = int(val[1:])
            if val == 1:
                plot1 = True
            elif val == 2:
                plot2 = True
            elif val == 3:
                plot3 = True
            elif val == 4:
                plot4 = True
            elif val == 5:
                plot5 = True
            elif val == 6:
                plot6 = True
        elif val.startswith('d'):
            val = int(val[1:])
            if val == 0:
                dbg0 = True
            elif val == 1:
                dbg1 = True
            elif val == 2:
                dbg2 = True
        elif val.startswith('c'):
            capture = True
        elif val.startswith('r'):
            draw = True
        elif val.startswith('l'):
            loop = True
    elif refFile is None:
        refFile = val
    elif targetFile is None:
        targetFile = val
    n += 1

if refFile is None:
    refFile = "cRef-800x600-1.jpg"

refImage = Image.open(refFile)
refGray = ImageOps.grayscale(refImage)
refGrayArray = np.asarray(refGray)
if dbg0:
    print(len(refGrayArray), len(refGrayArray[0]), refGrayArray[0][0])

rowArray = np.rint(refGrayArray.sum(axis=1) / \
                      len(refGrayArray[0])).astype(int)

histogram = np.zeros(255)
for val in rowArray:
    histogram[val] += 1
if plot1:
    plt.plot(histogram)
    plt.title("Row Histogram")
    plt.show()

# find upper and lower bound of LCD display

minRows = []
negDelta = True
deltaTotal = 0
lastSum = rowArray[0]
strMin = MAX_PIXEL
endMin = MAX_PIXEL
for row, rSum in enumerate(rowArray):
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
                    minRows.append(start)
                    negDelta = False
                    deltaTotal = 0
                    if dbg1:
                        print()
                else:
                    deltaTotal = 0
                    strMin = MAX_PIXEL
            if dbg1:
                print("<row %3d rSum %3d delta %3d dTotal %3d" % \
                      (row, rSum, delta, deltaTotal))
        else:
            if rSum < endMin:
                endMin = rSum
                end = row

            if delta > 0:
                maxVal = rSum
                deltaTotal += delta
            else:
                if deltaTotal > DELTA_THRESHOLD:
                    minRows.append(end)
                    break
                else:
                    deltaTotal = 0
                    endMin = MAX_PIXEL
            if dbg1:
                print(">row %3d rSum %3d delta %3d dTotal %3d" % \
                      (row, rSum, delta, deltaTotal))
    lastSum = rSum

if dbg0:
    print("str %3d minVal %3d" % (start, minVal))
    print("end %3d maxVal %3d" % (end, maxVal))
    print("top %3d bottom %3d" % (minRows[0], minRows[1]))

if plot2:
    plt.plot(rowArray)
    plt.title("Row Array")
    plt.plot(minRows, [minVal, maxVal])
    plt.show()

# find left and right bound of LCD display

for row in minRows:
    deltaMin = 0
    deltaMax = 0
    negDelta = True
    deltaTotal = 0
    lastPixel = int(refGrayArray[row][0])
    startMin = MAX_PIXEL
    endMin = MAX_PIXEL
    for col, pixel in enumerate(refGrayArray[row]):
        pixel = int(pixel)
        delta = pixel - lastPixel
        if delta != 0:
            if negDelta:
                if delta < 0:
                    deltaTotal -= delta
                else:
                    if deltaTotal > COL_DELTA_THRESHOLD:
                        cropStartCol = col
                        if dbg0:
                            print("start %3d" % (start))
                        negDelta = False
                        deltaTotal = 0
                        deltaMin = pixel
                        if dbg2:
                            print()
                    else:
                        deltaTotal = 0
                if dbg2:
                    print("<col %3d pixel %3d delta %3d dTotal %3d" % \
                          (col, pixel, delta, deltaTotal))
            else:
                if delta > 0:
                    deltaTotal += delta
                else:
                    if deltaTotal > COL_DELTA_THRESHOLD:
                        if dbg0:
                            print("end %3d" % (end))
                        deltaMax = pixel
                        break
                    else:
                        deltaTotal = 0
                        cropEndCol = col
                if dbg2:
                    print(">col %3d pixel %3d delta %3d dTotal %3d" % \
                          (col, pixel, delta, deltaTotal))
        lastPixel = pixel
    if plot3:
        plt.plot(refGrayArray[row])
        plt.title("Min Row %d" % (row))
        plt.plot([cropStartCol, cropEndCol], [deltaMin, deltaMax])
        plt.show()

    if dbg0:
        print("left %3d right %3d" % (start, end))
        
refCropped = refGray.crop((cropStartCol, minRows[0], cropEndCol, minRows[1]))

if draw:
    drawImg = ImageDraw.Draw(refGray)
    drawImg.line(((cropStartCol, minRows[0]), \
                  (cropEndCol,   minRows[0])), fill=WHITE_FILL)
    drawImg.line(((cropEndCol,   minRows[0]), \
                  (cropEndCol,   minRows[1])), fill=WHITE_FILL)
    drawImg.line(((cropEndCol,   minRows[1]), \
                  (cropStartCol, minRows[1])), fill=WHITE_FILL)
    drawImg.line(((cropStartCol, minRows[1]), \
                  (cropStartCol, minRows[0])), fill=WHITE_FILL)
    refGray.save("ref.png", "PNG")

refArray = np.asarray(refCropped)

height = minRows[1] - minRows[0]
width = cropEndCol - cropStartCol
topRow = int(TOP_SEG * height)
botRow = int(BOTTOM_SEG * height)
if dbg0:
    print("width %3d height %3d pixels %5d, top %3d bottom %3d" % \
          (width, height, width * height, topRow, botRow))
    
# find location of segments on the reference array

if draw:
    refDraw = refCropped.copy()
    draw1 = ImageDraw.Draw(refDraw)
    draw1.line(((0, topRow), (width, topRow)), fill=BLACK_FILL)
    draw1.line(((0, botRow), (width, botRow)), fill=BLACK_FILL)
    refCropped.save("refDraw0.png", "PNG")

drawLine = draw

if drawLine:
    refDraw = refCropped.copy()
    draw1 = ImageDraw.Draw(refDraw)

mark = int(MARK_HEIGHT * height)
for (rowNum, markStart, markEnd) in \
    ((topRow, 0, mark), (botRow, mark, height)):
    maxPixel = 0
    minPixel = MAX_PIXEL
    findMin = True
    row = refArray[rowNum]
    if plot4:
        plt.plot(row)
        plt.title("Ref Row %d" % (rowNum))
        plt.show()
    segColumn = []
    for col in range(len(row) - 1, 0, -1):
        pixel = row[col]
        # print(i, pixel)
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


    j = 0
    flag = INITIAL_COLUMN_INDEX
    dig = 0
    last = len(row)
    digitColumns = []
    for col in segColumn:
        if (j & 1) == 0:
            fill = WHITE_FILL
            color = 'w'
        else:
            fill = BLACK_FILL
            color = 'b'
        if drawLine:
            draw1.line(((col, markStart), (col, markEnd)), fill=fill)
        deltaCol = last - col
        if flag == 0:
            flag = DIGIT_COLUMNS
            if dig <= MAX_DIGITS:
                if dig < MAX_DIGITS:
                    gap = (col - segColumn[j+1]) // 2
                st = segColumn[j-3] + gap
                if dig < MAX_DIGITS:
                    en = col - gap
                    w = st - en
                else:
                    en = st - w
                digitColumns.append((st, en))
                m = "%d %3d %3d %2d" % (dig, st, en, w)
                if markStart == 0:
                    if drawLine:
                        draw1.line(((st, markStart), (st, markEnd)), \
                                  fill=GRAY_FILL)
                        if dig == MAX_DIGITS:
                            draw1.line(((en, markStart), (en, markEnd)), \
                                      fill=GRAY_FILL)
                dig += 1
        else:
            flag -= 1
            m = " "
        if dbg0:
            print("%2d %3d delta %3d %s %d %s" % \
                  (j, col, deltaCol, color, flag, m))
        j += 1
        last = col

    if dbg0:
        print()
        for i, (st, en) in enumerate(digitColumns):
            print("%d st %3d en %3d" % (i, st, en))
        print()

if drawLine:
    refDraw.save("refDraw1.png", "PNG")

if draw:
    refDraw = refCropped.copy()
    draw1 = ImageDraw.Draw(refDraw)

if dbg0:
    print("refArray %d %d" % (len(refArray), len(refArray[0])))

for n in range(len(digitColumns)):
    (stCol, enCol) = digitColumns[n]
    centerCol = (stCol + enCol) // 2
    col = refArray[:, centerCol]
    if draw:
        draw1.line(((centerCol, 0), (centerCol, len(col))), fill=BLACK_FILL)
        draw1.line(((stCol, 0), (stCol, len(col))), fill=WHITE_FILL)
        draw1.line(((enCol, 0), (enCol, len(col))), fill=WHITE_FILL)
    if dbg0:
        print("%d st %3d en %3d c %3d" % (n, stCol, enCol, centerCol), end="")
    
    if plot5:
        plt.plot(col)
        plt.title("%d Column %d" % (n, centerCol))
    minPixel = MAX_PIXEL
    segRows = []
    pixelVal = []
    last = col[0]
    for row, pixel in enumerate(col):
        if pixel < last:
            if row > 3:
                if pixel < minPixel:
                    minPixel = pixel
                    minRow = row
        else:
            if (pixel - minPixel) > SEG_ROW_THRESHOLD:
                if dbg0:
                    print(" %3d" % (minRow), end="")
                if draw:
                    draw1.line(((stCol, minRow), (enCol, minRow)), \
                               fill=GRAY_FILL)
                segRows.append(minRow)
                pixelVal.append(minPixel)
                minPixel = MAX_PIXEL
                if len(segRows) == SEG_ROWS:
                    break
        last = pixel
    if dbg0:
        print()
    if plot5:
        plt.plot(segRows, pixelVal)
        plt.show()

if draw:
    refDraw.save("refDraw2.png", "PNG")

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

def decode(result):
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

# for i, result in enumerate((0x3f, 0x06, 0x5b, 0x4f, \
#                             0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x67)):
#     val = decode(result)
#     print("%d %02x %d %s" % (i, result, val, "*" if val == i else ""))

threshold = 75

def findSegments(imageArray, col, colRange, topRow, botRow, rowRange):
    # print("col %3d colRange %2d topRow %2d botRow %2d rowRange %2d" % \
    #       (col, colRange, topRow, botRow, rowRange))
    # sys.stdout.flush()
    result = 0
    for i in range(colRange):
        c0 = col + i
        c1 = col - i
        pixel1 = imageArray[topRow][c0]
        if pixel1 < threshold:
            result |= 0x02

        pixel5 = imageArray[topRow][c1]
        if pixel5 < threshold:
            result |= 0x20

        pixel2 = imageArray[botRow][c0]
        if pixel2 < threshold:
            result |= 0x04

        pixel4 = imageArray[botRow][c1]
        if pixel4 < threshold:
            result |= 0x10

    for i in range(rowRange):
        r0 = topRow - i
        r1 = topRow + i
        r2 = botRow + i
        pixel0 = imageArray[r0][col]
        if pixel0 < threshold:
            result |= 0x01

        pixel6 = imageArray[r1][col]
        if pixel6 < threshold:
            result |= 0x40

        pixel3 = imageArray[r2][col]
        if pixel3 < threshold:
            result |= 0x08
    return result

def findDirection(imageArray, col, startRow, rowRange):
    skip = True
    lastPixel = 0
    # print("\ncol %3d" % (col))
    result = 0
    for row in range(startRow, startRow + rowRange):
        pixel = imageArray[row][col]
        # print("%2d pixel %3d skip %s" % (row, pixel, skip))
        if skip:
            if pixel > threshold:
                skip = False
        else:
            if lastPixel <= threshold and pixel >= threshold:
                result = 1
                break
        lastPixel = pixel
    # print("result %d" % (result))
    return result

def saveError(image, ctr, errCtr):
    print("errctr %d" % (errCtr))
    name = "err-%03d-%d-%s.png" % (errCtr, ctr, timeStr()[4:])
    name = name.replace(' ', '_')
    name = name.replace(':', '-')
    image.save(name, 'PNG')

stCol = digitColumns[0][0]
enCol = digitColumns[-1][1]
topRow = (segRows[0] + segRows[1]) // 2
botRow = (segRows[1] + segRows[2]) // 2

if (targetFile is None) and (not capture):
    targetFile = refFile

lastVal = 0
lastDir = 0
sync = False
meterVal = [888888, 0, 0, 0]
ctr = 0
errCtr = 0
while True:
    if capture:
        contents = urllib.request.urlopen(URL).read()
        targetFile = io.BytesIO(contents)
        if False:
            f = open("input.jpg", "wb")
            f.write(contents)
            f.close()

    targetImage = Image.open(targetFile)
    targetGray = ImageOps.grayscale(targetImage)
    targetCropped = targetGray.crop((cropStartCol, minRows[0],
                                     cropEndCol, minRows[1]))
    targetArray = np.asarray(targetCropped)

    if draw:
        targetDraw = targetCropped.copy()
        draw1 = ImageDraw.Draw(targetDraw)

    # draw1.line(((stCol, topRow), (enCol, topRow)), fill=GRAY_FILL)
    # draw1.line(((stCol, botRow), (enCol, botRow)), fill=GRAY_FILL)

    rowRange = (segRows[1] - segRows[0]) // 2 + 2
    val = 0
    mult = 1
    dirMask = 1
    dirVal = 0
    for i, (stCol, enCol) in enumerate(digitColumns):
        # print("st %3d en %3d" % (st, en))
        col = (stCol + enCol) // 2
        colRange = (stCol - enCol) // 2
        result = findSegments(targetArray, col, colRange, \
                              topRow, botRow, rowRange)
        if dbg0:
            print("result %02x %d" % (result, decode(result)))
        val += mult * decode(result)
        mult *= 10

        if plot6:
            plt.plot(targetArray[botRow + rowRange:, col])
            plt.title("Direction %d col %d" % (i, col))
            plt.show()
            
        dirStart = botRow + rowRange
        dirRange = ((len(targetArray) - dirStart) * 3) // 4
        result = findDirection(targetArray, col, dirStart, dirRange)
        if result:
            dirVal |= dirMask
        dirMask <<= 1

        if draw:
            d = draw1.line
            d(((col, topRow), (col+colRange, topRow)), fill=BLACK_FILL)
            d(((col, topRow), (col-colRange, topRow)), fill=WHITE_FILL)
            d(((col, botRow), (col+colRange, botRow)), fill=WHITE_FILL)
            d(((col, botRow), (col-colRange, botRow)), fill=BLACK_FILL)

            d(((col, topRow), (col, topRow-rowRange)), fill=BLACK_FILL)
            d(((col, topRow), (col, topRow+rowRange)), fill=WHITE_FILL)
            d(((col, botRow), (col, botRow+rowRange)), fill=BLACK_FILL)

    if capture:
        if sync:
            # print("%d %6d 0x%02x" % (ctr, val, dirVal))
            if val != lastVal:
                ctr += 1
                if ctr >= 4:
                    ctr = 0
                    if val != 888888:
                        print("%s expected 888888 read %d" % \
                              (timeStr(), val))
                        saveError(targetImage, ctr, errCtr)
                        errCtr += 1
                        sync = False
                meter = meterVal[ctr]
                if val != meter:
                    if meter == 0:
                        delta = 0
                    else:
                        delta = val - meter
                    print("%s %d val %6d meter %6d delta %2d" % \
                          (timeStr(), ctr, val, meter, val - meter))
                    if abs(delta) <= 1:
                        meterVal[ctr] = val
                    else:
                        saveError(targetImage, ctr, errCtr)
                        errCtr += 1
        else:
            if val != lastVal:
                print(val)
            if dirVal != lastDir:
                print("0x%02x" % (dirVal))
            if val == 888888:
                print("sync")
                sync = True
                ctr = 0
    else:
        print("%6d 0x%02x" % (val, dirVal))
        
    if not loop:
        break
    lastVal = val
    lastDir = dirVal
    sleep(1)

if draw:
    targetDraw.save("targetDraw0.png", "PNG")

    refCropped.save("refCropped.png", "PNG")
    targetCropped.save("targetCropped.png", "PNG")
