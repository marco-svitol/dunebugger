from setupGPIOs import GPIOMap
import RPi.GPIO as GPIO
from dunebuggerlogging import logger 

def start(motornum, rotation="cw",speed=100):
    pwm = GPIO.PWM(GPIOMap["Motor"+str(motornum)+"PWM"],5000)
    pwm.start(25)
    logger.debug("motor "+str(motornum)+" start with rotation "+rotation+" and speed "+str(speed)+" PWM GPIO: "+str(GPIOMap["Motor"+str(motornum)+"PWM"]))
    if rotation == "cw":
        GPIO.output(GPIOMap["Motor"+str(motornum)+"In1"],GPIO.HIGH)
        GPIO.output(GPIOMap["Motor"+str(motornum)+"In2"],GPIO.LOW)
    else:
        GPIO.output(GPIOMap["Motor"+str(motornum)+"In1"],GPIO.LOW)
        GPIO.output(GPIOMap["Motor"+str(motornum)+"In2"],GPIO.HIGH)
    pwm.ChangeDutyCycle(speed)

def stop(motornum):
    logger.debug("motor "+str(motornum)+" stopping")
    GPIO.output(GPIOMap["Motor"+str(motornum)+"In1"],GPIO.LOW)
    GPIO.output(GPIOMap["Motor"+str(motornum)+"In2"],GPIO.LOW)
    GPIO.output(GPIOMap["Motor"+str(motornum)+"PWM"],GPIO.LOW)