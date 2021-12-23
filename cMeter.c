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

const int dirConv[] =
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

int dbg0 = false;
int dbg1 = false;
int dbg2 = false;
extern int updateEna;

#define ROW_LEN 800
#define COL_LEN 600

#define UPD_COUNT 3

#define MAX_COL 24
#define INITIAL_COLUMN_INDEX 3
#define DIGIT_COLUMNS 3
#define MAX_DIGITS 6
#define SEGMENTS 7
#define SEG_ROWS 6
#define DELTA_OFS 5

extern double TARGET_COLUMN_RANGE;
extern double TARGET_ROW_RANGE;
extern int SUM_THRESHOLD;

extern int DIGIT_THRESHOLD;

#define MAX_PIXEL 255

int targetUpdFlag;		/* target updated flag */
int drawTargetErrFlag;		/* draw target error */
int drawTargetDbgFlag;		/* draw target dbg */

uint8_t targetArray[ROW_LEN * COL_LEN];

int targetRows[2];
int targetCols[2];

int segCol0[MAX_COL];
int segCol1[MAX_COL];

int *seg[] = {segCol0, segCol1};

void getSegColumn(int *segCol, int n, int index)
{
 int *segColumn = seg[index];
 if (dbg0)
  printf("getSegColumn %d\n", n);
 for (int i = 0; i < n; i++)
  *segCol++ = *segColumn++;
}

int avgPixel0[ROW_LEN];
int avgPixel1[ROW_LEN];

int *avgPixelData[] = {avgPixel0, avgPixel1};

void getAvgPixel(uint8_t *array, int n, int index)
{
 int *avgPixel = avgPixelData[index];
 for (int i = 0; i < n; i++)
  *array++ = (uint8_t) (*avgPixel++);
}

typedef struct sLcdShape
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

typedef struct sUpdShape
{
 int lastT;
 int lastB;
 int rowCount;
 
 int lastL;
 int lastR;
 int colCount;
} T_UPD_SHAPE, *P_UPD_SHAPE;

T_UPD_SHAPE updShape;

typedef struct sSegData
{
 int start;
 int offset;
} T_SEG_DATA, *P_SEG_DATA;

typedef struct sDigitData
{
 int strCol[2];
 int endCol[2];
 int col[2];
 int colRange[2];

 int segRows[SEG_ROWS];
 int maxRow;
 int topRow;
 int botRow;
 int rrT;
 int rrC;
 int rrB;

 int dirStart;
 int dirEnd;

 T_SEG_DATA segments[SEGMENTS];
 int result;
} T_DIGIT_DATA, *P_DIGIT_DATA;

#define TOP_SEG 0.3
#define BOTTOM_SEG 0.6

T_DIGIT_DATA digitData[MAX_DIGITS];

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
 int netTotal;
 int fwdTotal;
 int revTotal;
} T_METER, *P_METER;

T_METER m;

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

const char *month[] =
{
 "Jan", "Feb", "Mar", "Apr", "May", "Jun",
 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
};

char *timeStr(char *buf, int len)
{
#if defined(__GNUC__)
 time_t now;
 time(&now);
 struct tm local;
 localtime_r(&now, &local);
#endif

#if defined(_WIN64)
 __time64_t now;
 struct tm local;
 _time64(&now);
 _localtime64_s(&local, &now);
#endif

 snprintf(buf, len, "%3s_%02d_%4d_%02d-%02d-%02d",
	  month[local.tm_mon], local.tm_mday, local.tm_year + 1900,
	  local.tm_hour, local.tm_min, local.tm_sec);
 return buf;
}

void dbgSet(int index, int val)
{
 switch (index)
 {
 case 0:
  dbg0 = val;
  break;

 case 1:
  dbg1 = val;
  break;

 case 2:
  dbg2 = val;
  break;

 default:
  break;
 }
}

void setRef(uint8_t *array, int n, int w, int h)
{
 shape.rArray = array;
 shape.rLen = n;
 shape.rArrayW = w;
 shape.rArrayH = h;

 if (dbg0)
 {
  printf("setRef %d n %d w %d h %d\n", *array, n, w, h);
  fflush(stdout);
 }
}

void setTarget(uint8_t *array, int n, int w, int h)
{
 shape.tArray = array;
 shape.tLen = n;
 shape.tArrayW = w;
 shape.tArrayH = h;

 if (dbg0)
 {
  printf("setTarget %d n %d w %d h %d\n", *array, n, w, h);
  fflush(stdout);
 }
}

void setSize(int width, int height)
{
 shape.width = width;
 shape.height = height;
 shape.topRow = (int) (TOP_SEG * height);
 shape.botRow = (int) (BOTTOM_SEG * height);
 if (dbg0)
  printf("setSize w %3d h %3d tr %3d br %3d\n",
	 width, height, shape.topRow, shape.botRow);
}

void setRows(int top, int bottom)
{
 shape.top = top;
 shape.bottom = bottom;
 if (dbg0)
 {
  printf("setRows t %3d b %3d\n", shape.top, shape.bottom);
  fflush(stdout);
 }
}

void setColumns(int left, int right)
{
 shape.left = left;
 shape.right = right;
 if (dbg0)
 {
  printf("setColumns l %3d r %3d\n", shape.left, shape.right);
  fflush(stdout);
 }
}

