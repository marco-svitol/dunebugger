import configparser
from ast import literal_eval
from os import path
import re
import atexit
from dunebugger_logging import logger
from dunebugger_settings import settings

if settings.ON_RASPBERRY_PI:
    import RPi.GPIO as GPIO  # type: ignore
else:
    from dunemock import GPIO
class GPIOHandler:
    def __init__(self, state_tracker):
        # Load GPIO configuration from gpio_config.conf
        self.GPIOMap = {}
        self.channelsSetup = {}
        self.channels = {}
        self.logicalChannels = {}
        self.load_gpio_configuration()
        self.GPIO = GPIO
        self.state_tracker = state_tracker
        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        for channel, config in self.channelsSetup.items():
            pin_setup, initial_state = config
            if pin_setup == "OUT" and (initial_state == "HIGH" or initial_state == "LOW"):
                GPIO.setup(
                    self.channels[channel],
                    GPIO.OUT,
                    initial=GPIO.HIGH if initial_state == "HIGH" else GPIO.LOW,
                )
            elif pin_setup == "IN" and (initial_state == "DOWN" or initial_state == "UP"):
                pull_up_down = GPIO.PUD_UP if initial_state == "UP" else GPIO.PUD_DOWN
                GPIO.setup(self.channels[channel], GPIO.IN, pull_up_down)

        atexit.register(self.clean_gpios)

    def load_gpio_configuration(self):
        config = configparser.ConfigParser()
        # Set optionxform to lambda x: x to preserve case
        config.optionxform = lambda x: x
        try:
            gpioConfig = path.join(path.dirname(path.abspath(__file__)), "config/gpio.conf")
            config.read(gpioConfig)

            # Load Channels Setup
            try:
                for channelSetup, values in config.items("ChannelsSetup"):
                    channelSetupValues = values.split(", ")
                    self.channelsSetup[channelSetup] = channelSetupValues
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading channel setup configuration: {e}")
                # Handle the error as needed

            # Load Channels
            try:
                for physicalChannel, values in config.items("Channels"):
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
                for logicalChannel, values in config.items("LogicalChannels"):
                    channel, index = self.__extract_variable_info(values)
                    self.logicalChannels[logicalChannel] = self.channels[channel][index]
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading LogicalChannels configuration: {e}")
                # Handle the error as needed

            # Load GPIOMap
            try:
                for GPIOMap, values in config.items("GPIOMaps"):
                    logicalChannel, index = self.__extract_variable_info(values)
                    self.GPIOMap[GPIOMap] = self.logicalChannels[index]
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading LogicalChannels configuration: {e}")
                # Handle the error as needed

            # Check if StartButton entry exists in GPIOMap
            if settings.startButtonGPIOName not in self.GPIOMap:
                raise ValueError(f"GPIOMap must have an entry for {settings.startButtonGPIOName}")

        except (configparser.Error, ValueError) as e:
            logger.error(f"Error reading GPIO configuration: {e}")
            # You might want to handle the error in an appropriate way, e.g., logging or quitting the program

    def getGPIOLabel(self, GPIONum):
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
        match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\[(.+)\]", expression)

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

    def addEventDetect(self, gpioName, callback, bouncetime=0):
        gpio = self.GPIOMap[gpioName]
        if bouncetime > 0:
            GPIO.add_event_detect(gpio, GPIO.RISING, callback=callback, bouncetime=bouncetime)
        else:
            GPIO.add_event_detect(gpio, GPIO.RISING, callback=callback)

    def removeEventDetect(self, gpioName):
        gpio = self.GPIOMap[gpioName]
        logger.debug(f"Removing interrupt on {self.getGPIOLabel(gpio)}")
        GPIO.remove_event_detect(gpio)

    def clean_gpios(self):
        logger.debug("Cleanup GPIOs")
        GPIO.cleanup()
        self.state_tracker.notify_update("gpios")

    def set_gpio_state(self, gpio_num, value):
        gpiomode = self.__gpio_get_mode(gpio_num)
        if gpiomode == self.GPIO.OUT or (not settings.ON_RASPBERRY_PI):
            GPIO.output(gpio_num, value)
            self.state_tracker.notify_update("gpios")
        elif gpiomode == self.GPIO.IN and settings.ON_RASPBERRY_PI:
            raise ValueError(f"Can't set GPIO #{gpio_num}: it's an input GPIO")

    def __gpiomap_get_gpio(self, gpiomap):
        try:
            return self.GPIOMap[gpiomap]
        except Exception:
            return None

    def __gpio_get_mode(self, gpio):
        try:
            return self.GPIO.gpio_function(gpio)
        except Exception:
            return None

    def get_gpio_status(self):
        gpios = range(0, 28)  # Assuming BCM numbering scheme and 27 available GPIO pins
        gpio_status = []

        for gpio in gpios:
            mode = "UNKNOWN"
            state = "UNKNOWN"
            switchstate = "UNKNOWN"
            label = self.getGPIOLabel(gpio) if self.getGPIOLabel(gpio) is not None else "_not_found_"

            # Determine mode
            try:
                if self.GPIO.gpio_function(gpio) == self.GPIO.IN:
                    mode = "INPUT"
                elif self.GPIO.gpio_function(gpio) == self.GPIO.OUT:
                    mode = "OUTPUT"
            except Exception:
                mode = "ERROR"

            # Read state
            if mode == "INPUT" or mode == "OUTPUT":
                try:
                    state = "HIGH" if self.GPIO.input(gpio) == 1 else "LOW"
                    switchstate = "OFF" if self.GPIO.input(gpio) == 1 else "ON"
                except Exception:
                    state = "ERROR"
                    switchstate = "ERROR"

            gpio_status.append({"pin": gpio, "label": label, "mode": mode, "state": state, "switch": switchstate})

        return gpio_status

    def validate_switch_command_args(self, command_parts):
        if not command_parts or len(command_parts) != 2:
            arg_count = len(command_parts) if command_parts else 0
            raise ValueError(f"GPIO command requires 2 arguments: <gpio_name/number> <on/off/toggle>. Got {arg_count} argument(s).")
        
        gpio_identifier = command_parts[0]
        action = command_parts[1].lower()
        
        # Validate action
        if action not in ["on", "off", "toggle"]:
            raise ValueError(f"Invalid action: {action}. Use 'on', 'off', or 'toggle'.")
        
        # Check if gpio_identifier is a valid integer GPIO number
        try:
            gpio_num = int(gpio_identifier)
            # Check if this GPIO number exists in the GPIOMap values
            if gpio_num not in self.GPIOMap.values():
                raise ValueError(f"Invalid GPIO number: {gpio_num}")
        except ValueError:
            # It's a string, so use __gpiomap_get_gpio to convert to GPIO number
            gpio_num = self.__gpiomap_get_gpio(gpio_identifier)
            if gpio_num is None:
                raise ValueError(f"GPIO map '{gpio_identifier}' not found.")
        
        # Determine the action value
        if action == "toggle":
            # Read current value and toggle it
            current_value = GPIO.input(gpio_num)
            action = current_value ^ 1
        else:
            # returned action must be 0 if "on", 1 if "off"
            action = GPIO.LOW if action == "on" else GPIO.HIGH
        
        return gpio_num, action

    def execute_gpio_command(self, command_parts, dry_run=False):
        gpio, action = self.validate_switch_command_args(command_parts)
        if dry_run:
            return True
        else:
            self.set_gpio_state(gpio, action)
            return (f"GPIO {gpio} set to {'ON' if action == GPIO.LOW else 'OFF'}")
            
