import time
import atexit
import threading
from dunebugger_logging import logger
from dunebugger_settings import settings
from pwm_handler import PWMHandler


class MotorController:
    def __init__(self, mygpio_handler, GPIO):
        self.mygpio_handler = mygpio_handler
        self.GPIO = GPIO
        self.pwm_motor1 = PWMHandler(GPIO, mygpio_handler.GPIOMap["Motor1PWM"], settings.motor1Freq)
        self.pwm_motor2 = PWMHandler(GPIO, mygpio_handler.GPIOMap["Motor2PWM"], settings.motor2Freq)

    def start(self, motornum, rotation="cw", speed=100):
        logger.debug(f"motor {motornum} start with rotation {rotation} and speed {speed}")

        # Crash prevention
        if (rotation == "cw" and self.mygpio_handler.GPIOMap[f"In_Motor{motornum}LimitCW"] == self.GPIO.HIGH) or (rotation == "ccw" and self.mygpio_handler.GPIOMap[f"In_Motor{motornum}LimitCCW"] == self.GPIO.HIGH):
            logger.warning("Start command aborted to prevent motor crash")
            return

        if rotation == "cw":
            self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motornum}In1"], self.GPIO.HIGH)
            self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motornum}In2"], self.GPIO.LOW)
        else:
            self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motornum}In1"], self.GPIO.LOW)
            self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motornum}In2"], self.GPIO.HIGH)

        if motornum == 1:
            self.pwm_motor1.set_duty_cycle(speed)
        elif motornum == 2:
            self.pwm_motor2.set_duty_cycle(speed)

    def stop(self, motornum):
        logger.debug(f"motor {motornum} stopping")
        self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motornum}In1"], self.GPIO.LOW)
        self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motornum}In2"], self.GPIO.LOW)
        self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motornum}PWM"], self.GPIO.LOW)

    def limitTouch(self, channel, event=None):
        time.sleep(settings.bouncingTreshold + 0.23)  # avoid catching a bouncing
        if self.GPIO.input(channel) != 1:
            return

        GPIOLabel = self.mygpio_handler.getGPIOLabel(channel)
        logger.debug(f"Limit touched on channel {GPIOLabel}")
        motornum = 1 if channel in (self.mygpio_handler.GPIOMap["In_Motor1LimitCCW"], self.mygpio_handler.GPIOMap["In_Motor1LimitCW"]) else 2
        self.stop(motornum)

        if channel == self.mygpio_handler.GPIOMap[f"In_Motor{motornum}LimitCCW"]:
            time.sleep(0.2)
            self.start(motornum, "cw", speed=100)
        elif event is not None:
            self.start(motornum, "ccw", speed=85)
            time.sleep(3)
            self.stop(motornum)
            logger.debug("Event set")
            event.set()

    def reset(self, motornum):
        pos = ""
        if self.GPIO.input(self.mygpio_handler.GPIOMap[f"In_Motor{motornum}LimitCW"]) == self.GPIO.HIGH:
            pos = "CW limit touch"
            logger.debug(f"Motor {motornum} position is {pos}. Short CCW and then CW.")
            self.start(motornum, "ccw", 100)
            time.sleep(0.5)
            return
        elif self.GPIO.input(self.mygpio_handler.GPIOMap[f"In_Motor{motornum}LimitCCW"]) == self.GPIO.HIGH:
            pos = "CCW limit touch"
        else:
            pos = "floating"
        logger.debug(f"Motor {motornum} position is {pos}. Reaching CW limit.")
        self.start(motornum, "cw", 100)

    def motor_clean(self):
        logger.info("Motor remove events detect")
        self.mygpio_handler.removeEventDetect("In_Motor1LimitCCW")
        self.mygpio_handler.removeEventDetect("In_Motor1LimitCW")
        self.mygpio_handler.removeEventDetect("In_Motor2LimitCCW")
        self.mygpio_handler.removeEventDetect("In_Motor2LimitCW")

    def initMotorLimits(self):
        atexit.register(self.motor_clean)
        motor1_reset_event = threading.Event()

        def motor1_callback_with_params(channel):
            self.limitTouch(channel, motor1_reset_event)

        self.mygpio_handler.addEventDetect("In_Motor1LimitCCW", self.limitTouch, 5)
        self.mygpio_handler.addEventDetect("In_Motor1LimitCW", motor1_callback_with_params, 5)

        motor2_reset_event = threading.Event()

        def motor2_callback_with_params(channel):
            self.limitTouch(channel, motor2_reset_event)

        self.mygpio_handler.addEventDetect("In_Motor2LimitCCW", self.limitTouch, 5)
        self.mygpio_handler.addEventDetect("In_Motor2LimitCW", motor2_callback_with_params, 5)

        if settings.motor1Enabled:
            self.reset(1)
        if settings.motor1Enabled:
            motor1_reset_event.wait()
        if settings.motor2Enabled:
            self.reset(2)
        if settings.motor2Enabled:
            motor2_reset_event.wait()