void updateSize()
{
 shape.height = (shape.bottom - shape.top) + 1;
 shape.width = (shape.right - shape.left) + 1;
 shape.topRow = (int) (TOP_SEG * shape.height);
 shape.botRow = (int) (BOTTOM_SEG * shape.height);
 if (dbg0)
 {
  printf("updSize w %3d h %3d tr %3d br %3d\n",
	shape. width, shape.height, shape.topRow, shape.botRow);
  fflush(stdout);
 }
}

void targetUpdate()
{
 setRows(targetRows[0], targetRows[1]);
 setColumns(targetCols[0], targetCols[1]);
 updateSize();
}

void getRows(int *tVal, int *bVal)
{
 *tVal = shape.top;
 *bVal = shape.bottom;
}

void getColumns(int *lVal, int *rVal)
{
 *lVal = shape.left;
 *rVal = shape.right;
}

void getSize(int *hVal, int *wVal, int *tRowVal, int *bRowVal)
{
 *hVal = shape.height;
 *wVal = shape.width;;
 *tRowVal = shape.topRow;
 *bRowVal = shape.botRow;;
}
  
void printShape(void)
{
 printf("c t %3d b %3d ", shape.top, shape.bottom);
 printf("l %3d r %3d ", shape.left, shape.right);
 printf("w %3d h %3d s %5d ",
	shape.width, shape.height, shape.width * shape.height);
 printf("tr %3d br %3d\n", shape.topRow, shape.botRow);
 fflush(stdout);
}

bool updateRows(int top, int bottom, int upd)
{
 bool rtn = false;
 if (upd)
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
     printf("t %3d %3d b %3d %3d rowCount %d\n",
	    shape.top, updShape.lastT, shape.bottom, updShape.lastB,
	    updShape.rowCount);
 
     if ((shape.top != updShape.lastT) || (shape.bottom != updShape.lastB))
     {
      updShape.lastT = shape.top;
      updShape.lastB = shape.bottom;
      updShape.rowCount = UPD_COUNT;
     }
     else
     {
      if (updShape.rowCount != 0)
      {
       updShape.rowCount -= 1;
       if (updShape.rowCount == 0)
       {
	shape.top = top;
	shape.bottom = bottom;
	shape.height = (shape.bottom - shape.top) + 1;
	shape.topRow = (int) (TOP_SEG * shape.height);
	shape.botRow = (int) (BOTTOM_SEG * shape.height);
	rtn = true;
       }
      }
     }
    }
 
    if (1)
     printf("%s updateRows %d t %3d d %3d b %3d d %3d u %d ctr %d\n",
	    timeStr(buf, sizeof(buf)), rtn, top, deltaT, bottom, deltaB,
	    updateEna, updShape.rowCount);
   }
  }
 }
 else
 {
  shape.top = top;
  shape.bottom = bottom;
  shape.height = (shape.bottom - shape.top) + 1;
  shape.topRow = (int) (TOP_SEG * shape.height);
  shape.botRow = (int) (BOTTOM_SEG * shape.height);
  rtn = true;
 }
 return(rtn);
}

bool updateColumns(int left, int right, int upd)
{
 bool rtn = false;
 if (upd)
 {
  int deltaL = left - shape.left;
  int deltaR = right - shape.right;
  if ((deltaL != 0) || (deltaR != 0))
  {
   if ((abs(deltaL) < 10) && (abs(deltaR) < 10))
   {
    if (updateEna)
    {
     printf("t %3d %3d b %3d %3d rowCount %d\n",
	    shape.left, updShape.lastL, shape.right, updShape.lastR,
	    updShape.colCount);

     if ((shape.left != updShape.lastL) || (shape.right != updShape.lastR))
     {
      updShape.lastL = shape.left;
      updShape.lastR = shape.right;
      updShape.colCount = UPD_COUNT;
     }
     else
     {
      if (updShape.colCount != 0)
      {
       updShape.colCount -= 1;
       if (updShape.colCount == 0)
       {
	shape.left = left;
	shape.right = right;
	shape.width = (shape.right - shape.left) + 1;
	rtn = true;
       }
      }
     }
    }

    if (1)
    {
     char buf[24];
     printf("%s updateCols %d l %3d d %3d r %3d d %3d u %d ctr %d\n",
	    timeStr(buf, sizeof(buf)), rtn, left, deltaL, right, deltaR,
	    updateEna, updShape.colCount);
    }
   }
  }
 }
 else
 {
  shape.left = left;
  shape.right = right;
  shape.width = (shape.right - shape.left) + 1;
  rtn = true;
 }
 return(rtn);
}

void setDigitCol(int strCol, int endCol, int index, int n)
{
// printf("strcol %3d endCol %3d\n", strCol, endCol);
 P_DIGIT_DATA data = &digitData[index];
 data->strCol[n] = strCol;
 data->endCol[n] = endCol;
 data->col[n] = (strCol + endCol) / 2;
 data->colRange[n] = (endCol - strCol) / 2;
}

void updateSegRows(P_DIGIT_DATA data);

void setSegRows(int *segRows, int n, int index)
{
//  printf("index %d segRows %3d %3d %3d\n",
//	index, segRows[0], segRows[1], segRows[2]);
 P_DIGIT_DATA data = &digitData[index];
 memcpy((void *) (data->segRows), (void *) segRows, 3 * sizeof(int));

 updateSegRows(data);
}

