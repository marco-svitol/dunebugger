import logging, logging.config
from os import path
logConfig = path.join(path.dirname(path.abspath(__file__)), 'config/dunebuggerlogging.conf')
logging.config.fileConfig(logConfig) #load logging config file
logger = logging.getLogger('dunebuggerLog')