
from gpio_handler import mygpio_handler
import RPi.GPIO as GPIO
import time
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
    motor = 0
    if switch == mygpio_handler.GPIOMap["Motor1LimitLeft"] or switch == mygpio_handler.GPIOMap["Motor1LimitRight"]:
        motor = 1
    else:
        motor = 2
    stop(motor)
    if switch == mygpio_handler.GPIOMap["Motor1LimitLeft"] or switch == mygpio_handler.GPIOMap["Motor2LimitLeft"]:
        time.sleep(0.2)
        start(motor,"cw", speed=100)
        



    