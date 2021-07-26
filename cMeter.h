#include <stdint.h>
#include <stdbool.h>

int dbg0 = true;

void piInit(void);

//void dbg0Set(void);
//void dbg0Clr(void);
//void dbg1Set(void);
//void dbg1Clr(void);
//void dbg2Set(void);
//void dbg2Clr(void);

void setThresholds(int col, int digit);

void setTargetArray(uint8_t *array, int n, int w, int h);
void setSize(int width, int height);
void setRows(int top, int bottom);
void getRows(int *tVal, int *bVal);
void setColumns(int left, int right);
void getColumns(int *lVal, int *rVal);
void printShape(void);

void setDigit(int index);
void setDigitCol(int strCol, int endCol);
void setSegRows(int *segRows, int n);

void targetBounds(uint8_t *array, int n, int w, int h);

void loopInit(void);

void readDisplay(uint8_t *array, int n, int *val, int *dirIndex, int *dirVal);
int loopProcess(uint8_t *array, int n);

double inplace(double *invec, int n);

int arrayTest(uint8_t *array, int n, int w, int row, int col);
