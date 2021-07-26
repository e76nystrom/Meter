#!/bin/bash

rm -rf __pycache__
rm -rf build
python3 setup.py -v build
cp build/lib.linux-x86_64-3.8/_cMeter.cpython-38-x86_64-linux-gnu.so ~/.local/lib/python3.8/site-packages/ 
