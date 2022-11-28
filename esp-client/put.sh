#!/bin/bash

FILES="./libs/*.py"
for f in $FILES
do
  echo uploading $f...
  ampy -b 115200 -p /dev/ttyUSB0 put $f
done

echo uploading boot.py...
ampy -b 115200 -p /dev/ttyUSB0 put boot.py

echo uploading main.py...
ampy -b 115200 -p /dev/ttyUSB0 put main.py

echo listing device
ampy -b 115200 -p /dev/ttyUSB0 ls