
from gpio_handler import mygpio_handler, GPIO
import time
from dunebuggerlogging import logger 
from pwm_handler import pwm_motor1, pwm_motor2
from dunebugger_settings import settings

def start(motornum, rotation="cw",speed=100):
    logger.debug("motor "+str(motornum)+" start with rotation "+rotation+" and speed "+str(speed))
    
    # Crashprevention
    if rotation == "cw" and mygpio_handler.GPIOMap["In_Motor"+str(motornum)+"LimitCW"] == GPIO.HIGH \
    or rotation == "ccw" and mygpio_handler.GPIOMap["In_Motor"+str(motornum)+"LimitCCW"] == GPIO.HIGH:
        logger.warning("Start command aborted to prevent motor crash")
        return
    ######

    if rotation == "cw":
        GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In1"],GPIO.HIGH)
        GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In2"],GPIO.LOW)
    else:
        GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In1"],GPIO.LOW)
        GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In2"],GPIO.HIGH)
    if motornum == 1:
        pwm_motor1.set_duty_cycle(speed)
    if motornum == 2:
        pwm_motor2.set_duty_cycle(speed)
        
def stop(motornum):
    logger.debug("motor "+str(motornum)+" stopping")
    GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In1"],GPIO.LOW)
    GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"In2"],GPIO.LOW)
    GPIO.output(mygpio_handler.GPIOMap["Motor"+str(motornum)+"PWM"],GPIO.LOW)

def limitTouch(channel, event = None):
    time.sleep(settings.bouncingTreshold+0.23)    # avoid catching a bouncing
    if GPIO.input(channel) != 1:
        #logger.debug ("Warning! Limit touch: below treshold of "+str(settings.bouncingTreshold)+" on channel"+str(channel))
        return
    
    GPIOLabel = mygpio_handler.getGPIOLabel(channel)
    logger.debug("Limit touched on channel "+GPIOLabel)
    motornum = 0
    if channel == mygpio_handler.GPIOMap["In_Motor1LimitCCW"] or channel == mygpio_handler.GPIOMap["In_Motor1LimitCW"]:
        motornum = 1
    else:
        motornum = 2
    stop(motornum)

    if channel == mygpio_handler.GPIOMap["In_Motor"+str(motornum)+"LimitCCW"]:
        time.sleep(0.2)
        start(motornum,"cw", speed=100)
    elif event != None:
        start(motornum, "ccw", speed=85)
        time.sleep(3)
        stop(motornum)   
        logger.debug("Event set")
        event.set()

def reset(motornum):
    pos = ""
    if GPIO.input(mygpio_handler.GPIOMap["In_Motor"+str(motornum)+"LimitCW"]) == GPIO.HIGH:
        pos = "CW limit touch"
        logger.debug("Motor "+str(motornum)+" position is "+pos+". Short CCW and then CW.")
        start(motornum,"ccw",100)
        time.sleep(0.5)
        return
    elif GPIO.input(mygpio_handler.GPIOMap["In_Motor"+str(motornum)+"LimitCCW"]) == GPIO.HIGH:
        pos = "CCW limit touch"
    else:
        pos = "floating"
    logger.debug("Motor "+str(motornum)+" position is "+pos+". Reaching CW limit.")
    start(motornum,"cw",100)





    