void updateSegRows(P_DIGIT_DATA data)
{
 int *segRows = data->segRows;

 data->topRow = (segRows[1] + segRows[2]) / 2;
 data->botRow = (segRows[3] + segRows[4]) / 2;
 data->rrT = data->topRow - data->segRows[0];
 data->rrC = segRows[3] - data->topRow;
 data->rrB = segRows[5] - data->botRow;
}

void setDirRows(int dirStart, int dirEnd, int index)
{
 P_DIGIT_DATA data = &digitData[index];
 data->dirStart = dirStart;
 data->dirEnd = dirEnd;
 if (dbg0)
  printf("setDirRows %d dirStart %2d dirEnd %2d\n",
	 index, dirStart, dirEnd);
}

void getDigitCol(int *rStrCol, int *rEndCol, int index, int n)
{
 P_DIGIT_DATA data = &digitData[index];
 *rStrCol = data->strCol[n];
 *rEndCol = data->endCol[n];
}

void getSegRows(int *rSegRows, int n, int index)
{
 P_DIGIT_DATA data = &digitData[index];
 for (int i = 0 ; i < SEG_ROWS; i++)
  rSegRows[i] = data->segRows[i];
}

void getDirRows(int *rDirStart, int *rDirEnd, int index)
{
 P_DIGIT_DATA data = &digitData[index];
 *rDirStart = data->dirStart;
 *rDirEnd = data->dirEnd;
}

void getSegData(int *start, int *offset, int index, int n)
{
 P_DIGIT_DATA data = &digitData[index];
 P_SEG_DATA p = &data->segments[n];
 *start = p->start;
 *offset = p->offset;
}

void printDigitData(P_DIGIT_DATA data)
{
 printf("st %3d %3d en %3d %3d seg %2d %2d %2d dir %2d %2d ",
	data->strCol[0], data->strCol[1],
	data->endCol[0], data->endCol[1],
	data->segRows[0], data->segRows[1], data->segRows[2],
	data->dirStart, data->dirEnd);
 fflush(stdout);
}

void prtDigDat(int index)
{
 printf("cm %d ", index);
 printDigitData(&digitData[index]);
}

void printDigitDataC(P_DIGIT_DATA data)
{
 printf("col %3d %3d cr %2d %2d tr %2d br %2d rr %2d %2d %2d dir %2d %2d\n",
	data->col[0], data->col[1],
	data->colRange[0], data->colRange[1],
	data->topRow, data->botRow, data->rrT, data->rrC, data->rrB,
	data->dirStart, data->dirEnd);
 fflush(stdout);
}

void prtDigDatC(int index)
{
 printDigitDataC(&digitData[index]);
}

void printData(void)
{
 for (int i = 0; i < MAX_DIGITS; i++)
 {
  prtDigDat(i);
  prtDigDatC(i);
 }
}

#if 0
int targetBounds(uint8_t *array, int n, int w, int upd)
{
 if (dbg0)
  printf("\ncMeter targetBounds w %3d\n", w);
 int lc = shape.left;
 int rc = shape.right;
 int rr = (int) (shape.height * TARGET_ROW_RANGE);
 int cr = (int) (shape.width * TARGET_COLUMN_RANGE);

 if (dbg0)
  printf("t %3d b %3d l %3d r %3d rr %3d cr %3d threshold %3d\n",
	 shape.top, shape.bottom, lc, rc, rr, cr, SUM_THRESHOLD);

 int rows[2] = {0, 0};
 int vBounds[2] = {shape.top, shape.bottom};
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
    rSum += array[k];

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
 }

 int cols[2] = {0, 0};
 int r0 = rows[0];
 int r1 = rows[1];
 int tRows = r1 - r0 + 1;
 int tCol[2] = {shape.left, shape.right};
 for (int i = 0; i < 2; i++)
 {
  int cs = tCol[i];
  bool findNeg = true;
  int lastSum = MAX_PIXEL;
  int c0 = 0;
  for (int col = cs - cr; col < cs + cr; col++)
  {
   int cSum = 0;

   for (int row = r0; row < r1; row++)
    cSum += array[row * w + col];

   cSum /= tRows;
   if (dbg0)
    printf("col %3d cSum %3d", col, cSum);
   if (findNeg)
   {
    if ((cSum <= SUM_THRESHOLD) && (lastSum >= SUM_THRESHOLD))
    {
     if (dbg0)
      printf(" c0 %3d", col);
     c0 = col;
     findNeg = false;
    }
   }
   else
   {
    if ((cSum >= SUM_THRESHOLD) && (lastSum <= SUM_THRESHOLD))
    {
     cols[i] = (col + c0) /  2;
     if (dbg0)
      printf(" c1 %3d cols[%d] %3d\n", col, i, cols[i]);
     break;
    }
   }
   if (dbg0)
    printf("\n");
   lastSum = cSum;
  }
  if (dbg0)
   printf("\n");
 }

 targetRows[0] = rows[0];
 targetRows[1] = rows[1];
 targetCols[0] = cols[0];
 targetCols[1] = cols[1];

 if (dbg0)
  printf("\nt %3d b %3d l %3d r %3d\n", rows[0], rows[1], cols[0], cols[1]);

 int rtn = updateRows(rows[0], rows[1], upd);
 rtn |= updateColumns(cols[0], cols[1], upd);

 if (dbg0)
  fflush(stdout);
 return(rtn);
}
#else

