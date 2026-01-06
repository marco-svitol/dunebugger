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
        if settings.motorEnabled:
            self.init_pwm()
        # self.pwm_motor1 = PWMHandler(GPIO, mygpio_handler.GPIOMap["Motor1PWM"], settings.motor1Freq)
        # self.pwm_motor2 = PWMHandler(GPIO, mygpio_handler.GPIOMap["Motor2PWM"], settings.motor2Freq)

    def init_pwm(self):
        self.pwm_motor1 = PWMHandler(self.GPIO, self.mygpio_handler.GPIOMap["Motor1PWM"], settings.motor1Freq)
        self.pwm_motor2 = PWMHandler(self.GPIO, self.mygpio_handler.GPIOMap["Motor2PWM"], settings.motor2Freq)
        logger.info("Motor PWM initialized")

    def validate_motor_command_args(self, args):
        if len(args) < 1:
            raise ValueError("At least one argument is required")
        
        # Check if first argument is 'init'
        if args[0].lower() == "init":
            return True, None, None, None
        
        if len(args) < 3:
            raise ValueError("Motor number, rotation, and speed are required")
        
        try:
            motor_number = int(args[0])
            if motor_number not in (1, 2):
                raise ValueError("Motor number must be 1 or 2")
        except ValueError:
            raise ValueError("Motor number must be an integer (1 or 2)")
        
        rotation = args[1].lower()
        if rotation not in ("cw", "ccw"):
            raise ValueError("Rotation must be 'cw' or 'ccw'")
        
        try:
            speed = int(args[2])
            if not (0 <= speed <= 100):
                raise ValueError("Speed must be between 0 and 100")
        except ValueError:
            raise ValueError("Speed must be an integer between 0 and 100")
        
        return False, motor_number, rotation, speed

    def execute_motor_command(self, args, dry_run=False):
        if settings.motorEnabled:
            init_motor, motor_number, rotation, speed = self.validate_motor_command_args(args)
        else:
            return "Motor module is disabled"
        
        if dry_run:
            return True
        else:
            if init_motor:
                self.sequence_handler.motor_handler.initMotorLimits()
                return "Initializing motor limits"
            else:
                self.start(motor_number, rotation, speed)
                return f"Motor {motor_number} started {rotation} at speed {speed}"

    def start(self, motor_number, rotation="cw", speed=100):
        logger.debug(f"motor {motor_number} start with rotation {rotation} and speed {speed}")

        # Crash prevention
        if (rotation == "cw" and self.mygpio_handler.GPIOMap[f"In_Motor{motor_number}LimitCW"] == self.GPIO.HIGH) or (rotation == "ccw" and self.mygpio_handler.GPIOMap[f"In_Motor{motor_number}LimitCCW"] == self.GPIO.HIGH):
            logger.warning("Start command aborted to prevent motor crash")
            return

        if rotation == "cw":
            self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motor_number}In1"], self.GPIO.HIGH)
            self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motor_number}In2"], self.GPIO.LOW)
        else:
            self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motor_number}In1"], self.GPIO.LOW)
            self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motor_number}In2"], self.GPIO.HIGH)

        if motor_number == 1:
            self.pwm_motor1.set_duty_cycle(speed)
        elif motor_number == 2:
            self.pwm_motor2.set_duty_cycle(speed)

    def stop(self, motor_number):
        logger.debug(f"motor {motor_number} stopping")
        self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motor_number}In1"], self.GPIO.LOW)
        self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motor_number}In2"], self.GPIO.LOW)
        self.GPIO.output(self.mygpio_handler.GPIOMap[f"Motor{motor_number}PWM"], self.GPIO.LOW)

    def limitTouch(self, channel, event=None):
        time.sleep(settings.bouncingTreshold + 0.23)  # avoid catching a bouncing
        if self.GPIO.input(channel) != 1:
            return

        GPIOLabel = self.mygpio_handler.getGPIOLabel(channel)
        logger.debug(f"Limit touched on channel {GPIOLabel}")
        motor_number = 1 if channel in (self.mygpio_handler.GPIOMap["In_Motor1LimitCCW"], self.mygpio_handler.GPIOMap["In_Motor1LimitCW"]) else 2
        self.stop(motor_number)

        if channel == self.mygpio_handler.GPIOMap[f"In_Motor{motor_number}LimitCCW"]:
            time.sleep(0.2)
            self.start(motor_number, "cw", speed=100)
        elif event is not None:
            self.start(motor_number, "ccw", speed=85)
            time.sleep(3)
            self.stop(motor_number)
            logger.debug("Event set")
            event.set()

    def reset(self, motor_number):
        pos = ""
        if self.GPIO.input(self.mygpio_handler.GPIOMap[f"In_Motor{motor_number}LimitCW"]) == self.GPIO.HIGH:
            pos = "CW limit touch"
            logger.debug(f"Motor {motor_number} position is {pos}. Short CCW and then CW.")
            self.start(motor_number, "ccw", 100)
            time.sleep(0.5)
            return
        elif self.GPIO.input(self.mygpio_handler.GPIOMap[f"In_Motor{motor_number}LimitCCW"]) == self.GPIO.HIGH:
            pos = "CCW limit touch"
        else:
            pos = "floating"
        logger.debug(f"Motor {motor_number} position is {pos}. Reaching CW limit.")
        self.start(motor_number, "cw", 100)

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
