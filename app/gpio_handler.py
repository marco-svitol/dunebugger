import RPi.GPIO as GPIO



from dunebuggerlogging import logger 

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
            "Dimmer2":chan_releA[4],
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
            "DimChiesa":GPIOMapPhysical["Dimmer3"],
            "DimAlba":GPIOMapPhysical["Dimmer4"],
            "DimTramonto":GPIOMapPhysical["Dimmer2"],
            "DimGiorno":GPIOMapPhysical["Dimmer6"],
            "Accensione":GPIOMapPhysical["Rele6"],
            "AmpliWood":GPIOMapPhysical["Rele7"],
            "Fontane":GPIOMapPhysical["Rele8"],
            "Case1":GPIOMapPhysical["Rele9"],
            "Case2":GPIOMapPhysical["Rele10"],
            "LuceBosco":GPIOMapPhysical["Rele11"],
            "LuceSopraNat":GPIOMapPhysical["Rele12"],
            "FarettoVolta":GPIOMapPhysical["Rele13"],
            "LuciChiesa":GPIOMapPhysical["Rele14"],
            "Fuochi":GPIOMapPhysical["Rele15"],
            "LedFontana":GPIOMapPhysical["Rele16"],
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
            logger.debug(str(value)+" == "+str(GPIONum))
            if value == GPIONum:
                return key
            # Return None if the value is not found
            return "_not_found_"

mygpio_handler = GPIOHandler()
