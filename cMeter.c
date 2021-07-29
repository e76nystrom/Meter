#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>
#include <stdlib.h>
#include <time.h>

#if defined(__arm__)
#include <wiringPi.h>
#endif

#define DIR_INV 99

int dirConv[] =
{ 
 DIR_INV,			// 0x00
 DIR_INV,			// 0x01
 DIR_INV,			// 0x02
 0,				// 0x03
 DIR_INV,			// 0x04
 DIR_INV,			// 0x05
 1,				// 0x06
 DIR_INV,			// 0x07
 DIR_INV,			// 0x08
 DIR_INV,			// 0x09
 DIR_INV,			// 0x0A
 DIR_INV,			// 0x0B
 2,				// 0x0C
 DIR_INV,			// 0x0D
 DIR_INV,			// 0x0E
 DIR_INV,			// 0x0F
 DIR_INV,			// 0x10
 DIR_INV,			// 0x11
 DIR_INV,			// 0x12
 DIR_INV,			// 0x13
 DIR_INV,			// 0x14
 DIR_INV,			// 0x15
 DIR_INV,			// 0x16
 DIR_INV,			// 0x17
 3,				// 0x18
 DIR_INV,			// 0x19
 DIR_INV,			// 0x1A
 DIR_INV,			// 0x1B
 DIR_INV,			// 0x1C
 DIR_INV,			// 0x1D
 DIR_INV,			// 0x1E
 DIR_INV,			// 0x1F
 DIR_INV,			// 0x20
 5,				// 0x21
 DIR_INV,			// 0x22
 DIR_INV,			// 0x23
 DIR_INV,			// 0x24
 DIR_INV,			// 0x25
 DIR_INV,			// 0x26
 DIR_INV,			// 0x27
 DIR_INV,			// 0x28
 DIR_INV,			// 0x29
 DIR_INV,			// 0x2A
 DIR_INV,			// 0x2B
 DIR_INV,			// 0x2C
 DIR_INV,			// 0x2D
 DIR_INV,			// 0x2E
 DIR_INV,			// 0x2F
 4,				// 0x30
};

extern int dbg0;
extern int dbg1;
extern int updateEna;

#define MAX_PIXEL 255
int COL_DELTA_THRESHOLD = 100;
int DIGIT_THRESHOLD = 75;

void setThresholds(int col, int digit)
{
 COL_DELTA_THRESHOLD = col;
 DIGIT_THRESHOLD = digit;
}

typedef struct
{
 uint8_t *rArray;
 int rLen;
 int rArrayH;
 int rArrayW;

 uint8_t *tArray;
 int tLen;
 int tArrayW;
 int tArrayH;

 int top;
 int bottom;
 int height;
 
 int left;
 int right;
 int width;

 int topRow;
 int botRow;

 bool update;
} T_LCD_SHAPE, *P_LCD_SHAPE;

T_LCD_SHAPE shape;

typedef struct
{
 int strCol;
 int endCol;
 int col;
 int colRange;

 int segRows[3];
 int maxRow;
 int topRow;
 int botRow;
 int rowRange;

 int dirStart;
 int dirRange;
} T_DIGIT_DATA, *P_DIGIT_DATA;

#define TOP_SEG 0.3
#define BOTTOM_SEG 0.6

T_DIGIT_DATA digitData[6];

// a = numpy.empty([800, 600], numpy.uint8)
// a[0][0] = 255
// cMeter.setArray(a.ravel())

#if defined(__arm__)

const int dbg0Pin = 5;
const int dbg1Pin = 6;
const int dbg2Pin = 21;

void piInit(void)
{
 wiringPiSetup();

 pinMode(dbg0Pin, OUTPUT);
 pinMode(dbg1Pin, OUTPUT);
 pinMode(dbg2Pin, OUTPUT);
}

inline void dbg0Set(void)
{
 digitalWrite(dbg0Pin, HIGH);
}

inline void dbg0Clr(void)
{
 digitalWrite(dbg0Pin, LOW);
}

inline void dbg1Set(void)
{
 digitalWrite(dbg1Pin, HIGH);
}

inline void dbg1Clr(void)
{
 digitalWrite(dbg1Pin, LOW);
}

