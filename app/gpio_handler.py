from dunebuggerlogging import logger, COLORS
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
        return None

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

    def gpio_set_output(self, gpiocast,value):
        if isinstance(gpiocast, int):
            gpio = gpiocast
            gpiomap = self.getGPIOLabel(gpio)
        else:
            gpiomap = gpiocast
            gpio = self.__gpiomap_get_gpio(gpiomap)

        gpiomode = self.__gpio_get_mode(gpio)
        if gpiomap is not None: 
            if gpiomode == self.GPIO.OUT or (not settings.ON_RASPBERRY_PI):
                logger.debug(f"{gpiomap} {value}")
                bit = int(value == "off")
                if gpiomode == self.GPIO.IN:
                    bit = int(not bit)
                GPIO.output(gpio,bit)
            elif gpiomode == self.GPIO.IN and settings.ON_RASPBERRY_PI:
                logger.error(f"Can't set an input GPIO. (gpio={gpio}, gpiomap={gpiomap})")
        else:
            logger.error(f"gpio_set_output: gpio={gpio}, gpiomap={gpiomap}, gpiomode={gpiomode}")


    def gpiomap_toggle_output(self, gpiomap):
        logger.debug(f"Toggling {gpiomap}")
        GPIO.output(self.GPIOMap[gpiomap], not GPIO.input(self.GPIOMap[gpiomap]))

    def __gpiomap_get_gpio(self, gpiomap):
        try:
            return self.GPIOMap[gpiomap]
        except Exception as e:
            return None

    def __gpio_get_mode(self, gpio):
        try:
            return self.GPIO.gpio_function(gpio)
        except Exception as e:
            return None
        
    def show_gpio_status(self, gpio_handler = None):
        gpios = range(0, 28)  # Assuming BCM numbering scheme and 27 available GPIO pins
        print("Current GPIO Status:") 
        for gpio in gpios:
            mode = "UNKNOWN"
            state = "UNKNOWN"
            # Determine mode
            try:
                if self.GPIO.gpio_function(gpio) == self.GPIO.IN:
                    mode = "INPUT"
                    color = COLORS['CYAN']
                elif self.GPIO.gpio_function(gpio) == self.GPIO.OUT:
                    mode = "OUTPUT"
                    color = COLORS['BLUE']
            except Exception as e:
                mode = "ERROR"

            # Read state
            if mode == "INPUT" or mode == "OUTPUT":
                try:
                    state = 'HIGH' if self.GPIO.input(gpio) == 1 else 'LOW'
                    switchstate = 'OFF' if self.GPIO.input(gpio) == 1 else 'ON'
                    switchcolor = COLORS['MAGENTA'] if self.GPIO.input(gpio) == 1 else COLORS['GREEN']
                
                except Exception as e:
                    state = "ERROR"
                    color = COLORS['RED']
                    switchcolor = color
            print(f"{color}Pin {gpio} label: {self.getGPIOLabel(gpio) if self.getGPIOLabel(gpio) is not None else '_not_found_'} \
mode: {mode}, state: {state}, switch: {COLORS['RESET']}{switchcolor}{switchstate}{COLORS['RESET']}")
            
class TerminalInterpreter:
    def __init__(self, gpio_handler):
        self.gpio_handler = gpio_handler
        if settings.ON_RASPBERRY_PI: 
            self.help = f"I am a Raspberry. You can ask me to:\n\
                s: show gpio status\n\
                t: show dunebugger conf\n\
                l: reload dunebugger conf\n\
                <gpionum or label> on: set gpio status High (OUTPUT gpios only)\n\
                <gpionum or label> off: set gpio status Low (OUTPUT gpios only)\n\
                r: toggle random actions\
                q: quit\n\
                ? or h: help\
                "
            self.show_gpio_status = self.gpio_handler.show_gpio_status
        else:
            self.help = f"I am not a Raspberry. You can ask me to:\n\
                s: show gpio status\n\
                t: show dunebugger conf\n\
                l: reload dunebugger conf\n\
                <#gpionum or label> on: set gpio status High\n\
                <#gpionum or label> off: set gpio status Low\n\
                r: toggle random actions\
                q: quit\n\
                ? or h: help\
                "
            self.show_gpio_status = self.gpio_handler.GPIO.show_gpio_status

    def process_terminal_input(self, input_str):
        # Process commands received through the terminal
        command_strs = input_str.split(',')

        for command_str in command_strs:
            if command_str == "":
                continue

            elif command_str in {"h", "?"}:
                print(self.help)
                continue

            elif command_str == "s":
                self.show_gpio_status(self.gpio_handler)
                continue
            
            elif command_str == "t":
                settings.show_configuration()
                continue

            elif command_str == "l":
                settings.load_configuration()
                continue

            elif command_str == "q":
                dunequit()
                continue

            elif command_str in {"r"}:
                if settings.random_actions_event.is_set():
                    settings.random_actions_event.clear()
                    print(f"Random actions enabled")
                else:
                    settings.random_actions_event.set()
                    print(f"Random actions disabled")
                continue

            elif command_str.startswith("#"):
                # Handle commands starting with "#"
                command_parts = command_str[1:].split()  # Remove "#" from the beginning
                if len(command_parts) == 2 and (command_parts[1] == "on" or command_parts[1] == "off"):
                    gpio = int(command_parts[0])
                    self.gpio_handler.gpio_set_output(gpio, command_parts[1])
                    continue
        
            else:
                # Handle other commands
                command_parts = command_str.split()
                if len(command_parts) == 2 and (command_parts[1] == "on" or command_parts[1] == "off"):
                    gpiomap = command_parts[0]
                    self.gpio_handler.gpio_set_output(gpiomap, command_parts[1])
                    continue

            logger.info(f"Unkown command {command_str}")


mygpio_handler = GPIOHandler()
terminalInterpreter = TerminalInterpreter(mygpio_handler)
