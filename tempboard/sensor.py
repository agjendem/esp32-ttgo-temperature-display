

class Sensor:
    # Setup data structure for local historical temperature measurements for the sensors:
    # TODO: Refactor readings..
    max_number_of_readings = 60

    def __init__(self, name, sensor, color):
        self.name = name
        self.sensor = sensor
        self.color = color
        self.measurements = list()

    def get_name(self):
        return self.name

    def get_color(self):
        return self.color

    def get_measurements(self):
        return self.measurements

    def add_measurement(self, value: float):
        if len(self.measurements) >= self.max_number_of_readings:
            self.measurements.pop(0)
        self.measurements.append(value)
        print("Sensor: {} Type: {} Value: {}".format(self.name, self.__class__, value))

    def get_current_value(self):
        return ""


class DS18B20Sensor(Sensor):
    def __init__(self, name, sensor, color):
        super().__init__(name, sensor, color)
        self.rom_code = sensor.rom_code()

    def get_current_value(self):
        current_value = self.sensor.convert_read()
        self.add_measurement(current_value)
        return "{:2.1f}".format(current_value)


# class DHT22Sensor(Sensor):
#     def __init__(self, name, sensor, color):
#         super().__init__(name, sensor, color)
#
#     def get_current_value(self):
#         current_value = # TODO
#         self.add_measurement(current_value)
#         return "{:2.1f}".format(current_value)
#
#