inline void dbg2Set(void)
{
 digitalWrite(dbg2Pin, HIGH);
}

inline void dbg2Clr(void)
{
 digitalWrite(dbg2Pin, LOW);
}

#else

void piInit(void) {}
inline void dbg0Set(void) {}
inline void dbg0Clr(void) {}
inline void dbg1Set(void) {}
inline void dbg1Clr(void) {}
inline void dbg2Set(void) {}
inline void dbg2Clr(void) {}

#endif

char *month[] =
{
 "Jan", "Feb", "Mar", "Apr", "May", "Jun",
 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
};

char *timeStr(char *buf, int len)
{
 time_t now;
 time(&now);
 struct tm local;
 localtime_r(&now, &local);

 snprintf(buf, len, "%3s_%02d_%4d_%02d-%02d-%02d",
	  month[local.tm_mon], local.tm_mday, local.tm_year + 1900,
	  local.tm_hour, local.tm_min, local.tm_sec);
 return buf;
}

void setRef(uint8_t *array, int n, int w, int h)
{
 shape.rArray = array;
 shape.rLen = n;
 shape.rArrayW = w;
 shape.rArrayH = h;

 if (dbg0)
  printf("setRef %d n %d w %d h %d\n", *array, n, w, h);
}

void setTarget(uint8_t *array, int n, int w, int h)
{
 shape.tArray = array;
 shape.tLen = n;
 shape.tArrayW = w;
 shape.tArrayH = h;

 if (dbg0)
  printf("setTarget %d n %d w %d h %d\n", *array, n, w, h);
}

void setSize(int width, int height)
{
 shape.width = width;
 shape.height = height;
 shape.topRow = (int) (TOP_SEG * height);
 shape.botRow = (int) (BOTTOM_SEG * height);
 if (dbg0)
  printf("width %3d height %3d size %5d\n", width, height, width * height);
}

void setRows(int top, int bottom)
{
 shape.top = top;
 shape.bottom = bottom;
 if (dbg0)
  printf("setRows top %3d bottom %3d\n", shape.top, shape.bottom);
}

void getRows(int *tVal, int *bVal)
{
 *tVal = shape.top;
 *bVal = shape.bottom;
}

void setColumns(int left, int right)
{
 shape.left = left;
 shape.right = right;
 if (dbg0)
  printf("setColumns left %3d right %3d\n", shape.left, shape.right);
}

void getColumns(int *lVal, int *rVal)
{
 *lVal = shape.left;
 *rVal = shape.right;
}

void updateRows(int top, int bottom)
{
 int deltaT = top - shape.top;
 int deltaB = bottom - shape.bottom;
 if ((deltaT != 0) || (deltaB != 0))
 {
  if ((abs(deltaT) < 10) && (abs(deltaB) < 10))
  {
   char buf[24];
   if (updateEna)
   {
    shape.top = top;
    shape.bottom = bottom;
   }
   if (1)
    printf("%s updateRows top %3d d %3d bottom %3d d %3d\n",
	   timeStr(buf, sizeof(buf)),shape.top, deltaT, shape.bottom, deltaB);
  }
 }
}

void updateColumns(int left, int right)
{
 int deltaL = left - shape.left;
 int deltaR = right - shape.right;
 if ((deltaL != 0) || (deltaR != 0))
 {
  if ((abs(deltaL) < 10) && (abs(deltaR) < 10))
  {
   if (updateEna)
   {
    shape.left = left;
    shape.right = right;
   }
   if (1)
   {
    char buf[24];
    printf("%s updateCols left %3d d %3d right %3d d %3d\n",
	   timeStr(buf, sizeof(buf)), shape.left, deltaL, shape.right, deltaR);
   }
  }
 }
}

void printShape(void)
{
 printf("top %3d bottom %3d\n", shape.top, shape.bottom);
 printf("left %3d right %3d\n", shape.left, shape.right);
 printf("width %3d height %3d size %5d\n",
	shape.width, shape.height, shape.width * shape.height);
}
  
