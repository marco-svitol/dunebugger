from dunebuggerlogging import logger
import configparser
from ast import literal_eval
from dunebugger_settings import settings
from os import path
import re

if settings.ON_RASPBERRY_PI:
    import RPi.GPIO as GPIO
#PWM 13,19,12,18 # free : 19
# 2,3 were used for Arduino serial (no rele). Two GPIOs were reserved for Arduino reset (14) relè and Dimmer board reset (15) relè

#     # Dimmer1 I2C - Light dimmering : 0 Fully open - 100 Fully closed
#     Dimmer1Add = '0x27'
#     Dimmer1Ch1 = '0x80'
#     Dimmer1Ch2 = '0x81'
#     Dimmer1Ch3 = '0x82'
#     Dimmer1Ch4 = '0x83'

#     # Dimmer2 Serial - Protocol commands
#     Ch1Rst = "900\n"
#     Ch1FIn = "i\n"
#     Ch1FOu = "o\n"

class GPIOHandler:
    def __init__(self):
        # Load GPIO configuration from gpio_config.conf
        self.GPIOMap = {}
        
        self.load_gpio_configuration()
        if settings.ON_RASPBERRY_PI:
            # Initialize GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.chan_releA, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.setup(self.chan_releB, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.setup(self.chan_contr, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.chan_motor_1, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.chan_limitswitch_motor1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.chan_motor_2, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.chan_limitswitch_motor2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.GPIO = GPIO
        
    def load_gpio_configuration(self):
        config = configparser.ConfigParser()
        # Set optionxform to lambda x: x to preserve case
        config.optionxform = lambda x: x
        channels = {}
        logicalChannels = {}

        try:
            gpioConfig = path.join(path.dirname(path.abspath(__file__)), 'config/gpio.conf')
            config.read(gpioConfig)

            # Load Channels
            try:
                for physicalChannel, values in config.items('Channels'):
                    # Convert the values to tuple if there is more than one element
                    channel_values = literal_eval(values)
                    if isinstance(channel_values, tuple):
                        channels[physicalChannel] = channel_values
                    else:
                        channels[physicalChannel] = (channel_values,)
            except (configparser.Error, ValueError) as e:
                logger.error("Error reading channel configuration: "+ {e})
                # Handle the error as needed

            # Load GPIOMapPhysical
            try:
                for logicalChannel, values in config.items('LogicalChannels'):
                    channel, index = self.__extract_variable_info(values)
                    logicalChannels[logicalChannel] = channels[channel][index]
            except (configparser.Error, ValueError) as e:
                logger.error("Error reading LogicalChannels configuration: "+ {e})
                # Handle the error as needed
        
            # Load GPIOMap
            try:
                for GPIOMap, values in config.items('GPIOMaps'):
                    logicalChannel, index = self.__extract_variable_info(values)
                    self.GPIOMap[GPIOMap] = logicalChannels[index]
            except (configparser.Error, ValueError) as e:
                logger.error("Error reading LogicalChannels configuration: "+ {e})
                # Handle the error as needed

            # Check if "I_StartButton" entry exists in GPIOMap
            if 'I_StartButton' not in self.GPIOMap:
                raise ValueError('GPIOMap must have an entry for "I_StartButton"')

        except (configparser.Error, ValueError) as e:
            print(f"Error reading GPIO configuration: {e}")
            # You might want to handle the error in an appropriate way, e.g., logging or quitting the program


    def cleanup(self):
        GPIO.cleanup()

    def getGPIOLabel(self,GPIONum):
        for key, value in self.GPIOMap.items():
            if value == GPIONum:
                return key
            # Return None if the value is not found
        return "_not_found_"

    def __extract_variable_info(solf, expression):
        """
        Extract variable name and index from an expression of the form 'variable[index]'.
        
        Parameters:
        - expression (str): The input expression.

        Returns:
        - Tuple[str, int]: A tuple containing the variable name and index.
        If the expression is not in the correct format, returns (None, None).
        """
        match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\[(.+)\]', expression)
        
        if match:
            variable_name = match.group(1)
            index = match.group(2)
            try:
                index = int(index)
            except ValueError:
                pass
            return variable_name, index
        else:
            return None, None


def RPiwrite(gpio,bit):
    logger.debug("RPi "+gpio+" write "+str(bit))
    bit = not bit
    GPIO.output(mygpio_handler.GPIOMap[gpio],bit)

def RPiToggle(gpio):
    GPIO.output(mygpio_handler.GPIOMap[gpio], not GPIO.input(mygpio_handler.GPIOMap[gpio]))
    #logger.verbose("Toggled RPi "+gpio+" to "+str(GPIO.input(mygpio_handler.GPIOMap[gpio])))

if not settings.ON_RASPBERRY_PI:
    # Mock GPIO class for non-Raspberry Pi platforms
    class MockGPIO:
        BCM = "MockBCM"
        OUT = "MockOUT"
        HIGH = "MockHIGH"
        LOW = "MockLOW"
        PUD_DOWN = "MockPUD_DOWN"

        def setmode(self, mode):
            pass

        def setup(self, channel, direction, initial):
            pass

        def input(self, channel):
            return False

        def output(self, channel, value):
            pass

        def cleanup(self):
            pass

    GPIO = MockGPIO()

mygpio_handler = GPIOHandler()
