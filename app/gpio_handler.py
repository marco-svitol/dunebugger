from dunebuggerlogging import logger
import configparser
from ast import literal_eval
from dunebugger_settings import settings
from os import path
import re
from utils import dunequit
if settings.ON_RASPBERRY_PI:
    import RPi.GPIO as GPIO
else:
    from dunemock import GPIO

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
        self.channelsSetup = {}
        self.channels = {}
        self.logicalChannels = {}
        self.load_gpio_configuration()
        self.GPIO = GPIO

        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        for channel, config in self.channelsSetup.items():
            pin_setup, initial_state = config
            if (pin_setup == 'OUT' and (initial_state == 'HIGH' or initial_state == 'LOW')):
                GPIO.setup(self.channels[channel], GPIO.OUT, initial=GPIO.HIGH if initial_state == 'HIGH' else GPIO.LOW)
            elif (pin_setup == 'IN' and (initial_state == 'DOWN' or initial_state == 'UP')):
                pull_up_down = GPIO.PUD_UP if initial_state == 'UP' else GPIO.PUD_DOWN
                GPIO.setup(self.channels[channel], GPIO.IN, pull_up_down)

    def load_gpio_configuration(self):
        config = configparser.ConfigParser()
        # Set optionxform to lambda x: x to preserve case
        config.optionxform = lambda x: x
        try:
            gpioConfig = path.join(path.dirname(path.abspath(__file__)), 'config/gpio.conf')
            config.read(gpioConfig)

            # Load Channels Setup
            try:
                for channelSetup, values in config.items('ChannelsSetup'):
                    channelSetupValues = values.split(', ')
                    self.channelsSetup[channelSetup] = channelSetupValues
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading channel setup configuration: {e}")
                # Handle the error as needed

            # Load Channels
            try:
                for physicalChannel, values in config.items('Channels'):
                    # Convert the values to tuple if there is more than one element
                    channel_values = literal_eval(values)
                    if isinstance(channel_values, tuple):
                        self.channels[physicalChannel] = channel_values
                    else:
                        self.channels[physicalChannel] = (channel_values,)
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading channel configuration: {e}")
                # Handle the error as needed

            # Load GPIOMapPhysical
            try:
                for logicalChannel, values in config.items('LogicalChannels'):
                    channel, index = self.__extract_variable_info(values)
                    self.logicalChannels[logicalChannel] = self.channels[channel][index]
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading LogicalChannels configuration: {e}")
                # Handle the error as needed
        
            # Load GPIOMap
            try:
                for GPIOMap, values in config.items('GPIOMaps'):
                    logicalChannel, index = self.__extract_variable_info(values)
                    self.GPIOMap[GPIOMap] = self.logicalChannels[index]
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading LogicalChannels configuration: {e}")
                # Handle the error as needed

            # Check if "I_StartButton" entry exists in GPIOMap
            if 'In_StartButton' not in self.GPIOMap:
                raise ValueError('GPIOMap must have an entry for "I_StartButton"')

        except (configparser.Error, ValueError) as e:
            logger.error(f"Error reading GPIO configuration: {e}")
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

    def setupStartButton(self, callback):
         startButton = self.GPIOMap[settings.startButton]
         GPIO.add_event_detect(startButton,GPIO.RISING,callback=callback,bouncetime=200)

    def removeStartButton(self):
        startButton = self.GPIOMap[settings.startButton]
        GPIO.remove_event_detect(startButton)

    import RPi.GPIO as GPIO

def RPiwrite(gpio,bit):
    logger.debug("RPi "+gpio+" write "+str(bit))
    bit = not bit
    GPIO.output(mygpio_handler.GPIOMap[gpio],bit)

def RPiToggle(gpio):
    GPIO.output(mygpio_handler.GPIOMap[gpio], not GPIO.input(mygpio_handler.GPIOMap[gpio]))
    #logger.verbose("Toggled RPi "+gpio+" to "+str(GPIO.input(mygpio_handler.GPIOMap[gpio])))

class TerminalInterpreter:
    def __init__(self, gpio_handler):
        self.gpio_handler = gpio_handler

    def process_terminal_input(self, input_str):
        # Process commands received through the terminal
        command_strs = input_str.lower().split(',')

        for command_str in command_strs:
            if command_str == "":
                continue

            elif command_str == "h":
                print(f"I am a Raspberry. You can ask me to:\n\
                s: show gpio status\n\
                q: quit\n\
                ")
                continue

            elif command_str == "s":
                self.show_gpio_status()
                continue

            elif command_str == "q":
                dunequit()
                continue

            logger.info(f"Unkown command {command_str}")
    
    def show_gpio_status(self):
        gpio_pins = range(1, 28)  # Assuming BCM numbering scheme and 27 available GPIO pins

        for pin in gpio_pins:
            # Determine mode
            try:
                if self.gpio_handler.GPIO.gpio_function(pin) == self.gpio_handler.GPIO.IN:
                    mode = "INPUT"
                elif self.gpio_handler.GPIO.gpio_function(pin) == self.gpio_handler.GPIO.OUT:
                    mode = "OUTPUT"
            except Exception as e:
                mode = "ERROR"

            # Read state
            if mode == "INPUT":
                try:
                    state = self.gpio_handler.GPIO.input(pin)
                except Exception as e:
                    state = "ERROR"
   
mygpio_handler = GPIOHandler()

if settings.ON_RASPBERRY_PI:
    terminalInterpreter = TerminalInterpreter(mygpio_handler)
else:
    from dunemock import TerminalInterpreter
    terminalInterpreter = TerminalInterpreter(mygpio_handler)