void setDigitCol(int strCol, int endCol, int index)
{
// printf("strcol %3d endCol %3d\n", strCol, endCol);
 P_DIGIT_DATA digit = &digitData[index];
 digit->strCol = strCol;
 digit->endCol = endCol;
 digit->col = (strCol + endCol) / 2;
 digit->colRange = (endCol - strCol) / 2;
}

void setSegRows(int *segRows, int n, int index)
{
//  printf("index %d segRows %3d %3d %3d\n",
//	index, segRows[0], segRows[1], segRows[2]);
 P_DIGIT_DATA digit = &digitData[index];
 memcpy((void *) (digit->segRows), (void *) segRows, 3 * sizeof(int));

 digit->topRow = (segRows[0] + segRows[1]) / 2;
 digit->botRow = (segRows[1] + segRows[2]) / 2;
 digit->rowRange = (segRows[1] - segRows[0]) / 2 + 2;
 digit->dirStart = segRows[2];
 digit->dirRange = ((shape.height - digit->dirStart) * 7) / 8;
}

void targetBounds(uint8_t *array, int n, int w, int h)
{
 if (dbg0)
  printf("\ncMeter targetBounds w %3d h %3d threshold %3d\n",
	 w, h, COL_DELTA_THRESHOLD);
 int cr = (int) (shape.width * 0.10);
 int lc = shape.left;
 int rc = shape.right;
 int rr = (int) (shape.height * 0.20);
 int vBounds[2] = {shape.top, shape.bottom};
 if (dbg0)
 {
  printf("left %3d right %3d top %3d bottom %3d\n",
	 shape.left, shape.right, shape.top, shape.bottom);
  printf("lc %3d rc %3d cr %3d tr %3d br %3d rr %3d\n",
	 lc, rc, cr, vBounds[0], vBounds[1], rr);
 }
 int rows[2];
 int cols[2][2];
 for (int i = 0; i < 2; i++)
 {
  int r = vBounds[i];
  if (dbg0)
   printf("\ni %d r %3d\n", i, r);
  uint8_t minSum = MAX_PIXEL;
  int r0 = 0;
  for (int row = r - rr; row < r + rr; row += 1)
  {
   int index = row * w;
   int rSum = 0;
   for (int k = index + lc - cr; k < index + rc + cr; k++)
   {
    rSum += array[k];
   }
   rSum /= (rc - lc + 2 * cr);
   if (rSum < minSum)
   {
    minSum = rSum;
    r0 = row;
   }
  }
  rows[i] = r0;
  if (dbg0)
   printf("%d row %3d\n", i, r0);

  int deltaTotal = 0;
  int lastPixel = 0;
  int index = r0 * w;
  for (int col = lc - cr; col < lc + cr; col++)
  {
   int pixel = array[index + col];
   int delta = pixel - lastPixel;
   if (delta != 0)
   {
    if (delta < 0)
    {
     deltaTotal -= delta;
    }
    else
    {
     if (deltaTotal > COL_DELTA_THRESHOLD)
     {
      cols[i][0] = col;
      break;
     }
     deltaTotal = 0;
    }
    if (dbg0)
     printf("<col %3d pixel %3d delta %3d dTotal %3d\n",
	    col, pixel, delta, deltaTotal);
   }
   lastPixel = pixel;
  }
  if (dbg0)
   printf("\n");
  
  deltaTotal = 0;
  lastPixel = 0;
  for (int col = rc - cr; col < rc + cr; col++)
  {
   int pixel = array[index + col];
   int delta = pixel - lastPixel;
   if (delta > 0)
   {
    deltaTotal += delta;
    if (deltaTotal > COL_DELTA_THRESHOLD)
     break;
   }
   else
   {
    deltaTotal = 0;
    cols[i][1] = col;
   }
   lastPixel = pixel;
   if (dbg0)
    printf(">col %3d pixel %3d delta %3d dTotal %3d\n",
	   col, pixel, delta, deltaTotal);
  }
  if (dbg0)
   printf("row %3d left %3d right %3d\n", rows[i], cols[i][0], cols[i][1]);
 }
 updateRows(rows[0], rows[1]);
 updateColumns(cols[0][0], cols[0][1]);
 if (dbg0)
  printf("\n");
}

