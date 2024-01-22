import os
import serial
from dunebugger_settings import settings
from dunebuggerlogging import logger

class ArduinoHandler:
    def __init__(self):
        self.Arduino = None

        if settings.arduinoConnected:
            if os.path.exists(settings.arduinoSerialPort):
                try:
                    self.Arduino = serial.Serial(settings.arduinoSerialPort, 9600)
                    logger.info(f"Arduino: found device on {settings.arduinoSerialPort} and connected")
                except serial.SerialException as e:
                    logger.critical(f'Arduino: error connecting to {settings.arduinoSerialPort}: {e}')
            else:
                logger.critical(f"Arduino: serial port on {settings.arduinoSerialPort} not available: no communication with Arduino")
