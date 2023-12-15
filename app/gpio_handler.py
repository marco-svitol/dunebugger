import RPi.GPIO as GPIO
from utils import RPiwrite, waituntil
import motor
from audio_handler import audioPlayer

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
            "DimIngresso":GPIOMapPhysical["Dimmer6"],
            "DimStandby":GPIOMapPhysical["Dimmer5"],
            "DimTramonto":GPIOMapPhysical["Dimmer4"],
            "DimGiorno":GPIOMapPhysical["Dimmer3"],
            "Ombra2":GPIOMapPhysical["Rele5"],
            "Accensione":GPIOMapPhysical["Rele6"],
            "SchedaMotori":GPIOMapPhysical["Rele7"],
            "Ombra1":GPIOMapPhysical["Rele8"],
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

    def setStandBy():
        RPiwrite("SchedaMotori",1)
        RPiwrite("LuceNativita",1)
        RPiwrite("Accensione",1)
        RPiwrite("AlwaysOn",1)
        RPiwrite("DimIngresso",1)
        RPiwrite("Case1",1)
        RPiwrite("Case2",1)
        RPiwrite("Case3",1)
        RPiwrite("Fuochi1",1)
        RPiwrite("Fuochi2",1)
        RPiwrite("DimStandby",1)

    def testCommands():
        waituntil(3)
        RPiwrite("Ombra1",1)
        #motor.start(1,"ccw",30)

    def sequence():
        waituntil(5)
        RPiwrite("DimIngresso",0)
        RPiwrite("PompaAcqua",1)
        waituntil(12)
        RPiwrite("Case1",0)
        waituntil(13)
        RPiwrite("Case2",0)
        waituntil(15)
        RPiwrite("Fuochi1",0)
        RPiwrite("DimStandby",0)
        waituntil(18)
        RPiwrite("Case3",0)
        waituntil(25)
        RPiwrite("Fuochi2",0)
        RPiwrite("LuceNativita",0)
        motor.start(1,"ccw",85)
        waituntil(26)
        RPiwrite("Ombre1",1)
        waituntil(47)
        motor.start(2,"ccw",85)
        waituntil(48)
        RPiwrite("Ombre2",1)
        waituntil(49)
        RPiwrite("Ombre1",0)
        waituntil(71)
        RPiwrite("Ombre2",0)
        RPiwrite("DimIngresso",1)
        waituntil(73)
        RPiwrite("LuceNativita",1)
        waituntil(75)
        RPiwrite("Fuochi1",1)
        RPiwrite("Case1",1)
        waituntil(78)
        RPiwrite("Case2",1)
        RPiwrite("Fuochi2",1)
        waituntil(81)
        RPiwrite("Case3",1)
        waituntil(100)
        RPiwrite("PompaAcqua",0)
        audioPlayer.vstopaudio()

mygpio_handler = GPIOHandler()
