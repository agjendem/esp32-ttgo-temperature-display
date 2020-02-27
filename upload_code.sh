#!/bin/bash
# Requires that you are in the dialup group (restart after adding, ensure "groups" lists it)

# Check if Ampy is already installed:
output="$(pip3 show ampy)"
if ! [[ $? -eq 0 ]] ; then
  pip3 install adafruit-ampy
fi

ampy --port /dev/ttyUSB0 put main.py
ampy --port /dev/ttyUSB0 mkdir tempboard
cd tempboard
ampy --port /dev/ttyUSB0 put __init__.py tempboard/__init__.py
ampy --port /dev/ttyUSB0 put button.py tempboard/button.py
ampy --port /dev/ttyUSB0 put sensor.py tempboard/sensor.py
cd -
ampy --port /dev/ttyUSB0 run main.py
