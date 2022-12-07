#!/usr/bin/env python3
# coding: utf8
import os, time, RPi.GPIO as GPIO, serial, random, vlc, subprocess, logging, logging.config, InTime
from datetime import datetime

#Functions definition:

def ArduinoSend(command):
    global Arduino    
    ccommand = command.replace("\n","")
    if Arduino != False:
        Arduino.write(bytes(command,'UTF-8'))
        logger.debug("Sending command "+ccommand+" to Arduino")
    else:
        ccommand = command.replace("\n","")
        logger.warning("ignoring command "+ccommand+" to Arduino")

def dimmer1(channel, level, speed):
    args = ['python','/home/pi/dunebugger/dimmer1.py','0x27',str(channel),str(level),str(speed)]
    subprocess.Popen(args)

def RPiwrite(gpio,bit):
    bit = not bit
    GPIO.output(GPIOMap[gpio],bit)
    logger.debug("RPi "+gpio+" write "+str(bit))

def waituntil(sec):
    global cyclespeed
    global cycleoffset
    logger.debug("Waiting: "+str(sec-cycleoffset))
    time.sleep((sec-cycleoffset) * cyclespeed)
    cycleoffset = sec

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>      Music section     <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
def vplaymusic(customsong):
    global musicplayer
    playlist = vlcinstance.media_list_new()

    fileplaylist = os.listdir(musicpath) #get filenames
    logger.info("Music: read " + str(len(fileplaylist)) + " files from folder " + musicpath)

    for mfile in fileplaylist: #keep only if extension is valid audio file
        if not checkaudioext(mfile):
            fileplaylist.remove(mfile)

    random.shuffle(fileplaylist)  # shuffle list
	
    if len(fileplaylist) > 20:
        fileplaylist = fileplaylist[:19]  # get only first 20 songs

    #Velasquez 2022 Finco entry song
    playlist.add_media(vlcinstance.media_new(sfxpath + entrysong))    

    if customsong: #eastereggg
        logger.info("EasterEgg enabled!!")
        playlist.add_media(vlcinstance.media_new(sfxpath + easteregg))
        playlist.add_media(vlcinstance.media_new(sfxpath + "A.mp3"))

    for song in range(len(fileplaylist)):  # add path to songname
        playlist.add_media(vlcinstance.media_new(musicpath + fileplaylist[song]))

    musiclistplayer.set_media_list(playlist)

    musiclistplayer.set_playback_mode(vlc.PlaybackMode.loop)
    musiclistplayer.play()

    musicplayer = musiclistplayer.get_media_player()
    time.sleep(0.1)
    logger.info("Setting music volume at "+str(musicVolume))
    musicplayer.audio_set_volume(musicVolume)

    logger.info("Playing music (first three songs): " + fileplaylist[0] + " " + fileplaylist[1] + " " + fileplaylist[2])

def vplaysfx(filename):
    media = vlcinstance.media_new(sfxpath + filename)

    sfxplayer.set_media(media)
    logger.info("Setting sfx volume at "+str(sfxVolume))
    sfxplayer.audio_set_volume(sfxVolume)

    sfxplayer.play()
    logger.info("Playing sfx :" + sfxpath + filename)

def checkaudioext(filename):
    audioext = ['AAC', 'AC3', 'AIFF', 'AMR', 'AU', 'FLAC', 'M4A', 'MIDI', 'MKA', 'MP3', 'OGA', 'RA', 'VOC', 'WAV', 'WMA']
    if filename[-3:].upper() in audioext:
        return True
    return False

def vstopaudio():
    if musicVolume >0 or sfxVolume > 0:
        if musicVolume > sfxVolume: # calculate pause interval. Takes higher volume
            fadeoutpause = fadeoutsec / (musicVolume * 1.0)
        else:
            fadeoutpause = fadeoutsec / (sfxVolume * 1.0)

        logger.info("Fading out in " + str(fadeoutsec) + " seconds")

        mvol = musicVolume
        svol = sfxVolume

        while (mvol>0 or svol > 0):
            if musicplayer is not None and mvol > 0: mvol-=1; musicplayer.audio_set_volume(mvol)
            if sfxplayer is not None and svol > 0: svol-=1; sfxplayer.audio_set_volume(svol)
            print ('.',end="",flush=True)
            time.sleep(fadeoutpause)

    try:
        logger.info("")
        logger.info('Stopping music and sfx player')
        musiclistplayer.stop()
        sfxplayer.stop()
    except:
        return
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   end music section    <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<




#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Main sequence >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def cycletest(channel):
    print("button pressed")
    dimmer1(1,100,10)
	
