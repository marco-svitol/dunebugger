from utils import waituntil
from audio_handler import audioPlayer
from gpio_handler import RPiwrite, RPiToggle
import random
from dunebugger_settings import settings
import motor

def setStandBy():
    RPiwrite("SchedaMotori",1)
    RPiwrite("DimGiorno",1)
    #RPiwrite("LuceNativita",1)
    RPiwrite("LuceStartButton",1)
    RPiwrite("AlwaysOnNativita",1)
    RPiwrite("DimIngressoEst",1)
    RPiwrite("DimIngressoOvest",1)
    RPiwrite("Case1",1)
    RPiwrite("Case2",1)
    RPiwrite("Fuochi1",1)
    
    
def testCommands():
    RPiwrite("Luce_StartButton",0)
    RPiwrite("Calice",0)
    RPiwrite("LuceNativita",0)
    RPiwrite("DimIngressoEst",0)
    waituntil(12)
    if settings.motor1Enabled:
        motor.start(1,"ccw",90)
    waituntil(13)
    RPiwrite("Ombre1",1)
    waituntil(39)
    if settings.motor2Enabled:
        motor.start(2,"ccw",85)
    waituntil(41)
    RPiwrite("Ombre2",1)
    waituntil(42)
    RPiwrite("Ombre1",0)
    waituntil(70)
    RPiwrite("Ombre2",0)
    waituntil(73)
    RPiwrite("LuceNativita",1)
    waituntil(75)
    RPiwrite("Calice",1)
    waituntil(100)
    #RPiwrite("DimIngressoEst",1)
    audioPlayer.vstopaudio()
    RPiwrite("Luce_StartButton",1)


def sequence():
    RPiwrite("LuceStartButton",0)
    RPiwrite("PompaAcqua",1)
    RPiwrite("DimTramonto",1)
    RPiwrite("DimIngressoEst",0)
    RPiwrite("DimGiorno",0)
    waituntil(10)
    RPiwrite("Case1",0)
    waituntil(17)
    RPiwrite("Case2",0)
    RPiwrite("Fuochi1",0) 
    RPiwrite("DimTramonto",0)
    waituntil(30)
    shadows(settings.cycleoffset) #duration 45
    RPiwrite("Fuochi1",1)
    waituntil(82)
    RPiwrite("LuceNativita",1)
    waituntil(85)
    RPiwrite("Cometa",1)
    RPiwrite("Calice",1)
    waituntil(110)
    RPiwrite("Calice",0)
    waituntil(145)
    RPiwrite("Cometa",0)
    RPiwrite("LuceNativita",0)
    shadows(settings.cycleoffset, True) #duration 45
    RPiwrite("DimGiorno",1)
    RPiwrite("DimTramonto",1)
    RPiwrite("Case1",1)
    RPiwrite("LuceNativita",1)
    waituntil(207)
    RPiwrite("Case2",1)
    waituntil(215)
    RPiwrite("DimIngressoEst",1)
    RPiwrite("Case2",0)
    RPiwrite("DimTramonto",0)
    waituntil(220)
    RPiwrite("PompaAcqua",0)
    RPiwrite("Case1",0)
    waituntil(225)
    RPiwrite("Fuochi1",0)
    audioPlayer.vstopaudio()
    waituntil(237)
    RPiwrite("LuceNativita",0)
    audioPlayer.vstopaudio()
    RPiwrite("Accensione",1)

def shadows(starttime, caliceoff = False):
    motor.start(1,"ccw",92)
    waituntil(starttime+1)
    RPiwrite("Ombre1",1)
    waituntil(starttime+4)
    if caliceoff:
        RPiwrite("Calice",0)
    waituntil(starttime+21)
    motor.start(2,"ccw",85)
    waituntil(starttime+22)
    RPiwrite("Ombre2",1)
    waituntil(starttime+23)
    RPiwrite("Ombre1",0)
    waituntil(starttime+45)
    RPiwrite("Ombre2",0)

def random_sequence(event):
    randomizable = ["Case1","Case2","Fuochi1"]
    rand_elem = random.choice(randomizable)
    RPiToggle(rand_elem)