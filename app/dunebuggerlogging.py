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