import RPi.GPIO as GPIO
from dunebuggerlogging import logger
import configparser
from ast import literal_eval

#PWM 13,19,12,18 # free : 19
# 2,3 were used for Arduino serial (no rele). Two GPIOs were reserved for Arduino reset (14) relè and Dimmer board reset (15) relè

#     # Dimmer1 I2C - Light dimmering : 0 Fully open - 100 Fully closed
#     Dimmer1Add = '0x27'
#     Dimmer1Ch1 = '0x80'
#     Dimmer1Ch2 = '0x81'
#     Dimmer1Ch3 = '0x82'
#     Dimmer1Ch4 = '0x83'

#     # Dimmer2 Serial - Protocol commands
#     Ch1Rst = "900\n"
#     Ch1FIn = "i\n"
#     Ch1FOu = "o\n"

class GPIOHandler:
    def __init__(self):
        # Load GPIO configuration from gpio_config.conf
        self.load_gpio_configuration()

        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.chan_releA, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.chan_releB, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.chan_contr, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.chan_motor_1, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.chan_limitswitch_motor1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.chan_motor_2, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.chan_limitswitch_motor2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def load_gpio_configuration(self):
        config = configparser.ConfigParser()
        try:
            config.read('gpio_config.conf')

            # Load channels
            for attr in dir(self):
                if attr.startswith("chan_"):
                    setattr(self, attr, literal_eval(config.get('Channels', attr)))

            # Load GPIOMapPhysical
            for key in config.options('GPIOMapPhysical'):
                self.GPIOMapPhysical[key] = literal_eval(config.get('GPIOMapPhysical', key))

            # Load GPIOMap
            for key in config.options('GPIOMap'):
                self.GPIOMap[key] = literal_eval(config.get('GPIOMap', key))

            # Check if "I_StartButton" entry exists in GPIOMap
            if 'I_StartButton' not in self.GPIOMap:
                raise ValueError('GPIOMap must have an entry for "I_StartButton"')

        except (configparser.Error, ValueError) as e:
            print(f"Error reading GPIO configuration: {e}")
            # You might want to handle the error in an appropriate way, e.g., logging or quitting the program


    def cleanup(self):
        GPIO.cleanup()

    def getGPIOLabel(self,GPIONum):
        for key, value in self.GPIOMap.items():
            if value == GPIONum:
                return key
            # Return None if the value is not found
        return "_not_found_"
        
def RPiwrite(gpio,bit):
    logger.debug("RPi "+gpio+" write "+str(bit))
    bit = not bit
    GPIO.output(mygpio_handler.GPIOMap[gpio],bit)

def RPiToggle(gpio):
    GPIO.output(mygpio_handler.GPIOMap[gpio], not GPIO.input(mygpio_handler.GPIOMap[gpio]))
    #logger.verbose("Toggled RPi "+gpio+" to "+str(GPIO.input(mygpio_handler.GPIOMap[gpio])))

mygpio_handler = GPIOHandler()
