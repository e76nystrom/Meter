%module cMeter

%{
      #define SWIG_FILE_WITH_INIT
      #include "cMeter.h"
  %}
%include "typemaps.i"
%include "numpy.i"


%init %{
  import_array();
  %}

%apply (double* IN_ARRAY1, int DIM1) {(double* invec, int n)};
%apply (uint8_t* IN_ARRAY1, int DIM1) {(uint8_t* array, int n)};
%apply (int* IN_ARRAY1, int DIM1) {(int* segRows, int n)};
%apply int *OUTPUT {int *val};
%apply int *OUTPUT {int *dirVal};
%apply int *OUTPUT {int *dirIndex};
%apply int *OUTPUT {int *tVal};
%apply int *OUTPUT {int *bVal};
%apply int *OUTPUT {int *lVal};
%apply int *OUTPUT {int *rVal};

%include "cMeter.h"
