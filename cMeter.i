%module cMeter

%{
      #define SWIG_FILE_WITH_INIT
      #include "cMeter.h"
  %}

%include "typemaps.i"
%include "numpy.i"
%include <carrays.i>

%init %{
  import_array();
  %}

%apply (double* IN_ARRAY1, int DIM1) {(double* invec, int n)};
%apply (uint8_t* IN_ARRAY1, int DIM1) {(uint8_t* array, int n)};
%apply (int* IN_ARRAY1, int DIM1) {(int* segRows, int n)};
%apply (int* INPLACE_ARRAY1, int DIM1) {(int* rSegRows, int n)};
%apply (int* INPLACE_ARRAY1, int DIM1) {(int* segCol, int n)};

%apply int *OUTPUT {int *val};
%apply int *OUTPUT {int *dirVal};
%apply int *OUTPUT {int *dirIndex};
%apply int *OUTPUT {int *tVal};
%apply int *OUTPUT {int *bVal};
%apply int *OUTPUT {int *rVal};
%apply int *OUTPUT {int *lVal};

%apply int *OUTPUT {int *rStrCol};
%apply int *OUTPUT {int *rEndCol};
%apply int *OUTPUT {int *rDirStart};
%apply int *OUTPUT {int *rDirEnd};

//%array_class(struct digitData, digitArray);

%include "cMeter.h"
