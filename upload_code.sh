# Requires that you are in the dialup group (restart after adding, ensure "groups" lists it)

# Check if Ampy is already installed:
output="$(pip3 show ampy)"
if ! [[ $? -eq 0 ]] ; then
  pip3 install adafruit-ampy
fi

ampy --port /dev/ttyUSB0 put main.py
