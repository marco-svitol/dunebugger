import RPi.GPIO as GPIO          
from time import sleep

in1 = 1
in2 = 23
en = 18
temp1=1

GPIO.setmode(GPIO.BCM)
GPIO.setup(in1,GPIO.OUT)
GPIO.setup(in2,GPIO.OUT)
GPIO.setup(en,GPIO.OUT)
GPIO.output(in1,GPIO.LOW)
GPIO.output(in2,GPIO.LOW)
p=GPIO.PWM(en,5000)
p.start(25)
print("\n")
print("The default speed & direction of motor is LOW & Forward.....")
print("r-run s-stop f-forward b-backward l-low m-medium h-high e-exit")
print("\n")    

#while(1):
def motortest(x):
    #x=input()
    print("motortest func in")
    p.ChangeDutyCycle(100)
    global in1, in2, en, temp1

    if x=='r':
        print("run")
        if(temp1==1):
         GPIO.output(in1,GPIO.HIGH)
         GPIO.output(in2,GPIO.LOW)
         print("forward")
         x='z'
        else:
         GPIO.output(in1,GPIO.LOW)
         GPIO.output(in2,GPIO.HIGH)
         print("backward")
         x='z'


    elif x=='s':
        print("stop")
        GPIO.output(in1,GPIO.LOW)
        GPIO.output(in2,GPIO.LOW)
        x='z'

    elif x=='f':
        print("forward")
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        temp1=1
        x='z'

    elif x=='b':
        print("backward")
        GPIO.output(in1,GPIO.LOW)
        GPIO.output(in2,GPIO.HIGH)
        temp1=0
        x='z'

    elif x=='l':
        print("low")
        p.ChangeDutyCycle(25)
        x='z'

    elif x=='m':
        print("medium")
        p.ChangeDutyCycle(35)
        x='z'

    elif x=='h':
        print("high")
        p.ChangeDutyCycle(100)
        x='z'
     
    
    elif x=='e':
        GPIO.cleanup()
        #break
    
    else:
        print("<<<  wrong data  >>>")
        print("please enter the defined data to continue.....")

#Mapping GPIO Names
chan_I2C   = [2,3]
chan_releA = [5,11,9,10,22,27,17,4]
chan_releB = [21,20,16,12,7,8,25,24]

chan_contr = [6,13,19]
chan_ArduinoReset = [14]
chan_ResetDimmer = [15]

chan_motor_1 = [18,1,23]

GPIOMapPhysical={
        "SDA1":chan_I2C[0],
        "SCL1":chan_I2C[1],
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
        "Dimmer1Reset":chan_ResetDimmer[0],
        "ArduinoReset":chan_ArduinoReset[0],
        "StartButton":chan_contr[0],
        "ThreeStateSingle":chan_contr[1],
        "ThreeStateLoop":chan_contr[2],
        "Motor1PWM":chan_motor_1[0],
        "Motor1In1":chan_motor_1[1],
        "Motor1In2":chan_motor_1[2]
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
        "ResetDimmer":GPIOMapPhysical["Dimmer1Reset"],
        "ArduinoReset":GPIOMapPhysical["ArduinoReset"],
        "I_ThreeStateSingle":GPIOMapPhysical["ThreeStateSingle"],
        "I_ThreeStateLoop":GPIOMapPhysical["ThreeStateLoop"],
        "Motor1PWM":GPIOMapPhysical["Motor1PWM"],
        "Motor1In1":GPIOMapPhysical["Motor1In1"],
        "Motor1In2":GPIOMapPhysical["Motor1In2"]
        }

GPIO.add_event_detect(GPIOMap["I_StartButton"],GPIO.RISING,callback=motortest("r"),bouncetime=5)