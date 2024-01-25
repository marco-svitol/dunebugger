
from dunebuggerlogging import logger

class MockGPIO:

    def __init__(self):
        self.BCM = "MockBCM"
        self.OUT = "MockOUT"
        self.IN  = "MockIN"
        self.HIGH = 1
        self.LOW = 0
        self.PUD_DOWN = 0
        self.PUD_UP = 1
        self.RISING = "MockRISING"
        self.FALLING = "MockFalling"
        self.myPWM = PWM()

        # Dictionary to store GPIO states and associated callbacks
        self.gpio_states = {}
        self.events_detect = {}

    def show_gpio_status(self):
        logger.debug("Current GPIO Status:")
        for gpio, value in sorted(self.gpio_states.items()):
            logger.debug(f"Pin {gpio} label: {'HIGH' if value['state'] else 'LOW'}, Direction: {value['direction']}")



    def setmode(self, mode):
        logger.debug(f"MockGPIO.setmode mode={mode}")
        pass

    def setup(self, channels, direction, initial):
        for channel in channels:
            logger.debug(f"MockGPIO.setup channel={channel}, direction={direction}, initial={initial}")

            # Set the GPIO state based on the initial value
            self.set_gpio_state(channel, {'state': initial, 'direction': direction})

    def input(self, gpio):
        logger.debug(f"MockGPIO.input gpio={gpio}")
        return self.gpio_states.get(gpio)['state']

    def output(self, channel, value):
        logger.debug(f"MockGPIO.output channel={channel}, value={value}")
        pass

    def cleanup(self):
        logger.debug(f"MockGPIO.cleanup")
        pass

    def setwarnings(self, mode):
        logger.debug(f"MockGPIO.setwarnings mode={mode}")
        pass

    def PWM(self, channel, freq):
        logger.debug(f"MockGPIO.PWM channel={channel}, freq={freq}")
        return self.myPWM

    def remove_event_detect(self, gpio):
        logger.debug(f"MockGPIO.remove_event_detect gpio={gpio}")
        pass

    def add_event_detect(self, gpio, mode, callback, bouncetime):
        logger.debug(f"MockGPIO.add_event_detect gpio={gpio}, mode={mode}, callback={callback}, bouncetime={bouncetime}")
                # Associate the callback with the GPIO and mode
        self.events_detect[(gpio, mode)] = callback

    def set_gpio_state(self, gpio, value):
        if self.gpio_states.get(gpio) is None:
            self.gpio_states[gpio] = value
            return
        elif self.gpio_states.get(gpio)['state'] < value:
            mode = self.RISING
        elif self.gpio_states.get(gpio)['state'] > value:
            mode = self.FALLING
        else:
            return
        self.gpio_states[gpio]['state'] = value
        # Check if there is a callback associated with the GPIO and mode
        callback = self.events_detect.get((gpio, mode), None)

        if callback is not None:
            # If callback exists and value is True, invoke the callback
            callback(gpio)

    def get_gpio_state(self, gpio):
        return self.gpio_states.get(gpio)['state']

    def process_terminal_input(self, input_str):
        # Process commands received through the terminal
        tokens = input_str.lower().split()

    def process_terminal_input(self, input_str):
        # Process commands received through the terminal
        command_strs = input_str.lower().split(',')

        for command_str in command_strs:
            if command_str == "s":
                self.show_gpio_status()
            else:
                # Extract numeric part and direction from each command string
                tokens = command_str.strip().split('u' if 'u' in command_str else 'd')
                if len(tokens) == 2 and tokens[0].isdigit():
                    channel = int(tokens[0])
                    pull_up = 'u' in command_str

                    if pull_up:
                        self.set_gpio_state(channel, 1)
                    else:
                        self.set_gpio_state(channel, 0)

                    logger.debug(f"Simulated GPIO input: Pin {channel} {'UP' if pull_up else 'DOWN'}")


class PWM:
    def start(self, duty_cycle):
        logger.debug(f"MockGPIO.PWM.start duty_cycle={duty_cycle}")
        pass

    def ChangeDutyCycle(self, duty_cycle):
        logger.debug(f"MockGPIO.PWM.start ChangeDutyCycle={duty_cycle}")
        pass

GPIO = MockGPIO()