def cycle(channel):
    global musicVolume
    global sfxVolume
    global cycleoffset

    time.sleep(0.10)    # avoid catching a bouncing
    if GPIO.input(channel) != 1:
        #logger.debug ("Bouncing: false interrupt on channel"+str(channel))
        return
    if channel==GPIOMap["I_ThreeStateLoop"]: #switching three state to 'loop' mode triggers this function
        logger.info("ThreeState switched to 'loop' mode on channel"+str(channel))
    else:
        logger.info("Start button pressed on channel "+str(channel)) #if function is triggered from button then check three state mode
        if GPIO.input(GPIOMap["I_ThreeStateSingle"])==1 or ignoreThreeStateSingle :
            logger.debug ("Three state switch on 'single' mode")
        else:
            logger.debug ("Three state switch on 'off' mode: not playing")
            return

    if testdunebuggger:
        #Test relè
        RPiwrite("DimGiorno",1)
        return
        t = 0
        vplaysfx(easteregg)
        musicplayer.audio_set_channel(1)
        vplaysfx(easteregg)
        musicplayer.audio_set_channel(2)
        vplaysfx(easteregg)
        musicplayer.audio_set_channel(3)
        for k in GPIOMap.keys():
            if not k.startswith('Dim') and not k.startswith('I_'):
                logger.info ("GPIO"+str(k))
                waituntil(t)
                RPiwrite(k,1)
                t+=5
                waituntil(t)
                RPiwrite(k,0)
                t+=1
        #Test dimmer
        vplaysfx(sfxuccelli)
        t+=5
        vplaymusic(False)
        for k in GPIOMap.keys():
            if k.startswith('Dim') and not k.startswith('I_'):
                logger.info ("GPIO"+str(k))
                waituntil(t)
                RPiwrite(k,1)
                t+=30
                waituntil(t)
                RPiwrite(k,0)
                t+=2
        cycleoffset = 0
        vstopaudio()
        return


    while True:

        #ArduinoDimmerStart()
        ##ArduinoSend(Ch1Rst)
        ##ArduinoSend(Ch1FIn)
        #check current date against calendar delle messe per impostare volume
        
        musicVolume = normalMusicVolume
        sfxVolume = normalSfxVolume
        if not ignoreQuietTime:
            if not isinstance(InTime.getNTPTime(),int): #time not synced
                musicVolume = quietMusicVol
                sfxVolume = quietSfxVol
                logger.info("Orario non sincronizzato: vol musica="+str(musicVolume)+" vol sfx="+str(sfxVolume))
            elif InTime.duranteCelebrazioni(datetime.now(),cyclelength):
                musicVolume = quietMusicVol
                sfxVolume = quietSfxVol
                logger.info("Siamo durante una celebrazione: vol music="+str(musicVolume)+" vol sfx="+str(sfxVolume))
        
        # Lista di (Time,Action) - ordina la lista - eseguo una runpending() che scansiona la lista ed esegue action
	#0 sec

        # RPiwrite("ResetDimmer",1)
        # time.sleep(2)
        # RPiwrite("ArduinoReset",1)
        # time.sleep(0.3)
        # RPiwrite("ArduinoReset",0)
        #musicplayer.audio_set_channel(2)
        if eastereggEnabled:
            time.sleep(1)
            if GPIO.input(channel) == 1:
                vplaymusic(True)
            else:
                vplaymusic(False)
        else:
            vplaymusic(False)
        
        RPiwrite("LuceSopraNat",0)
        RPiwrite("Fuochi",0)
        waituntil(2) #
        RPiwrite("LuceBosco",1)
        waituntil(15)
        vplaysfx(sfxuccelli)
        waituntil(70) #durata strofa bosco
        #musicplayer.audio_set_channel(3)
        RPiwrite("LuciChiesa",1)
        RPiwrite("LuceBosco",0)
        waituntil(100)	

        #Natività
        #musicplayer.audio_set_channel(1)
        vplaysfx(sfxfile)
        RPiwrite("Fontane",1)
        waituntil(103)
        RPiwrite("LuceSopraNat",1)
        waituntil(106)
        RPiwrite("FarettoVolta",1)
        waituntil(108)
        RPiwrite("Case1", 1)
        waituntil(110)
        RPiwrite("Case2",1)
        waituntil(114)
        RPiwrite("Fuochi",1)
        waituntil(116)
        #RPiwrite("Case3",1)
        waituntil(125)
        RPiwrite("DimAlba",1)
        waituntil(140)
        RPiwrite("Fuochi",0)
        waituntil(145)
        #RPiwrite("Case3",0)
        waituntil(150)
        RPiwrite("DimGiorno",1)
        RPiwrite("Case2",0)
        waituntil(160)
        RPiwrite("DimTramonto",1)
        RPiwrite("Case1",0)
        waituntil(230)
        RPiwrite("DimAlba",0)
        RPiwrite("DimGiorno",0)
        waituntil(303)
        RPiwrite("DimTramonto",0)
        waituntil(321)
        RPiwrite("FarettoVolta",0)
        waituntil(348)
        RPiwrite("Fuochi",1)
        waituntil(367)
        #RPiwrite("Case3",1)
        waituntil(379)
        RPiwrite("Case2",1)
        waituntil(383)
        RPiwrite("Case1",1)
        waituntil(407)
        RPiwrite("FarettoVolta",1)
        waituntil(453)
        RPiwrite("Fuochi,0")
        waituntil(480)
        RPiwrite("Case2",0)
        RPiwrite("Fontane",0)
        waituntil(487)
        vstopaudio()
        RPiwrite("Case1",0)
        waituntil(490)
        #RPiwrite("Case3",0)
        waituntil(495)
        RPiwrite("FarettoVolta",0)
        cycleoffset = 0
        if GPIO.input(GPIOMap["I_ThreeStateLoop"])!=1 :
            break # only reason to stay in the loop is that gpio
        else:
            time.sleep(2) # pause between cycles in loop mode

    logger.info("\nDunebugger listening. Press enter to quit\n")

