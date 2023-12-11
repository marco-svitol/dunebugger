
from gpio_handler import mygpio_handler
import RPi.GPIO as GPIO
from dunebuggerlogging import logger 
from pwm_handler import pwm_motor1

def start(motornum, rotation="cw",speed=100):
    logger.debug("motor "+str(motornum)+" start with rotation "+rotation+" and speed "+str(speed)+" PWM GPIO: "+str(mygpio_handler.GPIOMap["Motor"+str(motornum)+"PWM"]))
    if rotation == "cw":
        GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In1"],GPIO.HIGH)
        GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In2"],GPIO.LOW)
    else:
        GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In1"],GPIO.LOW)
        GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In2"],GPIO.HIGH)
    logger.debug("CDC"+str(speed))
    pwm_motor1.set_duty_cycle(speed)

def stop(motornum):
    logger.debug("motor "+str(motornum)+" stopping")
    GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In1"],GPIO.LOW)
    GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In2"],GPIO.LOW)
    GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"PWM"],GPIO.LOW)

def limitTouch(switch):
    logger.debug("Limit touched on switch "+str(switch))
    if switch == mygpio_handler.GPIOMap["Motor1LimitLeft"] or switch == mygpio_handler.GPIOMap["Motor1LimitRight"]:
        stop(1)


    