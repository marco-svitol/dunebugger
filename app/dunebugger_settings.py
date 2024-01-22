import threading, os
from os import path
import configparser
from dotenv import load_dotenv
from dunebuggerlogging import logger

class DunebuggerSettings:
    def __init__(self):
        # Load configuration from dunebugger.conf
        load_dotenv()
        self.config = configparser.ConfigParser()
        # Set optionxform to lambda x: x to preserve case
        self.config.optionxform = lambda x: x
        self.load_configuration()
        

    # def load_configuration(self):
    #     config = configparser.ConfigParser()

    #     try:
    #         dunebuggerConfig = path.join(path.dirname(path.abspath(__file__)), 'config/dunebugger.conf')
    #         config.read(dunebuggerConfig)

    #         self.ArduinoConnected = config.getboolean('General', 'ArduinoConnected')
    #         self.cyclelength = config.getint('General', 'cyclelength')
    #         self.bouncingTreshold = config.getfloat('General', 'bouncingTreshold')
    #         self.eastereggEnabled = config.getboolean('General', 'eastereggEnabled')
    #         self.cycleoffset = config.getint('General', 'cycleoffset')
    #         self.randomActionsEnabled = config.getboolean('General', 'randomActionsEnabled')
    #         self.randomActionsMinSecs = config.getint('General', 'randomActionsMinSecs')
    #         self.randomActionsMaxSecs = config.getint('General', 'randomActionsMaxSecs')

    #         # Motors
    #         self.motor1Enabled = config.getboolean('Motors', 'motor1Enabled')
    #         self.motor2Enabled = config.getboolean('Motors', 'motor2Enabled')
    #         self.motor1Freq = config.getint('Motors', 'motor1Freq')
    #         self.motor2Freq = config.getint('Motors', 'motor2Freq')

    #         # Debug
    #         self.cyclespeed = config.getfloat('Debug', 'cyclespeed')
    #         self.testdunebugger = config.getboolean('Debug', 'testdunebugger')
    #         self.ON_RASPBERRY_PI  = os.getenv("ON_RASPBERRY_PI")

    def load_configuration(self):
        

        try:
            dunebuggerConfig = path.join(path.dirname(path.abspath(__file__)), 'config/dunebugger.conf')
            self.config.read(dunebuggerConfig)

            for section in ['General', 'Audio', 'Motors', 'Debug']:
                for option in self.config.options(section):
                    value = self.config.get(section, option)
                    setattr(self, option, self.validate_option(section, option, value))
                    logger.info(f"{option}: {value}")

            self.ON_RASPBERRY_PI = os.getenv("ON_RASPBERRY_PI")
            logger.info(f"ON_RASPBERRY_PI: {self.ON_RASPBERRY_PI}")

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
                elif option in ['sequenceFolder', 'arduinoSerialPort', 'startButton']:
                    return str(value)
            elif section == 'Audio':
                if option in ['normalMusicVolume', 'normalSfxVolume', 'quietMusicVol', 'quietSfxVol',
                              'fadeoutsec', 'ignoreQuietTime']:
                    return int(value) if option != 'ignoreQuietTime' else self.config.getboolean(section, option)
                elif option in ['musicpath', 'sfxpath', 'sfxfile', 'easteregg', 'entrysong']:
                    return str(value)
            elif section == 'Motors':
                if option in ['motor1Freq', 'motor2Freq']:
                    return int(value)
                elif option in ['motor1Enabled', 'motor2Enabled']:
                    return self.config.getboolean(section, option)
            elif section == 'Debug':
                if option == 'cyclespeed':
                    return float(value)
                elif option == 'testdunebugger':
                    return self.config.getboolean(section, option)
        except (configparser.NoOptionError, ValueError):
            raise ValueError(f"Invalid configuration: Section={section}, Option={option}, Value={value}")

        # If no specific validation is required, return the original value
        return value
    

        # except configparser.Error as e:
        #     print(f"Error reading configuration: {e}")

settings = DunebuggerSettings()





