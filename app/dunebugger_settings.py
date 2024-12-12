import threading, os
from os import path
import configparser
from dotenv import load_dotenv
from dunebuggerlogging import logger, get_logging_level_from_name, set_logger_level

class DunebuggerSettings:
    def __init__(self):
        # Load configuration from dunebugger.conf
        load_dotenv()
        self.config = configparser.ConfigParser()
        # Set optionxform to lambda x: x to preserve case
        self.config.optionxform = lambda x: x
        self.load_configuration()
        self.override_configuration()
        self.cycle_thread_lock = threading.Lock()
        self.random_actions_event = threading.Event()
        set_logger_level("dunebuggerLog", self.dunebuggerLogLevel)

    def show_configuration(self):
        print("Current Configuration:")
        for attr_name in dir(self):
            if not attr_name.startswith('__') and not callable(getattr(self, attr_name)):
                print(f"{attr_name}: {getattr(self, attr_name)}")
        # Print state of random_actions_event
        random_actions_status =  "off" if self.random_actions_event.is_set() else "on"
        print(f"Random actions: {random_actions_status}")

    def load_configuration(self):
        from utils import is_raspberry_pi
        
        try:
            dunebuggerConfig = path.join(path.dirname(path.abspath(__file__)), 'config/dunebugger.conf')
            self.config.read(dunebuggerConfig)

            for section in ['General', 'Audio', 'Motors', 'Debug', 'Log']:
                for option in self.config.options(section):
                    value = self.config.get(section, option)
                    setattr(self, option, self.validate_option(section, option, value))
                    logger.debug(f"{option}: {value}")

            self.ON_RASPBERRY_PI = is_raspberry_pi()
            logger.debug(f"ON_RASPBERRY_PI: {self.ON_RASPBERRY_PI}")

        except configparser.Error as e:
            logger.error(f"Error reading configuration: {e}")

    def validate_option(self, section, option, value):
        # Validation for specific options
        try:
            if section == 'General':
                if option in ['cyclelength', 'cycleoffset', 'randomActionsMinSecs', 'randomActionsMaxSecs']:
                    return int(value)
                elif option == 'bouncingTreshold':
                    return float(value)
                elif option in ['arduinoConnected', 'eastereggEnabled', 'randomActionsEnabled']:
                    return self.config.getboolean(section, option)
                elif option in ['sequenceFolder', 'sequenceFile','standbyFile','offFile','randomElementsFile','arduinoSerialPort', 'startButtonGPIOName']:
                    return str(value)
            elif section == 'Audio':
                if option in ['normalMusicVolume', 'normalSfxVolume', 'quietMusicVol', 'quietSfxVol', 'ignoreQuietTime']:
                    return int(value) if option != 'ignoreQuietTime' else self.config.getboolean(section, option)
                elif option in ['easteregg', 'vlcdevice']:
                    return str(value)
            elif section == 'Motors':
                if option in ['motor1Freq', 'motor2Freq']:
                    return int(value)
                elif option in ['motorEnabled', 'motor1Enabled', 'motor2Enabled']:
                    return self.config.getboolean(section, option)
            elif section == 'Debug':
                if option == 'cyclespeed':
                    return float(value)
            elif section == 'Log':
                logLevel= get_logging_level_from_name(value)
                if (logLevel == ""):
                    return get_logging_level_from_name("INFO")
                else:
                    return logLevel
                
        except (configparser.NoOptionError, ValueError):
            raise ValueError(f"Invalid configuration: Section={section}, Option={option}, Value={value}")

        # If no specific validation is required, return the original value
        return value
    
    def override_configuration(self):
        if not self.ON_RASPBERRY_PI:
            self.vlcdevice = ''
            
settings = DunebuggerSettings()





