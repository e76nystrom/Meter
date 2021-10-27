#include <stdint.h>
#include <stdbool.h>

/*

typedef struct lcdShape
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

#define SEG_ROWS 3

typedef struct digitData
{
 int strCol[2];
 int endCol[2];
 int col[2];
 int colRange[2];

 int segRows[SEG_ROWS];
 int maxRow;
 int topRow;
 int botRow;
 int rowRange;

 int dirStart;
 int dirEnd;
} T_DIGIT_DATA, *P_DIGIT_DATA;

T_DIGIT_DATA digitData[6];

*/

int dbg0 = false;
int dbg1 = false;
int updateEna = false;

double TARGET_COLUMN_RANGE = 0.05;
double TARGET_ROW_RANGE = 0.20;
int SUM_THRESHOLD = 90;

int DIGIT_THRESHOLD = 75;

void piInit(void);

//void dbg0Set(void);
//void dbg0Clr(void);
//void dbg1Set(void);
//void dbg1Clr(void);
//void dbg2Set(void);
//void dbg2Clr(void);

void setRef(uint8_t *array, int n, int w, int h);
void setTarget(uint8_t *array, int n, int w, int h);
void setSize(int width, int height);
void setRows(int top, int bottom);
void setColumns(int left, int right);

void getRows(int *tVal, int *bVal);
void getColumns(int *lVal, int *rVal);
void getSize(int *hVal, int *wVal, int *tRowVal, int *bRowVal);

void printShape(void);

void getSegColumn(int *segCol, int n, int index);

void setDigitCol(int strCol, int endCol, int index, int n);
void setSegRows(int *segRows, int n, int index);
void setDirRows(int dirStart, int dirEnd, int index);

void getDigitCol(int *rStrCol, int *rEndCol, int index, int n);
void getSegRows(int *segRows, int n, int index);
void getDirRows(int *rDirStart, int *rDirEnd, int index);

void prtDigDat(int index);
void prtDigDatC(int index);
void printData(void);

void targetUpdate(void);
int targetBounds(uint8_t *array, int n, int w, int upd);
void findRefSegments(uint8_t *array, int n, int w);

void decodeInit();
void readDisplay(uint8_t *array, int n, int *val, int *dirIndex, int *dirVal);

void loopInit(void);
void loopSync(void);
int loopProcess(uint8_t *array, int n);
int drawTarget(void);

double inplace(double *invec, int n);

int arrayTest(uint8_t *array, int n, int w, int row, int col);

void getSumArray(int *sumArray, int n, int index);
void getDeltaArray(int *deltaArray, int n, int index);
void getIndexArray(int *indexArray, int n, int index);