#define SUM_SIZE (4 * ROW_LEN)
#define DELTA_SIZE (4 * ROW_LEN)
#define ROW_SIZE (4 * ROW_LEN)

int tbData[SUM_SIZE + DELTA_SIZE + ROW_SIZE];
int tbIndex;

int *tbAlloc(int size)
{
 int *rtnVal = &tbData[tbIndex];
 tbIndex += size;
// printf("tbAlloc size %3d index %3d %llx\n",
//	size, tbIndex, (unsigned long long) rtnVal);
 return(rtnVal);
}

typedef struct
{
 int *sumArray;
 int *deltaArray;
 int *indexArray;
} T_TARGET_DATA, *P_TARGET_DATA;

T_TARGET_DATA targetData[4];

void dumpBuf(int *p, unsigned int len)
{
#define DUMP_COL 16
 char col = 0;
 for (unsigned int i = 0; i < len; i++)
 {
  if (col == 0)		/* if column 0 */
  {
   printf("%3d  ", i);
  }
  printf(" %4d", *p++);
  col += 1;			/* count a column */
  if (col == DUMP_COL)	/* if at end of line */
  {
   col = 0;			/* reset column counter */
   printf("\n");
  }
 }
 if (col != 0)
  printf("\n");
 fflush(stdout);
}

void getSumArray(int *sumArray, int n, int index)
{
 printf("getSumArray %d size %2d\n", index, n);
 P_TARGET_DATA data = &targetData[index];
 int *dst = sumArray;
 int *src = data->sumArray;
 for (int i = 0; i < n; i++)
  *dst++ = *src++;
 //dumpBuf(sumArray, n);
}

void getDeltaArray(int *deltaArray, int n, int index)
{
 printf("getDeltaArray %d size %2d\n", index, n);
 P_TARGET_DATA data = &targetData[index];
 int *dst = deltaArray;
 int *src = data->deltaArray;
 for (int i = 0; i < n; i++)
  *dst++ = *src++;
 //dumpBuf(deltaArray, n);
}

void getIndexArray(int *indexArray, int n, int index)
{
 printf("getIndexArray %d size %2d\n", index, n);
 P_TARGET_DATA data = &targetData[index];
 int *dst = indexArray;
 int *src = data->indexArray;
 for (int i = 0; i < n; i++)
  *dst++ = *src++;
 //dumpBuf(indexArray, n);
}

int targetBounds(uint8_t *array, int n, int w, int upd)
{
 if (dbg0)
  printf("\ncMeter targetBounds w %3d\n", w);
 int lc = shape.left;
 int rc = shape.right;
 int rr = (int) (shape.height * TARGET_ROW_RANGE);
 int cr = (int) (shape.width * TARGET_COLUMN_RANGE);
 memset((void *) tbData, 0, sizeof(tbData));
 P_TARGET_DATA targetPtr = targetData;
 tbIndex = 0;

 if (dbg0)
  printf("t %3d b %3d l %3d r %3d rr %3d cr %3d\n",
	 shape.top, shape.bottom, lc, rc, rr, cr);

 int rows[2] = {0, 0};
 int vBounds[2] = {shape.top, shape.bottom};
 bool top = true;
 int strVal = MAX_PIXEL;
 int endVal = -MAX_PIXEL;
 for (int i = 0; i < 2; i++)
 {
  int r = vBounds[i];
  int size = 2 * rr + DELTA_OFS;
  if (dbg0)
   printf("\ni %d r %3d min %3d max %3d size %2d\n",
	  i, r, r - rr - DELTA_OFS, r + rr, size);

  int *sumArray = (int *) tbAlloc(size);
  int *deltaArray = (int *) tbAlloc(size);
  int *indexArray = (int *) tbAlloc(size);
  int i = 0;
  for (int row = r - rr - DELTA_OFS; row < r + rr; row++)
  {
   int index = row * w;
   int rSum = 0;

   for (int k = index + lc - cr; k < index + rc + cr; k++)
    rSum += array[k];

   sumArray[i] = rSum / (rc - lc + 2 * cr);
   indexArray[i] = row;
   //printf("i %3d row %3d rSum %3d\n", i, row, sumArray[i]);
   i += 1;
  }
  //printf("i %3d\n", i);
  
  i = DELTA_OFS;
  for (int row = r - rr; row < r + rr; row++)
  {
   int delta = sumArray[i] - sumArray[i - DELTA_OFS];
   //printf("i %3d row %3d rSum %3d delta %4d\n", i, row, sumArray[i], delta);
   deltaArray[i] = delta;
   if (top)
   {
    if (delta < strVal)
    {
     strVal = delta;
     rows[0] = row;
     if (dbg0)
      printf("<%2d row %3d sum %3d delta %4d\n", i, row, sumArray[i], delta);
    }
   }
   else
   {     
    if (delta > endVal)
    {
     endVal = delta;
     rows[1] = row - DELTA_OFS;
     if (dbg0)
      printf(">%2d row %3d sum %3d delta %4d\n", i, row, sumArray[i], delta);
    }
   }
   i += 1;
  }
  top = false;

  //dumpBuf(sumArray, size);
  //dumpBuf(deltaArray, size);
  //dumpBuf(indexArray, size);

  targetPtr->sumArray = sumArray;
  targetPtr->deltaArray = deltaArray;
  targetPtr->indexArray = indexArray;
  targetPtr += 1;
 }

 int cols[2] = {0, 0};
 bool left = true;
 strVal = MAX_PIXEL;
 endVal = -MAX_PIXEL;

 int tCol[2] = {shape.left, shape.right};
 for (int i = 0; i < 2; i++)
 {
  int c = tCol[i];
  if (dbg0)
   printf("\ni %d c %3d\n", i, c);

  int size = 2 * cr + DELTA_OFS;
  //printf("size %d\n", size);
  int *sumArray = (int *) tbAlloc(size);
  int *deltaArray = (int *) tbAlloc(size);
  int *indexArray = (int *) tbAlloc(size);
  int i = 0;
  for (int col = c - cr - DELTA_OFS; col < c + cr; col++)
  {
   int cSum = 0;
   //printf("col %3d\n", col);
   for (int row = rows[0]; row < rows[1]; row++)
   {
    cSum += array[row * w + col];
    //printf("row %3d index %6d pixel %3d, cSum %6d\n",
    //       row, row * w + col, array[row * w + col], cSum);
   }
   sumArray[i] = cSum / (rows[1] - rows[0]);
   indexArray[i] = col;
   i += 1; 
  }

  i = DELTA_OFS;
  for (int col = c - cr; col < c + cr; col++)
  {
   int delta = sumArray[i] - sumArray[i - DELTA_OFS];
   //printf("%2d col %3d sum %3d delta %4d\n", i, c, sumArray[i], delta);
   deltaArray[i] = delta;
   if (left)
   {
    if (delta < strVal)
    {
     strVal = delta;
     cols[0] = col;
     if (dbg0)
      printf(">%2d col %3d sum %3d delta %4d\n", i, c, sumArray[i], delta);
    }
   }
   else
   {     
    if (delta > endVal)
    {
     endVal = delta;
     cols[1] = col - DELTA_OFS;
     if (dbg0)
      printf("<%2d col %3d sum %3d delta %4d\n", i, c, sumArray[i], delta);
    }
   }
   i += 1;
  }
  left = false;

  //dumpBuf(sumArray, size);
  //dumpBuf(deltaArray, size);
  //dumpBuf(indexArray, size);

  targetPtr->sumArray = sumArray;
  targetPtr->deltaArray = deltaArray;
  targetPtr->indexArray = indexArray;
  targetPtr += 1;
 }
 targetRows[0] = rows[0];
 targetRows[1] = rows[1];
 targetCols[0] = cols[0];
 targetCols[1] = cols[1];

 if (dbg0)
  printf("\nt %3d b %3d l %3d r %3d\n", rows[0], rows[1], cols[0], cols[1]);

 int rtn = updateRows(rows[0], rows[1], upd);
 rtn |= updateColumns(cols[0], cols[1], upd);

 if (dbg0)
  fflush(stdout);
 return(rtn);
} 

