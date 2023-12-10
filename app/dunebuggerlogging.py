import logging, logging.config

logging.config.fileConfig('./dunebuggerlogging.conf') #load logging config file
logger = logging.getLogger('dunebuggerLog')