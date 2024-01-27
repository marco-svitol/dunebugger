from dunebuggerlogging import logger
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

def dunequit():
    # Get the process ID (PID) of the current process
    pid = os.getpid()
    # Send the SIGINT signal (equivalent to Ctrl+C)
    os.kill(pid, signal.SIGINT)

def is_raspberry_pi():
    try:
        with open('/proc/device-tree/model', 'r') as model_file:
            model = model_file.read()
            if 'Raspberry Pi' in model:
                return True
            else:
                return False
    except Exception as e:
        return False