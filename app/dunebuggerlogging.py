import logging, logging.config

logging.config.fileConfig('./config/dunebuggerlogging.conf') #load logging config file
logger = logging.getLogger('dunebuggerLog')