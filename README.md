# Hardware involved:
ESP32 with TTGO display (flashed with Micropython from Loboris):
* Board: https://www.banggood.com/LILYGO-TTGO-T-Display-ESP32-CP2104-WiFi-bluetooth-Module-1_14-Inch-LCD-Development-Board-p-1522925.html
* Temperature sensor: https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf

Board layout:
![alt text](https://user-images.githubusercontent.com/20520240/69371506-03c1d200-0cb1-11ea-91ba-818778235c49.jpeg "Board layout")

# Software:
* http://micropython.org/

## Uses Loboris MicroPython (esp32_psram_all_bt)
* https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo
* https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/tree/master/MicroPython_BUILD/firmware

DS18B20 api documentation:
* https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/wiki/onewire

TTGO api documentation:
* https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/wiki/display
