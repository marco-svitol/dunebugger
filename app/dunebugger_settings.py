import threading, os
from os import path
import configparser

class DunebuggerSettings:
    def __init__(self):
        # Load configuration from dunebugger.conf
        self.load_configuration()

        # Rest of your __init__ method

    def load_configuration(self):
        config = configparser.ConfigParser()

        try:
            dunebuggerConfig = path.join(path.dirname(path.abspath(__file__)), 'config/dunebugger.conf')
            config.read(dunebuggerConfig)

            # Example of how to read values from the configuration file
            self.ArduinoConnected = config.getboolean('General', 'ArduinoConnected')
            self.cyclelength = config.getint('General', 'cyclelength')
            self.bouncingTreshold = config.getfloat('General', 'bouncingTreshold')
            self.eastereggEnabled = config.getboolean('General', 'eastereggEnabled')
            self.cycleoffset = config.getint('General', 'cycleoffset')
            self.randomActionsEnabled = config.getboolean('General', 'randomActionsEnabled')
            self.randomActionsMinSecs = config.getint('General', 'randomActionsMinSecs')
            self.randomActionsMaxSecs = config.getint('General', 'randomActionsMaxSecs')

            # Motors
            self.motor1Enabled = config.getboolean('Motors', 'motor1Enabled')
            self.motor2Enabled = config.getboolean('Motors', 'motor2Enabled')
            self.motor1Freq = config.getint('Motors', 'motor1Freq')
            self.motor2Freq = config.getint('Motors', 'motor2Freq')

            # Debug
            self.cyclespeed = config.getfloat('Debug', 'cyclespeed')
            self.testdunebugger = config.getboolean('Debug', 'testdunebugger')
            self.ON_RASPBERRY_PI  = os.getenv("DEBUG", False)

        except configparser.Error as e:
            print(f"Error reading configuration: {e}")

settings = DunebuggerSettings()