try:
    logging.config.fileConfig('/home/pi/dunebugger/dunebuggerlogging.conf') #load logging config file
    logger = logging.getLogger('dunebuggerLog')
    logger.info('DuneBugger started')        
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    if os.path.exists('/dev/ttyUSB0') :                 # Arduino communication over serial port
        Arduino = serial.Serial('/dev/ttyUSB0',9600)
        logger.info('Arduino  : found device on /dev/ttyUSB0 and connected')
    else :
        Arduino = False
        logger.critical('Arduino  : serial port on /dev/ttyUSB0 not available: no com with Arduino')
    
    #Mapping GPIO Names
    chan_I2C   = [2,3]
    chan_releA = [5,11,9,10,22,27,17,4]
    chan_releB = [21,20,16,12,7,8,25,24]
    chan_contr = [6,13,19]
    chan_ArduinoReset = [14]
    chan_ResetDimmer = [15]
    
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
            "ThreeStateLoop":chan_contr[2]
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
            "FarettoBosco":GPIOMapPhysical["Rele16"],
            "I_StartButton":GPIOMapPhysical["StartButton"],
            "ResetDimmer":GPIOMapPhysical["Dimmer1Reset"],
            "ArduinoReset":GPIOMapPhysical["ArduinoReset"],
            "I_ThreeStateSingle":GPIOMapPhysical["ThreeStateSingle"],
            "I_ThreeStateLoop":GPIOMapPhysical["ThreeStateLoop"]
            }
    
    #Dimmer1 I2C - Light dimmering : 0 Fully open - 100 Fully closed
    Dimmer1Add = '0x27'
    Dimmer1Ch1 = '0x80'
    Dimmer1Ch2 = '0x81'
    Dimmer1Ch3 = '0x82'
    Dimmer1Ch4 = '0x83'
    
    #Dimmer2 Serial - Protocol commands
    Ch1Rst = "900\n"
    Ch1FIn = "i\n"
    Ch1FOu = "o\n"
	
    # set gpio modes
    GPIO.setup(chan_releA, GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(chan_releB, GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(chan_ArduinoReset, GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(chan_ResetDimmer, GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(chan_contr, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    logger.info ("GPIO     : initilized")
    
    # set initial state
    RPiwrite("LuceSopraNat",1)
    RPiwrite("AmpliWood",1)
    RPiwrite("Fuochi",1)
    RPiwrite("Accensione",1)
    #Music and sfx
    vlcinstance = vlc.Instance('--aout=alsa')
    musiclistplayer = vlcinstance.media_list_player_new()
    sfxplayer = vlcinstance.media_player_new()
    musicplayer = vlcinstance.media_player_new()

    normalMusicVolume = 95
    normalSfxVolume = 90
    musicVolume = normalMusicVolume
    sfxVolume = normalSfxVolume
    quietMusicVol = 95
    quietSfxVol = 90
    cyclelength = 372
	
    fadeoutsec = 8 #fade out seconds
    musicpath = "/home/pi/dunebugger/music/"
    sfxpath = "/home/pi/dunebugger/sfx/"
    sfxfile = "2009.mp3"
    easteregg = "ohhche.mp3"
    entrysong = "fincosong2022.wav"
    sfxuccelli = "allodole.m4a"

    cyclespeed = 1#0.2
    ignoreThreeStateSingle = True
    ignoreQuietTime = True
    eastereggEnabled = False
    cycleoffset = 0

    testdunebuggger = False

    GPIO.add_event_detect(GPIOMap["I_StartButton"],GPIO.RISING,callback=cycle,bouncetime=5)

    #GPIO.add_event_detect(GPIOMap["ThreeStateLoop"],GPIO.RISING,callback=cycle,bouncetime=5)
    logger.info ("GPIO     : Callback function 'cycle' binded to event detection on GPIO "+str(GPIOMap["I_StartButton"]))
        
    input("\nDunebugger listening. Press enter to quit\n")

except KeyboardInterrupt:
    logger.debug ("stopped through keyboard")
	
except Exception as exc:
    logger.critical ("Exception: "+str(exc)+". Exiting." )

finally:
    logger.info ("GPIO     : removing interrupt on GPIO "+str(GPIOMap["I_StartButton"])+" and cleaning up GPIOs")
    GPIO.remove_event_detect(GPIOMap["I_StartButton"])
    GPIO.cleanup()
    vstopaudio()

#NICETOHAVE:
#timing random con range di variabilità da aggiungere a funzione sleep
#cicli multipli scelta random
#WEBGUI -> velocità + contatori + calendario/orari messe + programciclo...
#Modalità riposo=notte -> attivazioni random luci/pompe
