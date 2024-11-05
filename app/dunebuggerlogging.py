import logging, logging.config
from os import path

logConfig = path.join(path.dirname(path.abspath(__file__)), 'config/dunebuggerlogging.conf')
logging.config.fileConfig(logConfig) #load logging config file
logger = logging.getLogger('dunebuggerLog')

COLORS = {
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'MAGENTA': '\033[95m',
    'CYAN': '\033[96m',
    'RESET': '\033[0m'
}

def get_logging_level_from_name(level_str):
    # Convert the string level to a logging level
    level = getattr(logging, level_str.upper(), None)
    if not isinstance(level, int):
        return ""
    else:
        return level

def set_logger_level(logger_name, level):
    try:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        print(f"Logger {logger_name} level set to {logging.getLevelName(level)}")
    except Exception as exc:
        print(f"Error while setting logger ${logger_name} level to {logging.getLevelName(level)}: ${str(exc)}")
        
