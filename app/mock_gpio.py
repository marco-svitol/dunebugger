
from dunebuggerlogging import logger

class MockGPIO:

    def __init__(self):
        self.BCM = "MockBCM"
        self.OUT = "MockOUT"
        self.IN  = "MockIN"
        self.HIGH = "MockHIGH"
        self.LOW = "MockLOW"
        self.PUD_DOWN = "MockPUD_DOWN"
        self.PUD_UP = "MockPUD_UP"
        self.myPWM = PWM()

    def setmode(self, mode):
        logger.debug(f"MockGPIO.setmode mode={mode}")
        pass

    def setup(self, channel, direction, initial):
        logger.debug(f"MockGPIO.setup channel={channel}, direction={direction}, initial={initial}")
        pass

    def input(self, channel):
        logger.debug(f"MockGPIO.input mode={channel}")
        return False

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


class PWM:
    def start(self, duty_cycle):
        logger.debug(f"MockGPIO.PWM.start duty_cycle={duty_cycle}")
        pass

GPIO = MockGPIO()