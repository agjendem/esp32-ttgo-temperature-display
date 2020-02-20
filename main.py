# Uses loboris micropython (esp32_psram_all_bt)
# https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/tree/master/MicroPython_BUILD/firmware
import display
import machine
import math

DS18B20 = "DS18B20"
DHT22 = "DHT22"

# Setup data structure for local historical temperature measurements for the sensors:
max_number_of_readings = 60

# Initialize the display
tft = display.TFT()
tft.init(tft.ST7789, rst_pin=23, backl_pin=4, miso=0, mosi=19, clk=18, cs=5, dc=16, width=235, height=340, backl_on=1)

# Invert colors
tft.tft_writecmd(0x21)

# Set orientation (optional)
tft.orient(tft.LANDSCAPE)

# Set window size - library is buggy with the display, have to move the view slightly
tft.setwin(40, 52, 278, 186)


class Sensor:
    def __init__(self, name, model, sensor, color):
        self.name = name
        self.model = model
        self.sensor = sensor
        self.color = color
        self.measurements = list()

    def get_name(self):
        return self.name

    def get_color(self):
        return self.color

    def get_measurements(self):
        return self.measurements

    def get_model(self):
        return self.model

    def add_measurement(self, value: float):
        if len(self.measurements) >= max_number_of_readings:
            self.measurements.pop(0)
        self.measurements.append(value)
        print("Sensor: {} Type: {} Value: {}".format(self.name, self.model, value))

    def get_current_value(self):
        return ""


class DS18B20Sensor(Sensor):
    def __init__(self, name, sensor, color):
        super().__init__(name, DS18B20, sensor, color)
        self.rom_code = sensor.rom_code()

    def get_current_value(self):
        current_value = self.sensor.convert_read()
        self.add_measurement(current_value)
        return "{:2.1f}".format(current_value)


# dht = machine.DHT(machine.Pin(25), machine.DHT.DHT2X)
ow = machine.Onewire(33)

sensors = [
    DS18B20Sensor("Luft", machine.Onewire.ds18x20(ow, 0), tft.RED),
    DS18B20Sensor("Bakke", machine.Onewire.ds18x20(ow, 1), tft.GREEN),
    DS18B20Sensor("Inne", machine.Onewire.ds18x20(ow, 2), tft.BLUE)
]


def temp_to_pixel(temp, min_temp, max_temp, height):
    temp_range = abs(min_temp - max_temp)
    pixels_per_degree = height / temp_range
    result = height - int(pixels_per_degree * temp)
    return result


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
    # Draw current temperatures on upper row for all sensors, in their colours:
    # .. but first draw empty string to initialize/reset LASTX to zero position
    tft.text(1, 0, "")
    for sensor in sensors:
        tft.text(tft.LASTX, 0, '{}: {} '.format(sensor.get_name(), sensor.get_current_value()), sensor.get_color())

    # Switch coordinates to the graph box
    tft.setwin(40 + temp_graph_area[0], 52 + temp_graph_area[1], 40 + temp_graph_area[2], 52 + temp_graph_area[3])

    # .. redraw graphs for all sensors:
    tft.clearwin(tft.BLACK)
    for sensor in sensors:
        current_position = 1
        # Depending on window size, the graph may not fill the entire screen due to rounding,
        # depending on the size and number of readings:
        step_size = math.floor((tft.winsize()[0]-2) / max_number_of_readings)

        for measurement in sensor.get_measurements():
            if sensor.get_model() is DS18B20:
                tp = temp_to_pixel(temp=measurement, min_temp=-20, max_temp=30, height=temp_graph_area[4]-20) # TODO: Why -20 here?
                # TODO: Why -20 here?
                tft.line(current_position, tp - 20, current_position + step_size, tp - 20, sensor.get_color())
                current_position += step_size
            else:
                # Not implemented yet:
                pass

    # Reset window to what we had initially:
    tft.setwin(40, 52, 278, 186)