#endif

//void rowScan(uint8_t *array, int row, int *segColumn; int maxCol)
//{
//}

void setDigitData(P_DIGIT_DATA data, int st, int en, int n)
{
 data->strCol[n] = st;
 data->endCol[n] = en;
 data->col[n] = (st + en) / 2;
 data->colRange[n] = (en - st) /2;
}

T_DIGIT_DATA refDigitData[MAX_DIGITS];

#define AVG_RANGE 2
#define AVG_SIZE (2 * AVG_RANGE + 1)
#define SCAN_START 3

void findRefSegments(uint8_t *array, int n, int w)
{
 int x0 = shape.right;
 int y0 = shape.top;
 int t = shape.topRow + y0;
 int b = shape.botRow + y0;

 if (dbg0)
  printf("\nc findRefSegments w %3d x0 %3d y0 %3d\n", w, x0 , y0);

 int vBounds[2] = {t, b};
 for (int i = 0; i < 2; i++)
 {
  int rowNum = vBounds[i];
  int *segColumn = seg[i];
  memset((void *) segColumn, 0, MAX_COL * sizeof(int));
  int *p = segColumn;
  bool findNeg = true;
  int colCount = 0;
  int rowIndex = rowNum * w + x0;
  int *avgPixel = avgPixelData[i];
  // int lastPixel = array[rowIndex - 2];

  if (dbg0)
   printf("rowScan %d row %3d %3d\n", i, rowNum, x0);

  int *a = avgPixel;
  for (int k = 0; k < ROW_LEN; k++)
   *a++ = 0;

  for (int j = rowNum - AVG_RANGE; j <= (rowNum + AVG_RANGE); j++)
  {
   if (0)
    printf("row %3d\n", j);

   int rowIndex = j * w + x0;
   int *a0 = &avgPixel[x0];
   uint8_t *a1 = &array[rowIndex];
   for (int col = 0; col < shape.width; col++)
   {
    // avgPixel[x0 - col] += array[rowIndex - col];
    *a0 += *a1;
    a0 -= 1;
    a1 -= 1;
   }
  }

  a = avgPixel;
  for (int k = 0; k < ROW_LEN; k++)
   *a++ /=  AVG_SIZE;

  if (0)
  {
   dumpBuf(avgPixel, ROW_LEN);
   printf("\n");
  }

  // for (int col = 3; col < shape.width; col++)
  // {
  //  int pixel = array[rowIndex - col];
  //  if (0)
  //   printf("%3d %3d p %3d\n", col, x0-col, pixel);

  a = &avgPixel[x0 - SCAN_START];
  int lastPixel = *(a + 1);
  for (int col = SCAN_START; col < shape.width; col++)
  {
   int pixel = *a;
   a -= 1;

   if (0)
   {
    int tmp = array[rowIndex - col];
    printf("%3d index %3d avg %3d pixel %3d d %3d colCount %2d\n",
	   col, x0-col, pixel, tmp, pixel-tmp, colCount);
   }

   if (findNeg)
   {
    if (pixel <= DIGIT_THRESHOLD && lastPixel >= DIGIT_THRESHOLD)
    {
     *p++ = col;
     colCount += 1;
     findNeg = false;
    }
   }
   else
   {
    if (pixel >= DIGIT_THRESHOLD && lastPixel <= DIGIT_THRESHOLD)
    {
     *p++ = col;
     colCount += 1;
     findNeg = true;
    }
   }
   lastPixel = pixel;
   if (colCount >= MAX_COL)
    break;
  }

  int flag = INITIAL_COLUMN_INDEX;
  int dig = 0;
  int last = 0;
  int gap = 0;
  int w0 = 0;
  P_DIGIT_DATA data = refDigitData;
  for (int j = 0; j < colCount; j++)
  {
   int col = segColumn[j];
   int st;
   int en;
   if (flag == 0)
   {
    flag = DIGIT_COLUMNS;
    dig += 1;
    if (dig < MAX_DIGITS)
    {
     int c1 = segColumn[j+1];
     gap = (c1 - col) / 2;
     st = segColumn[j-3] - gap;
     en = (col + c1) / 2;
     w0 = en - st;
    }
    else
    {
     st = segColumn[j-3] - gap;
     en = st + w0;
    }
    setDigitData(data, st, en, i);
    data += 1;
   }
   else
    flag -= 1;

   if (dbg0)
   {
    printf("j %2d col %3d %3d width %3d f %d",
	   j, col, x0-col, col-last, flag);
    if (flag == DIGIT_COLUMNS)
     printf(" d %d st %3d en %3d w %2d g %2d",
	    dig, st, en, w0, gap);
    printf("\n");
    last = col;
   }
  }

  if (dbg0)
  {
   printf("\n");
   data = refDigitData;
   for (int j = 0; j < MAX_DIGITS; j++)
   {
    printf("%d st %3d en %3d\n", j, data->strCol[i], data->endCol[i]);
    data += 1;
   }
   printf("\n");
  }

  if (i == 0)
  {
   data = refDigitData;
   for (int j = 0; j < MAX_DIGITS; j++)
   {
    if (dbg0)
     printf("dig %d st %3d en %3d col %3d cr %2d segRow ",
	    j, data->strCol[i], data->endCol[i],
	    data->col[i], data->colRange[i]);
    int centerCol = x0 - data->col[i];
    int *segRows = data->segRows;
    lastPixel = MAX_PIXEL;
    bool skip = true;
    int segIndex = 0;
    bool change = false;
    for (int row = 0; row <= shape.height; row++)
    {
     int pixel = array[(row + y0) * w + centerCol];
     if (dbg0 && 0)
      printf("row %2d pixel %3d skip %d neg %d\n", row, pixel, skip, findNeg);
     if (skip)
     {
      if (pixel >= DIGIT_THRESHOLD && lastPixel <= DIGIT_THRESHOLD)
       skip = false;
     }
     else
     {
      if (findNeg)
      {
       if (pixel <= DIGIT_THRESHOLD && lastPixel >= DIGIT_THRESHOLD)
       {
	segRows[segIndex++] = row;
	change = true;
	findNeg = false;
       }
      }
      else
      {
       if (pixel >= DIGIT_THRESHOLD && lastPixel <= DIGIT_THRESHOLD)
       {
	segRows[segIndex++] = row;
	change = true;
	findNeg = true;
       }
       if (dbg0 && change)
       {
	printf("%2d ", row);
	change = false;
       }
       if (segIndex >= SEG_ROWS)
	break;
      }
     }
     lastPixel = pixel;
    }

    if (segIndex == SEG_ROWS)
    {
     updateSegRows(data);
     
     int dirEnd = shape.height - 1;
     int dirStart = segRows[SEG_ROWS-1];
     for (int row = dirStart; row <= dirEnd; row++)
     {
      int pixel = array[(row + y0) * w + centerCol];
      if (pixel > DIGIT_THRESHOLD)
      {
       dirStart = row;
       break;
      }
     }

#if 0     
     lastPixel = MAX_PIXEL;
     int end = dirEnd;
     for (int row = dirStart; row < end; row++)
     {
      int pixel = array[(row + y0) * w + centerCol];
      if (pixel <= DIGIT_THRESHOLD && lastPixel >= DIGIT_THRESHOLD)
      {
       dirEnd = row - 1;
      }
      lastPixel = pixel;
     }
#else
     lastPixel = 0;
     for (int row = dirEnd; row < dirStart; --row)
     {
      int pixel = array[(row + y0) * w + centerCol];
      if (pixel <= DIGIT_THRESHOLD && lastPixel >= DIGIT_THRESHOLD)
      {
       dirEnd = row;
       break;
      }
      lastPixel = pixel;
     }
#endif
     
     data->dirStart = dirStart;
     data->dirEnd = dirEnd;
     if (dbg0)
      printf("dirStr %2d dirEnd %2d\n", dirStart, dirEnd);
    }
    data += 1;
   }
   if (dbg0)
    printf("\n");
  }
 }
 
 if (updateEna)
 {
  P_DIGIT_DATA s = refDigitData;
  P_DIGIT_DATA d = digitData;
  for (int i = 0; i < MAX_DIGITS; i++)
  {
   if (dbg0)
   {
    printf("%d s ", i);
    printDigitDataC(s);
   }
   memcpy((void *) d, (void *) s, sizeof(T_DIGIT_DATA));
   if (dbg0)
   {
    printf("%d d ", i);
    printDigitDataC(d);
    printf("\n");
   }
   d += 1;
   s += 1;
  }
 }
 if (dbg0)
  fflush(stdout);
}

