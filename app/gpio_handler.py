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
        self.gpio_map = {}
        self.logical_map = {}
        self.channels_setup = {}
        self.channels = {}
        self.logical_channels = {}
        self.load_gpio_configuration()
        self.GPIO = GPIO
        self.state_tracker = state_tracker
        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        for channel, config in self.channels_setup.items():
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
            gpio_config = path.join(path.dirname(path.abspath(__file__)), "config/gpio.conf")
            config.read(gpio_config)

            # Load Channels Setup
            try:
                for channel_setup, values in config.items("ChannelsSetup"):
                    channel_setup_values = values.split(", ")
                    self.channels_setup[channel_setup] = channel_setup_values
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading channel setup configuration: {e}")
                # Handle the error as needed

            # Load Channels
            try:
                for physical_channel, values in config.items("Channels"):
                    # Convert the values to tuple if there is more than one element
                    channel_values = literal_eval(values)
                    if isinstance(channel_values, tuple):
                        self.channels[physical_channel] = channel_values
                    else:
                        self.channels[physical_channel] = (channel_values,)
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading channel configuration: {e}")
                # Handle the error as needed

            # Load GPIOMapPhysical
            try:
                for logical_channel, values in config.items("LogicalChannels"):
                    channel, index = self.__extract_variable_info(values)
                    self.logical_channels[logical_channel] = self.channels[channel][index]
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading LogicalChannels configuration: {e}")
                # Handle the error as needed

            # Load GPIOMap
            try:
                for label, logic_label in config.items("GPIOMaps"):
                    self.logical_map[label] = logic_label
                    self.gpio_map[label] = self.logical_channels[logic_label]
            except (configparser.Error, ValueError) as e:
                logger.error(f"Error reading LogicalChannels configuration: {e}")
                # Handle the error as needed

            # Check if StartButton entry exists in GPIOMap
            if settings.startButtonGPIOName not in self.gpio_map:
                raise ValueError(f"GPIOMap must have an entry for {settings.startButtonGPIOName}")

        except (configparser.Error, ValueError) as e:
            logger.error(f"Error reading GPIO configuration: {e}")
            # You might want to handle the error in an appropriate way, e.g., logging or quitting the program

    def get_gpio_label(self, gpio_num):
        for key, value in self.gpio_map.items():
            if value == gpio_num:
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

    def add_event_detect(self, gpio_name, callback, bouncetime=0):
        gpio = self.gpio_map[gpio_name]
        if bouncetime > 0:
            GPIO.add_event_detect(gpio, GPIO.RISING, callback=callback, bouncetime=bouncetime)
        else:
            GPIO.add_event_detect(gpio, GPIO.RISING, callback=callback)

    def remove_event_detect(self, gpio_name):
        gpio = self.gpio_map[gpio_name]
        logger.debug(f"Removing interrupt on {self.get_gpio_label(gpio)}")
        GPIO.remove_event_detect(gpio)

    def clean_gpios(self):
        logger.debug("Cleanup GPIOs")
        GPIO.cleanup()
        self.state_tracker.notify_update("gpios")

    def set_gpio_state(self, gpio_num, value):
        gpio_mode = self.__gpio_get_mode(gpio_num)
        if gpio_mode == self.GPIO.OUT or (not settings.ON_RASPBERRY_PI):
            GPIO.output(gpio_num, value)
            self.state_tracker.notify_update("gpios")
        elif gpio_mode == self.GPIO.IN and settings.ON_RASPBERRY_PI:
            raise ValueError(f"Can't set GPIO #{gpio_num}: it's an input GPIO")

    def __gpiomap_get_gpio(self, gpiomap):
        try:
            return self.gpio_map[gpiomap]
        except Exception:
            return None

    def __gpio_get_mode(self, gpio):
        try:
            return self.GPIO.gpio_function(gpio)
        except Exception:
            return None

    def get_logic_status(self):
        # Iterate over logicalMap to get status
        logic_status = {}
        for label, logic_label in self.logical_map.items():
            gpio_num = self.gpio_map[label]
            try:
                state = "HIGH" if self.GPIO.input(gpio_num) == 1 else "LOW"
            except Exception:
                state = "ERROR"
            logic_status[logic_label] = {"pin": gpio_num, "label": label, "state": state}
        return logic_status

    def get_gpio_status(self):
        gpios = range(0, 28)  # Assuming BCM numbering scheme and 27 available GPIO pins
        gpio_status = []

        for gpio in gpios:
            mode = "UNKNOWN"
            state = "UNKNOWN"
            switch_state = "UNKNOWN"
            label = self.get_gpio_label(gpio) if self.get_gpio_label(gpio) is not None else "_not_found_"

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
                    switch_state = "OFF" if self.GPIO.input(gpio) == 1 else "ON"
                except Exception:
                    state = "ERROR"
                    switch_state = "ERROR"

            gpio_status.append({"logic": self.logical_map.get(label, "_not_found_"), "pin": gpio, "label": label, "mode": mode, "state": state, "switch": switch_state})

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
            # Check if this GPIO number exists in the gpio_map values
            if gpio_num not in self.gpio_map.values():
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
            
