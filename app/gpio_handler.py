import RPi.GPIO as GPIO
from dunebuggerlogging import logger
import time
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

# Dimmer su rele4 va fatto diventare relè 12V?
# DimIngresso dimmerabili?
# Natività alwayson very little led
# Led Always on sotto le panche
# StellaCometa: vuole un alimentazionee e un relè per comando inserito/disinserito. Nel 2019 avviavamo a 1 e dopo 20 sec a 0
# Musica sempre soft all'avvio?, poi random?
#
# Quindi alwayson:
#   Stereo
#   Insegna
#   Luce Nat piccola
#   Led sotto le panche
#  
# alternative: 
#   insegna non sotto centralina
#   dimingresso non dimmerabie, va sotto relè
#   luce/i ombre non relè ma dimmer o 220 invece di 12/5 v...
#
# emergenze:
#   non funziona questione piatti:
#       luci ombre on/off senza rotazione, tieni spento circuito motori
#  
class GPIOHandler:
    chan_releA = [5, 11, 9, 10, 22, 27, 17, 4]
    chan_releB = [21, 20, 16, 12, 7, 8, 25, 24]
    chan_contr = [6]

    chan_motor_1 = [18, 1, 23]
    chan_motor_2 = [13, 3, 2]
    chan_limitswitch_motor1 = [0,26]
    chan_limitswitch_motor2 = [14,15]

    GPIOMapPhysical={
            "Dimmer6":chan_releA[0],
            "Dimmer5":chan_releA[1],
            "Dimmer4":chan_releA[2],
            "Dimmer3":chan_releA[3],
            "Rele5":chan_releA[4],
            "Rele6":chan_releA[5],
            "Rele7":chan_releA[6],
            "Rele8":chan_releA[7],
            "Rele9":chan_releB[0],
            "Rele10":chan_releB[1],
            "Rele11":chan_releB[2],
            "Rele12":chan_releB[3],
            "Rele13":chan_releB[4],
            "Rele14":chan_releB[5],
            "Rele15":chan_releB[6],
            "Rele16":chan_releB[7],
            "StartButton":chan_contr[0],
            "Motor1PWM":chan_motor_1[0],
            "Motor1In1":chan_motor_1[1],
            "Motor1In2":chan_motor_1[2],
            "Motor1LimitA":chan_limitswitch_motor1[0],
            "Motor1LimitB":chan_limitswitch_motor1[1],
            "Motor2PWM":chan_motor_2[0],
            "Motor2In1":chan_motor_2[1],
            "Motor2In2":chan_motor_2[2],
            "Motor2LimitA":chan_limitswitch_motor2[0],
            "Motor2LimitB":chan_limitswitch_motor2[1],
            }
    GPIOMap={
            "DimIngressoOvest":GPIOMapPhysical["Dimmer6"],
            "DimIngressoEst":GPIOMapPhysical["Dimmer5"],
            "DimTramonto":GPIOMapPhysical["Dimmer4"],
            "DimGiorno":GPIOMapPhysical["Dimmer3"],
            "Ombre2":GPIOMapPhysical["Rele5"],
            "Accensione":GPIOMapPhysical["Rele6"],
            "SchedaMotori":GPIOMapPhysical["Rele7"],
            "Ombre1":GPIOMapPhysical["Rele8"],
            "Case1":GPIOMapPhysical["Rele9"],
            "Case2":GPIOMapPhysical["Rele10"],
            "Case3":GPIOMapPhysical["Rele11"],
            "Fuochi1":GPIOMapPhysical["Rele12"],
            "LuceNativita":GPIOMapPhysical["Rele13"],
            "PompaAcqua":GPIOMapPhysical["Rele14"],
            "Fuochi2":GPIOMapPhysical["Rele15"],
            "AlwaysOn":GPIOMapPhysical["Rele16"],
            "I_StartButton":GPIOMapPhysical["StartButton"],
            "Motor1PWM":GPIOMapPhysical["Motor1PWM"],
            "Motor1In1":GPIOMapPhysical["Motor1In1"],
            "Motor1In2":GPIOMapPhysical["Motor1In2"],
            "Motor1LimitCCW":GPIOMapPhysical["Motor1LimitA"],
            "Motor1LimitCW":GPIOMapPhysical["Motor1LimitB"],
            "Motor2PWM":GPIOMapPhysical["Motor2PWM"],
            "Motor2In1":GPIOMapPhysical["Motor2In1"],
            "Motor2In2":GPIOMapPhysical["Motor2In2"],
            "Motor2LimitCCW":GPIOMapPhysical["Motor2LimitA"],
            "Motor2LimitCW":GPIOMapPhysical["Motor2LimitB"],
            }

    def __init__(self):
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
    #logger.debug("Toggled RPi "+gpio+" to "+str(GPIO.input(mygpio_handler.GPIOMap[gpio])))

mygpio_handler = GPIOHandler()

class DebouncedButton:
    def __init__(self, name, channel, debounce_interval=0.2, callback_function=None, callback_event=None):
        
        # Set the GPIO mode and pin
        GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # Initialize variables
        self.name = name
        self.channel = channel
        self.button_state = GPIO.input(channel)
        self.last_button_state = self.button_state
        self.last_change_time = time.time()
        self.debounce_interval = debounce_interval
        self.callback_function = callback_function
        self.callback_event = callback_event

        # Set up event detection on the button pin
        GPIO.add_event_detect(channel, GPIO.RISING , callback=self.button_callback)

    def button_callback(self, channel):
        # Read the current state of the button
        self.button_state = GPIO.input(self.channel)

        # Check if the button state has changed
        if self.button_state != self.last_button_state:
            self.last_change_time = time.time()

        # Check if the button state has been stable for the debounce interval
        if time.time() - self.last_change_time > self.debounce_interval:
            # Call the provided callback function or perform a default action
            logger.debug("Button "+self.name+" state changed to "+str(self.button_state))
            if self.callback_function:
                self.callback_function(self.channel, self.callback_event)
            else:
                logger.error("No callback_function provided to button "+self.name)

        # Update the last button state
        self.last_button_state = self.button_state

    def cleanup(self):
        # Clean up GPIO when done
        GPIO.cleanup()