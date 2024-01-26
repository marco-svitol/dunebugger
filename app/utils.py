from dunebuggerlogging import logger
import time
from dunebugger_settings import settings
import os
import signal

def ArduinoSend(command):
    global Arduino    
    ccommand = command.replace("\n","")
    if Arduino != False:
        Arduino.write(bytes(command,'UTF-8'))
        logger.debug("Sending command "+ccommand+" to Arduino")
    else:
        ccommand = command.replace("\n","")
        logger.warning("ignoring command "+ccommand+" to Arduino")

def waituntil(sec):
    logger.debug("Waiting: "+str(sec-settings.cycleoffset))
    time.sleep((sec-settings.cycleoffset) * settings.cyclespeed)
    settings.cycleoffset = sec

def dunequit():
    # Get the process ID (PID) of the current process
    pid = os.getpid()
    # Send the SIGINT signal (equivalent to Ctrl+C)
    os.kill(pid, signal.SIGINT)