/*
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
*/

uint8_t segDecode[128];
#define SEG_INV 0xff

void decodeInit()
{
 memset((void *) segDecode, SEG_INV, sizeof(segDecode));
 segDecode[0x3f] = 0;		/* 0  0 1 1  1 1 1 1  0x3f */
 segDecode[0x06] = 1;		/* 1  0 0 0  0 1 1 0  0x06 */
 segDecode[0x5b] = 2;		/* 2  1 0 1  1 0 1 1  0x5b */
 segDecode[0x4f] = 3;		/* 3  1 0 0  1 1 1 1  0x4f */
 segDecode[0x66] = 4;		/* 4  1 1 0  0 1 1 0  0x66 */
 segDecode[0x6d] = 5;		/* 5  1 1 0  1 1 0 1  0x6d */
 segDecode[0x7d] = 6;		/* 6  1 1 1  1 1 0 1  0x7d */
 segDecode[0x07] = 7;		/* 7  0 0 0  0 1 1 1  0x07 */
 segDecode[0x7f] = 8;		/* 8  1 1 1  1 1 1 1  0x7f */
 segDecode[0x67] = 9;		/* 9  1 1 0  0 1 1 1  0x67 */
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

typedef struct
{
 uint8_t segVal;
 uint8_t dirVal;
} T_READ_RESULT;

//int readSegments(uint8_t *array, int n, int index)
T_READ_RESULT readSegments(uint8_t *array, int n, int index)
{
 P_DIGIT_DATA data = &digitData[index];

 P_SEG_DATA p = data->segments;
 for (int i = 0; i < SEGMENTS; i++)
 {
  p->start = 0;
  p->offset = 0;
  p += 1;
 }
 p = data->segments;
  
 int x0 = shape.right;
 int y0 = shape.top;
 int w = shape.tArrayW;
 // printf("x0 %3d y0 %3d w %3d ", x0, y0, w);

 int tr = (data->topRow + y0) * w;
 int br = (data->botRow + y0) * w;
 // printf("tr %2d %6d br %2d %6d ", data->topRow, tr, data->botRow, br);

 int result = 0;
 int colT = x0 - data->col[0];
 int crT = data->colRange[0];

 // printf("colT %3d crT %2d ", colT, crT);

 for (int i = 0; i < crT; i++)
 {
  if (array[tr + colT + i] < DIGIT_THRESHOLD)
  {
   if (p[1].start == 0)
   {
    p[1].start = tr + colT;
    p[1].offset = i;
   }
   result |= 0x02;
  }

  if (array[tr + colT - i] < DIGIT_THRESHOLD)
  {
   if (p[5].start == 0)
   {
    p[5].start = tr + colT;
    p[5].offset = -i;
   }
   result |= 0x20;
  }
 }

 int colB = x0 - data->col[1];
 int crB = data->colRange[1];
 // printf("colB %3d crB %2d ", colB, crB);
 for (int i = 0; i < crB; i++)
 {
  if (array[br + colB + i] < DIGIT_THRESHOLD)
  {
   if (p[2].start == 0)
   {
    p[2].start = br + colB;
    p[2].offset = i;
   }
   result |= 0x04;
  }

  if (array[br + colB - i] < DIGIT_THRESHOLD)
  {
   if (p[4].start == 0)
   {
    p[4].start = br + colB;
    p[4].offset = -i;
   }
   result |= 0x10;
  }
 }

 int trc = tr + colT;
 int brc = br + colB;
 int rr = data->rrT;
 // printf("trc %6d brc %6d rr %2d ", trc, brc, rr);
 for (int i = 0; i < rr; i++)
 {
  int r0 = i * w;

  if (array[trc - r0] < DIGIT_THRESHOLD)
  {
   if (p[0].start == 0)
   {
    p[0].start = trc;
    p[0].offset = -r0;
   }
   result |= 0x01;
  }
 }
  
 rr = data->rrC;
 for (int i = 0; i < rr; i++)
 {
  int r0 = i * w;

  if (array[trc + r0] < DIGIT_THRESHOLD)
  {
   if (p[6].start == 0)
   {
    p[6].start = trc;
    p[6].offset = r0;
   }
   result |= 0x40;
  }
 }
  
 rr = data->rrB;
 for (int i = 0; i < rr; i++)
 {
  int r0 = i * w;

  if (array[brc + r0] < DIGIT_THRESHOLD)
  {
   if (p[3].start == 0)
   {
    p[3].start = brc;
    p[3].offset = r0;
   }
   result |= 0x08;
  }
 }
 data->result = result;
 // printf("result %02x\n", result);
 
 T_READ_RESULT readResult;
 readResult.segVal = result;

 int startRow = data->dirStart + y0;
 int endRow = data->dirEnd + y0;
 bool skip = true;

 int lastPixel = 0;
 result = 0;
 int row;
 for (row = startRow; row < endRow; row++)
 {
  int pixel = array[row * w + colB];
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
 readResult.dirVal = result;
 return(readResult);
}

/*
int readDirection(uint8_t *array, int n, int index)
{
 P_DIGIT_DATA data = &digitData[index];
 int w = shape.tArrayW;
 int col = shape.right - data->col[0];
 int t = shape.top;
 int startRow = data->dirStart + t;
 int endRow = data->dirEnd + t;
 bool skip = true;
 int lastPixel = 0;
 int result = 0;
 int row;
 for (row = startRow; row < endRow; row++)
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
 //printf("%d col %3d row %2d result %d\n",
 //       index, -(col - shape.right), row - t, result);
 //fflush(stdout);
 return(result);
}
*/

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
   drawTargetErrFlag = (abs(delta) > 1);
   char buf[24];
   printf("%s %d v %6d m %6d d %2d n %5d r %5d f %5d\n",
	  timeStr(buf, sizeof(buf)), nxtCtr, val, meter, delta,
	  m.net, m.rev, m.fwd);
   if (abs(delta) <= 1)
   {
    m.ctr = nxtCtr;
    if (dbg2)
     drawTargetDbgFlag = 1;
    m.meterVal[nxtCtr] = val;
    if (delta != 0)
    {
     printf("%s delta %2d nxtCtr %d val %5d",
	    timeStr(buf, sizeof(buf)), delta, nxtCtr, val);
     switch (nxtCtr)
     {
     case 0:
      break;
     case 1:
      m.netTotal += m.net;
      printf(" rst net %3d t %5d", m.net, m.netTotal);
      m.net = 0;
      break;
     case 2:
      m.fwdTotal += m.fwd;
      printf(" rst fwd %3d t %5d", m.fwd, m.fwdTotal);
      m.fwd = 0;
      break;
     case 3:
      m.revTotal += m.rev;
      printf(" rst rev %3d t %5d", m.rev, m.revTotal);
      m.rev = 0;
      break;
     default:
      printf(" default");
      break;
     }
     printf("\n");
    }
   }
   else
    val = m.lastVal;
  }
  m.lastVal = val;
 }
}