int decode(int result)
{
 int val;
 if ((result & 0x20) != 0)
 {
  if ((result & 0x10) != 0)
  {
   if ((result & 0x40) != 0)
   {
    if ((result & 0x02) != 0)
     val = 8;
    else
     val = 6;
   }
   else
    val = 0;
  }
  else
  {
   if ((result & 0x01) != 0)
   {
    if ((result & 0x02) != 0)
     val = 9;
    else
     val = 5;
   }
   else
    val = 4;
  }
 }
 else
 {
  if ((result & 0x40) != 0)
  {
   if ((result & 0x04) != 0)
    val = 3;
   else
    val = 2;
  }
  else
  {
   if ((result & 0x01) != 0)
    val = 7;
   else
   {
    if ((result & 0x02) != 0)
     val = 1;
    else
     val = 0;
   }
  }
 }
 return(val);
}

void testDecode(void)
{
 uint8_t ch[] = {0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x67};
 for (size_t i = 0; i < sizeof(ch); i++)
 {
  int result = ch[i];
  int val = decode(result);
  printf("%d %02x %d %c\n", (int) i, result, val, val == (int) i ? '*' : ' ');
 }
}

int readSegments(uint8_t *array, int n, int index)
{
 P_DIGIT_DATA data = &digitData[index];
 int x0 = shape.right;
 int y0 = shape.top;
 int w = shape.tArrayW;
 int col = x0 - data->col;
 int cr = data->colRange;

 int tr = (data->topRow + y0) * w;
 int br = (data->botRow + y0) * w;
 int rr = data->rowRange;

 int result = 0;
 for (int i = 0; i < cr; i++)
 {
  if (array[tr + col + i] < DIGIT_THRESHOLD)
   result |= 0x02;

  if (array[tr + col - i] < DIGIT_THRESHOLD)
   result |= 0x20;

  if (array[br + col + i] < DIGIT_THRESHOLD)
   result |= 0x04;

  if (array[br + col - i] < DIGIT_THRESHOLD)
   result |= 0x10;
 }

 int trc = tr + col;
 int brc = br + col;
 for (int i = 0; i < rr; i++)
 {
  int r0 = i * w;

  if (array[trc - r0] < DIGIT_THRESHOLD)
   result |= 0x01;
  
  if (array[trc + r0] < DIGIT_THRESHOLD)
   result |= 0x40;
  
  if (array[brc + r0] < DIGIT_THRESHOLD)
   result |= 0x08;
 }
 return(result);
}

int readDirection(uint8_t *array, int n, int index)
{
 P_DIGIT_DATA data = &digitData[index];
 int w = shape.tArrayW;
 int col = shape.right - data->col;
 int startRow = data->dirStart + shape.top;
 int rowRange = data->dirRange;
 bool skip = true;
 int lastPixel = 0;
 int result = 0;
 for (int row = startRow; row < startRow + rowRange; row++)
 {
  int pixel = array[row * w + col];
  if (skip)
  {
   if (pixel > DIGIT_THRESHOLD)
    skip = false;
  }
  else
  {
   if ((lastPixel <= DIGIT_THRESHOLD) && (pixel >= DIGIT_THRESHOLD))
   {
    result = 1;
    break;
   }
  }
  lastPixel = pixel;
 }
 return(result);
}

typedef struct
{
 bool sync;
 int lastVal;
 int lastTmp;
 int check;
 int ctr;
 int delta;
 int meterVal[4];
 int lastDir;
 int dirSign;
 int net;
 int fwd;
 int rev;
} T_METER, *P_METER;

T_METER m;

void loopInit(void)
{
 memset((void *) &m, 0, sizeof(m));
}

