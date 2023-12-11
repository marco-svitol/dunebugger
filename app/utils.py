from dunebuggerlogging import logger
import time, RPi.GPIO as GPIO
from gpio_handler import mygpio_handler
from dunebugger_settings import settings

def ArduinoSend(command):
    global Arduino    
    ccommand = command.replace("\n","")
    if Arduino != False:
        Arduino.write(bytes(command,'UTF-8'))
        logger.debug("Sending command "+ccommand+" to Arduino")
    else:
        ccommand = command.replace("\n","")
        logger.warning("ignoring command "+ccommand+" to Arduino")

def RPiwrite(gpio,bit):
    bit = not bit
    GPIO.output(mygpio_handler.GPIOMap[gpio],bit)
    logger.debug("RPi "+gpio+" write "+str(bit))

def waituntil(sec):
    logger.debug("Waiting: "+str(sec-settings.cycleoffset))
    time.sleep((sec-settings.cycleoffset) * settings.cyclespeed)
    settings.cycleoffset = sec