int updateDirection(int dirIndex, int *dirError)
{
 if (dirIndex != m.lastDir)
 {
  if (dirIndex == DIR_INV)
  {
   dirIndex = m.lastDir;
   if (0)
   {    
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
   }
   printf("*+dirIndex %d\n", dirIndex);
   fflush(stdout);
   *dirError = 1;
   return dirIndex;
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

void getArray(uint8_t *cArray, int n)
{
 memcpy((void *) cArray, (void *) targetArray, n);
}
 
void readDisplay(uint8_t *array, int n, int *val,
		 int *dirIndex, int *dirVal)
{
 int meterVal = 0;
 int meterMult = 1;
 int dirV = 0;
 int dirM = 1;

 memcpy((void *) targetArray, (void *) array, n);

 for (int i = 0; i < 6; i++)
 {
#if 1
  T_READ_RESULT readResult = readSegments(array, n, i);
  // printf("segVal = %2x\n", readResult.segVal);
  int result = decode(readResult.segVal);
  meterVal += meterMult * result;
#else
  T_READ_RESULT readResult = readSegments(array, n, i);
  int result = segDecode[readResult.segVal];
  if (result != SEG_INV)
   meterVal += meterMult * result;
#endif
  meterMult *= 10;

  // result = readDirection(array, n, i);
  result = readResult.dirVal;
  if (result != 0)
   dirV |= dirM;
  dirM <<= 1;
 }
 *val = meterVal;
 *dirVal = dirV;
 *dirIndex = dirV <= 0x30 ? dirConv[dirV] : DIR_INV;
}

void loopInit(void)
{
 memset((void *) &m, 0, sizeof(m));
}

void loopSync(void)
{
 m.sync = false;
 m.lastVal = -1;
 m.lastTmp = -1;
}

int drawTargetUpd(void)
{
 return(targetUpdFlag);
}

int drawTargetErr(void)
{
 return(drawTargetErrFlag);
}

int drawTargetDbg(void)
{
 int tmp = drawTargetDbgFlag;
 drawTargetDbgFlag = 0;
 return(tmp);
}

int loopProcess(uint8_t *array, int n)
{
 int val;
 int dirIndex;
 int dirVal;
 int dirError = 0;
 
 readDisplay(array, n, &val, &dirIndex, &dirVal);
 shape.update = false;
 if (m.sync)
 {
  updateReading(val);
  dirIndex = updateDirection(dirIndex, &dirError);
  printf("%d %6d 0x%02x %d %2d n %3d f %3d r %3d\n",
	 m.ctr, val, dirVal, dirIndex, m.delta,
	 m.net, m.fwd, m.rev);
  m.delta = 0;
  if (shape.update)
  {
   targetUpdFlag = targetBounds(array, n, shape.rArrayW, true);
   if (targetUpdFlag)
    findRefSegments(array, n, shape.rArrayW);
   else
    shape.update = false;
  }
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

  int dirError = 0;
  updateDirection(dirIndex, &dirError);
 }
 fflush(stdout);
 return(dirError);
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