void updateReading(int val)
{
 if (val != m.lastVal)
 {
  if (val != m.lastTmp)
  {
   m.lastTmp = val;
   m.check = 0;
   return;
  }
  else
  {
   m.check += 1;
   if (m.check < 2)
    return;
  }
  m.lastTmp = -1;

  int nxtCtr = m.ctr + 1;
  if (nxtCtr >= 4)
  {
   nxtCtr = 0;
   if (val == 888888)
   {
    shape.update = true;
    m.ctr = nxtCtr;
   }
   else
    m.sync = false;
  }
  else
  {
   int meter = m.meterVal[nxtCtr];
   int delta = meter == 0 ? 0 : val - meter;
   if (abs(delta) <= 1)
   {
    char buf[24];
    printf("%s %d val %6d meter %6d delta %2d "\
	   "n %5d r %5d f %5d\n",
	   timeStr(buf, sizeof(buf)), nxtCtr, val, meter, delta,
	    m.net, m.rev, m.fwd);
    m.ctr = nxtCtr;
    m.meterVal[nxtCtr] = val;
    if (delta != 0)
    {
     switch (nxtCtr)
     {
     case 0:
      break;
     case 1:
      m.net = 0;
      break;
     case 2:
      m.fwd = 0;
      break;
     case 3:
      m.rev = 0;
      break;
     }
    }
   }
   else
    val = m.lastVal;
  }
  m.lastVal = val;
 }
}

int updateDirection(int dirIndex)
{
 if (dirIndex != m.lastDir)
 {
  if (dirIndex == DIR_INV)
  {
   dirIndex = m.lastDir;
   if (m.dirSign > 0)
   {
    dirIndex += 1;
    if (dirIndex > 5)
     dirIndex = 0;
   }
   else if (m.dirSign < 0)
   {
    dirIndex -= 1;
    if (dirIndex < 0)
     dirIndex = 5;
   }
   printf("*+dirIndex %d lastDir %d\n", dirIndex, m.lastDir);
  }

  int delta = dirIndex - m.lastDir;
  if (m.dirSign > 0)
  {
   if (delta <= -3)
    delta += 6;
  }
  else if (m.dirSign < 0)
  {
   if (delta >= 3)
    delta -= 6;
  }

  m.net += delta;
  if (delta > 0)
  {
   m.rev += delta;
   m.dirSign = 1;
  }
  else if (delta < 0)
  {
   m.fwd -= delta;
   m.dirSign = -1;
  }

  m.delta = delta;
  m.lastDir = dirIndex;
 }
 return dirIndex;
}
 
void readDisplay(uint8_t *array, int n, int *val,
		 int *dirIndex, int *dirVal)
{
 int meterVal = 0;
 int meterMult = 1;
 int dirV = 0;
 int dirM = 1;
 for (int i = 0; i < 6; i++)
 {
  int result = readSegments(array, n, i);
  meterVal += meterMult * decode(result);
  meterMult *= 10;

  result = readDirection(array, n, i);
  if (result != 0)
   dirV |= dirM;
  dirM <<= 1;
 }
 *val = meterVal;
 *dirVal = dirV;
 *dirIndex = dirV <= 0x30 ? dirConv[dirV] : DIR_INV;
}

int loopProcess(uint8_t *array, int n)
{
 int val;
 int dirIndex;
 int dirVal;
 readDisplay(array, n, &val, &dirIndex, &dirVal);
 shape.update = false;
 if (m.sync)
 {
  updateReading(val);
  dirIndex = updateDirection(dirIndex);
  printf("%d %6d 0x%02x %d %2d n %3d f %3d r %3d\n",
	 m.ctr, val, dirVal, dirIndex, m.delta,
	 m.net, m.fwd, m.rev);
  m.delta = 0;
 }
 else
 {
  printf("%2d %6d 0x%02x %2d\n", m.check, val, dirVal, dirIndex);
  if (val != m.lastVal)
  {
   if (val != m.lastTmp)
   {
    m.lastTmp = val;
    m.check = 0;
    return(0);
   }
   else
   {
    m.check += 1;
    if (m.check < 2)
     return(0);
    m.check = 0;
   }
   m.lastTmp = -1;

   if (val == 888888)
   {
    printf("sync\n");
    m.sync = true;
    m.ctr = 0;
   }
   m.lastVal = val;
  }

  updateDirection(dirIndex);
 }
 fflush(stdout);
 return(shape.update);
}

double inplace(double *invec, int n)
{
 int i;

 double sum = 0;
 for (i=0; i<n; i++)
 {
  sum += invec[i];
  invec[i] = 2*invec[i];
 }
 return(sum);
}

int arrayTest(uint8_t *array, int n, int w, int row, int col)
{
 return(array[row * w + col]);
}
