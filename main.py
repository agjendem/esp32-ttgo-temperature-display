# Uses loboris micropython (esp32_psram_all_bt)
# https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/tree/master/MicroPython_BUILD/firmware
import display
import machine
import math

# Initialize the display
tft = display.TFT()
tft.init(tft.ST7789, rst_pin=23, backl_pin=4, miso=0, mosi=19, clk=18, cs=5, dc=16, width=235, height=340, backl_on=1)

# Invert colors
tft.tft_writecmd(0x21)

# Set orientation (optional)
tft.orient(tft.LANDSCAPE)

# Set window size - library is buggy with the display, have to move the view slightly
tft.setwin(40, 52, 278, 186)

#dht = machine.DHT(machine.Pin(25), machine.DHT.DHT2X)
ow = machine.Onewire(33)
# TODO: Iterate on ow.num-devs discovered?
temp0 = machine.Onewire.ds18x20(ow, 0)
temp1 = machine.Onewire.ds18x20(ow, 1)
temp2 = machine.Onewire.ds18x20(ow, 2)

# Setup data structure for local historical temperature measurements for the sensors:
max_number_of_readings = 60
temp0_code = temp0.rom_code()
temp1_code = temp1.rom_code()
temp2_code = temp2.rom_code()

measurements = dict()
measurements[temp0_code] = list()
measurements[temp1_code] = list()
measurements[temp2_code] = list()

colors = dict()
colors[temp0_code] = tft.RED
colors[temp1_code] = tft.GREEN
colors[temp2_code] = tft.BLUE

alias = dict()
alias[temp0_code] = "Luft"
alias[temp1_code] = "Bakke"
alias[temp2_code] = "Inne"


# def read_dht22():
#   result, temperature, humidity = dht.read()
#   if result:
#     tft.text(10, 25, 't={} C'.format(temperature), tft.WHITE)
#     tft.text(100, 25, 'h={} % RH'.format(int(humidity)), tft.WHITE)


def read_ds18b20():
    temperature = temp0.convert_read()
    if temperature:
        tft.text(10, 25, 't={} C'.format(temperature), tft.WHITE)


def temp_to_pixel(temp, min_temp, max_temp, height):
    temp_range = abs(min_temp - max_temp)
    pixels_per_degree = height / temp_range
    result = height - int(pixels_per_degree * temp)
    return result


def add_measurement(sensor_id, current_value: float):
    readings = measurements[sensor_id]
    if len(readings) >= max_number_of_readings:
        readings.pop(0)
    readings.append(current_value)
    print("Sensor id: {} Temperature: {}".format(sensor_id, current_value))


def draw_temp_graph():
    # Width of broadest legend text
    x_legend_width = tft.textWidth("+30") + 1

    # Available space to draw a graph on
    x0 = x_legend_width
    y0 = 20
    x1 = tft.winsize()[0] - x_legend_width
    y1 = tft.winsize()[1] - 20
    tft.rect(x0, y0, x1, y1, tft.WHITE)

    # Draw legend X indicators
    for i in range(-20, 35, 5):
        tp = temp_to_pixel(temp=i, min_temp=-20, max_temp=30, height=(tft.winsize()[1]-2)-(y0+1))
        # TODO: Hvorfor -20 på tpene?? hvorfor tegnes ikke alle strekene/brukes hele rangen?
        tft.line(x0-4, tp - 20, x0, tp - 20, tft.WHITE)

        # Drawing X legend (temp in degrees C)
        if i % 10 is 0:
            if i < 0:
                color = tft.BLUE
            elif i == 0:
                color = tft.WHITE
            else:
                color = tft.RED
            tft.text(0, tp - 20 - int(tft.fontSize()[1]/2), "{}".format(i), color)

    # Return area to draw on inside the graph frame + convenience height / width:
    return x0+1,\
           y0+1,\
           tft.winsize()[0]-2,\
           tft.winsize()[1]-2,\
           (tft.winsize()[1]-2)-(y0+1),\
           (tft.winsize()[0]-2)-(x0+1)


temp_graph_area = draw_temp_graph()


while True:
    # Draw current temperatures on upper row for all sensors, in different colours:
    current_temp0 = temp0.convert_read()
    tft.text(1, 0, '{}: {:2.1f}'.format(alias[temp0_code], current_temp0), colors[temp0_code])
    add_measurement(temp0_code, current_temp0)

    current_temp1 = temp1.convert_read()
    tft.text(tft.LASTX + 5, 0, '{}: {:2.1f}'.format(alias[temp1_code], current_temp1), colors[temp1_code])
    add_measurement(temp1_code, current_temp1)

    current_temp2 = temp2.convert_read()
    tft.text(tft.LASTX + 5, 0, '{}: {:2.1f}'.format(alias[temp2_code], current_temp2), colors[temp2_code])
    add_measurement(temp2_code, current_temp2)

    # Switch coordinates to the graph box
    tft.setwin(40 + temp_graph_area[0], 52 + temp_graph_area[1], 40 + temp_graph_area[2], 52 + temp_graph_area[3])

    # .. redraw graphs for all sensors:
    tft.clearwin(tft.BLACK)
    for sensor in measurements:
        current_position = 1
        # Depending on window size, the graph may not fill the entire screen due to rounding,
        # depending on the size and number of readings:
        step_size = math.floor((tft.winsize()[0]-2) / max_number_of_readings)

        for reading in measurements[sensor]:
            tp = temp_to_pixel(temp=reading, min_temp=-20, max_temp=30, height=temp_graph_area[4]-20) # TODO: Hvorfor -20 her?
            # TODO: Se todo over om -20
            tft.line(current_position, tp - 20, current_position + step_size, tp - 20, colors[sensor])
            current_position += step_size

    # Reset window to what we had initially:
    tft.setwin(40, 52, 278, 186)
