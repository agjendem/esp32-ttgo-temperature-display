# Uses loboris micropython (esp32_psram_all_bt)
# https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/tree/master/MicroPython_BUILD/firmware
from display import TFT
from machine import Pin, Onewire, DHT
import math
import time

DS18B20 = "DS18B20"
DHT22 = "DHT22"

# Setup data structure for local historical temperature measurements for the sensors:
max_number_of_readings = 60


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


class Button:
    # Based on code from https://people.eecs.berkeley.edu/~boser/courses/49_sp_2019/N_gpio.html
    # as a result of issues with built-in debounce-code in Loboris:
    #   https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/issues/212

    def __init__(self, pin, callback=None, falling=True, debounce_ms=50):
        """ Button with debouncing. Arguments:
        pin: pin number
        callback: handler, called when button press detected
        falling: detect raising or falling edges
        """
        self.last_time_ms = 0
        self.detected = False  # a button press was detected
        self.debounce_ms = debounce_ms
        self.cb = callback
        Pin(pin,
            mode=Pin.IN,
            pull=Pin.PULL_UP,
            handler=self._irq_callback,
            trigger=Pin.IRQ_FALLING if falling else Pin.IRQ_RISING)

    def pressed(self):
        """Return True if button pressed since last call"""
        p = self.detected
        self.detected = False
        return p

    def _irq_callback(self, pin):
        # Limitations / rules: https://docs.micropython.org/en/latest/reference/isr_rules.html
        # TODO: On other boards than ESP32 most of this should be done via micropython.schedule()
        # (It seems that on ESP32, all interrupt handlers are by default scheduled by the interpreter)
        t = time.ticks_ms()
        diff = t - self.last_time_ms

        if abs(diff) < self.debounce_ms:
            return

        self.last_time_ms = t
        self.detected = True

        if self.cb:
            self.cb(pin)


class Visualization:

    def __init__(self, min_temp, max_temp, sensors):
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.sensors = sensors
        self.RENDER_MODES = ["all"]
        for sensor in sensors:
            self.RENDER_MODES.append(sensor)
        self.render_mode = 0
        self.tft = self._init_display()

        self._switch_window_to_whole_screen()
        self.graph_x0, \
            self.graph_y0, \
            self.graph_width, \
            self.graph_height = self._render_graph_area_with_legend(self.min_temp, self.max_temp)

    @staticmethod
    def _init_display():
        # Initialize the display
        # https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/wiki/display
        # https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/issues/310
        tft = TFT()
        tft.init(tft.ST7789,
                 rst_pin=23,
                 backl_pin=4,
                 miso=0,
                 mosi=19,
                 clk=18,
                 cs=5,
                 dc=16,
                 width=235,
                 height=340,
                 backl_on=1)

        # Invert colors
        tft.tft_writecmd(0x21)

        # Set orientation (optional)
        tft.orient(tft.LANDSCAPE)

        return tft

    def _render_graph_area_with_legend(self, min_temp, max_temp):
        # Width of broadest legend text expected
        x_legend_width = self.tft.textWidth("+30") + 1
        y_top_bar_height = 20
        temp_step_size = 5

        # Available space to draw a graph on
        x0 = x_legend_width
        y0 = y_top_bar_height
        width = self.tft.winsize()[0] - x_legend_width
        height = self.tft.winsize()[1] - y_top_bar_height
        internal_graph_height = height - 2  # _inside_ the box

        # Draw a frame around the graph area
        self.tft.rect(x0, y0, width, height, self.tft.WHITE)
    
        # Draw legend X indicators
        for i in range(min_temp, max_temp + 1, temp_step_size):
            tp = self._temp_to_pixel_height(i, internal_graph_height)
            self.tft.line(x0 - 4,
                          y0 + 1 + tp,
                          x0,
                          y0 + 1 + tp,
                          self.tft.WHITE)
    
            # Drawing X legend (temp in degrees C)
            if i % 10 is 0:
                if i < 0:
                    color = self.tft.BLUE
                elif i == 0:
                    color = self.tft.WHITE
                else:
                    color = self.tft.RED
                self.tft.text(0,
                              y0 + 1 + tp - int(self.tft.fontSize()[1]/2),  # Centered vertically
                              "{}".format(i),
                              color)
    
        # Return area to draw on _inside_ the graph frame:
        return \
            x0 + 1, \
            y0 + 1, \
            width - 2, \
            height - 2

    def _switch_window_to_whole_screen(self):
        # Set window size - library is buggy with the display, have to move the view slightly
        self.tft.setwin(40, 52, 278, 186)

    def _switch_window_to_graph(self):
        self.tft.setwin(40 + self.graph_x0,
                        52 + self.graph_y0,
                        40 + self.graph_width + self.graph_x0 - 1,
                        52 + self.graph_height + self.graph_y0 - 1)

    def _clear_current_window(self):
        self.tft.clearwin(self.tft.BLACK)

    def _temp_to_pixel_height(self, temp, height):
        temp_range = abs(self.min_temp - self.max_temp)
        pixels_per_degree = height / temp_range
        result = height - int(pixels_per_degree * (temp + abs(self.min_temp)))
        return result

    def _temp_to_pixel(self, temp):
        return self._temp_to_pixel_height(temp, self.graph_height)

    def next_render_mode(self):
        if self.render_mode + 1 < len(self.RENDER_MODES):
            self.render_mode += 1
        else:
            self.render_mode = 0
        print(self.render_mode)

    def render(self):
        #
        # Draw current temperatures on upper row for all sensors, in their colours:
        #
        # .. but first draw empty string to initialize/reset LASTX to zero position
        self._switch_window_to_whole_screen()
        self.tft.text(1, 0, "")
        for sensor in sensors:
            self.tft.text(self.tft.LASTX,
                         0,
                         '{}: {} '.format(sensor.get_name(), sensor.get_current_value()),
                         sensor.get_color())

        #
        # .. redraw graphs for all/selected sensor(s):
        #
        self._switch_window_to_graph()
        self._clear_current_window()

        for sensor in sensors:
            if self.render_mode is 0 \
                    or self.RENDER_MODES[self.render_mode] is sensor:
                self._render_sensor_graph(sensor)

    def _render_sensor_graph(self, sensor):
        # Depending on window size, the graph may not fill the entire screen due to rounding,
        # depending on the size and number of readings:
        step_size = math.floor(self.graph_width / max_number_of_readings)

        current_position = 1
        for measurement in sensor.get_measurements():
            if sensor.get_model() is DS18B20:
                tp = self._temp_to_pixel(measurement)
                self.tft.line(current_position, tp, current_position + step_size, tp, sensor.get_color())
                current_position += step_size
            else:
                # Not implemented yet:
                pass


# dht = DHT(Pin(25), DHT.DHT2X)
ow = Onewire(33)

sensors = [
    DS18B20Sensor(name="Luft", sensor=Onewire.ds18x20(ow, 0), color=TFT.RED),
    DS18B20Sensor(name="Bakke", sensor=Onewire.ds18x20(ow, 1), color=TFT.GREEN),
    DS18B20Sensor(name="Inne", sensor=Onewire.ds18x20(ow, 2), color=TFT.BLUE)
]

vis = Visualization(min_temp=-20, max_temp=40, sensors=sensors)


def cb(pin):
    vis.next_render_mode()
    print("Changing rendering mode to: {}".format(vis.render_mode), pin)


toggle_sensors_button = Button(0, callback=cb)
while True:
    vis.render()
