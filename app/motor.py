from setupGPIOs import GPIOMap
import RPi.GPIO as GPIO
from dunebuggerlogging import logger 

def start(motornum, rotation="cw",speed=100):
    pwm = GPIO.PWM(GPIOMap["Motor"+str(motornum)+"PWM"],100)
    pwm.start(speed)
    logger.debug("motor "+str(motornum)+" start with rotation "+rotation+" and speed "+str(speed))
    if rotation == "cw":
        GPIO.output(GPIOMap["Motor"+str(motornum)+"In1"],GPIO.HIGH)
        GPIO.output(GPIOMap["Motor"+str(motornum)+"In2"],GPIO.LOW)
    else:
        GPIO.output(GPIOMap["Motor"+str(motornum)+"In1"],GPIO.LOW)
        GPIO.output(GPIOMap["Motor"+str(motornum)+"In2"],GPIO.HIGH)

def stop(motornum):
    logger.debug("motor "+str(motornum)+" stopping")
    GPIO.output(GPIOMap["Motor"+str(motornum)+"In1"],GPIO.LOW)
    GPIO.output(GPIOMap["Motor"+str(motornum)+"In2"],GPIO.LOW)