from os import path
import configparser
from dotenv import load_dotenv
from dunebugger_logging import logger, get_logging_level_from_name, set_logger_level
from utils import is_raspberry_pi


class DunebuggerSettings:
    def __init__(self):
        load_dotenv()
        self.config = configparser.ConfigParser()
        # Set optionxform to lambda x: x to preserve case
        self.config.optionxform = lambda x: x
        self.dunebugger_config = path.join(path.dirname(path.abspath(__file__)), "config/dunebugger.conf")
        self.command_handlers = {}
        self.commands_config_path = path.join(path.dirname(path.abspath(__file__)), "config/commands.conf")
        self.load_commands(self.commands_config_path)
        self.load_configuration(self.dunebugger_config)
        self.override_configuration()
        set_logger_level("dunebuggerLog", self.dunebuggerLogLevel)

    def show_configuration(self):
        print("Current Configuration:")
        for attr_name in dir(self):
            if not attr_name.startswith("__") and not callable(getattr(self, attr_name)):
                print(f"{attr_name}: {getattr(self, attr_name)}")

    def load_configuration(self, dunebugger_config):
        try:
            self.config.read(dunebugger_config)
            for section in ["General", "MessageQueue", "Audio", "Motors", "Debug", "Log"]:
                for option in self.config.options(section):
                    value = self.config.get(section, option)
                    setattr(self, option, self.validate_option(section, option, value))
                    logger.debug(f"{option}: {value}")

            self.ON_RASPBERRY_PI = is_raspberry_pi()
            logger.debug(f"ON_RASPBERRY_PI: {self.ON_RASPBERRY_PI}")
            logger.info("Configuration loaded successfully")
        except configparser.Error as e:
            logger.error(f"Error reading {dunebugger_config} configuration: {e}")

    def load_commands(self, commands_config_path):
        try:
            self.config.read(commands_config_path)
            for command, value in self.config.items("Commands"):
                parts = value.split(", ")
                handler = parts[0]
                description = parts[1].strip('"')
                
                self.command_handlers[command] = {
                    "handler": handler,
                    "description": description
                }

        except configparser.Error as e:
            logger.error(f"Error reading {commands_config_path} configuration: {e}")

    def validate_option(self, section, option, value):
        # Validation for specific options
        try:
            if section == "General":
                if option in [
                    "cyclelength",
                    "cycleoffset",
                    "randomActionsMinSecs",
                    "randomActionsMaxSecs",
                ]:
                    return int(value)
                elif option == "bouncingTreshold":
                    return float(value)
                elif option in ["arduinoConnected", "eastereggEnabled", "randomActionsEnabled"]:
                    return self.config.getboolean(section, option)
                elif option in [
                    "sequenceFolder",
                    "sequenceFile",
                    "standbyFile",
                    "offFile",
                    "randomElementsFile",
                    "arduinoSerialPort",
                    "startButtonGPIOName",
                ]:
                    return str(value)
                elif option == "initializationCommandsString":
                    commands = value.split(",")
                    for command in commands:
                        if command not in self.command_handlers:
                            raise ValueError(f"Invalid commands in initializationCommandsString: {command}")
            elif section == "MessageQueue":
                if option in ["mQueueServers", "mQueueClientID", "mQueueSubjectRoot"]:
                    return str(value)
                elif option in ["mQueueStateCheckIntervalSecs", "mQueueCyclePlayingResolutionSecs"]:
                    return int(value)
            elif section == "Audio":
                if option in [
                    "normalMusicVolume",
                    "normalSfxVolume",
                    "quietMusicVol",
                    "quietSfxVol",
                    "ignoreQuietTime",
                ]:
                    return int(value) if option != "ignoreQuietTime" else self.config.getboolean(section, option)
                elif option in ["easteregg", "vlcdevice"]:
                    return str(value)
            elif section == "Motors":
                if option in ["motor1Freq", "motor2Freq"]:
                    return int(value)
                elif option in ["motorEnabled", "motor1Enabled", "motor2Enabled"]:
                    return self.config.getboolean(section, option)
            elif section == "Debug":
                if option == "cyclespeed":
                    return float(value)
            elif section == "Log":
                logLevel = get_logging_level_from_name(value)
                if logLevel == "":
                    return get_logging_level_from_name("INFO")
                else:
                    return logLevel

        except (configparser.NoOptionError, ValueError) as e:
            raise ValueError(f"Invalid configuration: Section={section}, Option={option}, Value={value}. Error: {e}")

        # If no specific validation is required, return the original value
        return value

    def override_configuration(self):
        if not self.ON_RASPBERRY_PI:
            self.vlcdevice = ""


settings = DunebuggerSettings()
