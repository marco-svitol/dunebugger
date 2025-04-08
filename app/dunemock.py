from dunebugger_logging import logger, COLORS
import json

class MockGPIO:

    def __init__(self):
        self.BCM = "BCM"
        self.OUT = "OUTPUT"
        self.IN = "INPUT"
        self.HIGH = 1
        self.LOW = 0
        self.PUD_DOWN = 0
        self.PUD_UP = 1
        self.RISING = "RISING"
        self.FALLING = "FALLING"

        # Dictionary to store GPIO states and associated callbacks
        self.gpio_states = {}
        self.events_detect = {}

    def setmode(self, mode):
        logger.debug(f"MockGPIO.setmode mode={mode}")
        pass

    def setup(self, channels, mode, initial):
        for channel in channels:
            logger.debug(f"MockGPIO.setup channel={channel}, mode={mode}, initial={initial}")

            # Set the GPIO state based on the initial value
            self.set_gpio_state(channel, {"state": initial, "mode": mode})

    def input(self, gpio):
        return self.gpio_states.get(gpio)["state"]

    def output(self, gpio, value):
        self.set_gpio_state(gpio, value)
        pass

    def cleanup(self):
        logger.debug("MockGPIO.cleanup")
        pass

    def setwarnings(self, mode):
        logger.debug(f"MockGPIO.setwarnings mode={mode}")
        pass

    class PWM:
        def __init__(self, gpio, freq):
            self.parentGPIO = GPIO
            self.gpio = gpio
            self.freq = freq
            self.dutycycle = 0

        def start(self, dutycycle):
            self.parentGPIO.output(self.gpio, GPIO.HIGH)
            self.dutycycle = dutycycle
            logger.debug(f"MockGPIO.PWM.start duty_cycle={dutycycle}")
            pass

        def ChangeDutyCycle(self, dutycycle):
            logger.debug(f"MockGPIO.PWM.start ChangeDutyCycle={dutycycle}")
            self.dutycycle = dutycycle
            pass

    def remove_event_detect(self, gpio):
        logger.debug(f"MockGPIO.remove_event_detect gpio={gpio}")
        pass

    def add_event_detect(self, gpio, mode, callback, bouncetime=0):
        logger.debug(f"MockGPIO.add_event_detect gpio={gpio}, mode={mode}, callback={callback}, bouncetime={bouncetime}")
        # Associate the callback with the GPIO and mode
        self.events_detect[(gpio, mode)] = callback

    def set_gpio_state(self, gpio, value):
        if self.gpio_states.get(gpio) is None:
            self.gpio_states[gpio] = value
            return
        elif self.gpio_states.get(gpio)["mode"] == self.OUT:
            self.gpio_states[gpio]["state"] = value
            return
        else:
            if self.gpio_states.get(gpio)["state"] < value:
                mode = self.RISING
            elif self.gpio_states.get(gpio)["state"] > value:
                mode = self.FALLING
            else:
                return
            self.gpio_states[gpio]["state"] = value
            # Check if there is a callback associated with the GPIO and mode
            callback = self.events_detect.get((gpio, mode), None)

            if callback is not None:
                # If callback exists and value is True, invoke the callback
                callback(gpio)

    def gpio_function(self, gpio):
        return self.gpio_states[gpio]["mode"]

    def get_gpio_state(self, gpio):
        return self.gpio_states.get(gpio)["state"]

GPIO = MockGPIO()
