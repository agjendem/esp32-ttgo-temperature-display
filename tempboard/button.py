from machine import Pin
import time


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
