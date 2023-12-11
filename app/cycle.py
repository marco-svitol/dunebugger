#!/usr/bin/env python3
# coding: utf8
import os, time, RPi.GPIO as GPIO, serial, random, vlc, subprocess, InTime
from datetime import datetime
from gpio_handler import mygpio_handler
import motor
from dunebuggerlogging import logger 

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
    args = ['python','./dimmer1.py','0x27',str(channel),str(level),str(speed)]
    subprocess.Popen(args)

def RPiwrite(gpio,bit):
    bit = not bit
    GPIO.output(mygpio_handler.GPIOMap[gpio],bit)
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
    try:
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
            logger.info('Stopping music and sfx player')
            musiclistplayer.stop()
            sfxplayer.stop()
    except:
        logger.warning("vstopaudio exception, most probably sound was not even playing.")
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
    if channel==mygpio_handler.GPIOMap["I_ThreeStateLoop"]: #switching three state to 'loop' mode triggers this function
        logger.info("ThreeState switched to 'loop' mode on channel"+str(channel))
    else:
        logger.info("Start button pressed on channel "+str(channel)) #if function is triggered from button then check three state mode
        if GPIO.input(mygpio_handler.GPIOMap["I_ThreeStateSingle"])==1 or ignoreThreeStateSingle :
            logger.debug ("Three state switch on 'single' mode")
        else:
            logger.debug ("Three state switch on 'off' mode: not playing")
            return

    if testdunebuggger:
        #Test relè
        #RPiwrite("DimGiorno",1)
        waituntil(3)
        motor.start(1,"ccw",30)
        waituntil(10)
        motor.stop(1)
        waituntil(20)
        motor.start(1,"cw",100)
        waituntil(30)
        motor.stop(1)
        cycleoffset = 0
        return
        t = 0
        vplaysfx(easteregg)
        musicplayer.audio_set_channel(1)
        vplaysfx(easteregg)
        musicplayer.audio_set_channel(2)
        vplaysfx(easteregg)
        musicplayer.audio_set_channel(3)
        for k in mygpio_handler.GPIOMap.keys():
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
        for k in mygpio_handler.GPIOMap.keys():
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
        logger.debug("MusicVolume: "+str(musicVolume)+" SfxVolume: "+str(sfxVolume))
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
        musicplayer.audio_set_channel(1)
        if eastereggEnabled:
            time.sleep(1)
            if GPIO.input(channel) == 1:
                vplaymusic(True)
            else:
                vplaymusic(False)
        else:
            logger.debug("Playing music...")
            vplaymusic(False)
        #musicplayer.audio_set_channel(1)
        musicplayer.audio_set_volume(normalMusicVolume)
        sfxplayer.audio_set_volume(normalSfxVolume)

        #primo ciclo: notte 
        vplaysfx(sfxfile)
        RPiwrite("Fontane",1)
        RPiwrite("LuceSopraNat",1)
        RPiwrite("FarettoVolta",1)
        RPiwrite("Fuochi",1)
        RPiwrite("LedFontana",1)
        waituntil(103)
        RPiwrite("LuciChiesa",0)
        RPiwrite("Case1", 1)
        waituntil(105)
        RPiwrite("Case2",1)
        waituntil(116)
        RPiwrite("DimAlba",1)
        waituntil(158)
        RPiwrite("DimAlba",0)
        RPiwrite("DimGiorno",1)
        RPiwrite("DimTramonto",1)
        waituntil(170)
        RPiwrite("Case2",0)
        waituntil(173)
        RPiwrite("Case1",0)
        waituntil(182)
        RPiwrite("DimGiorno",0)
        RPiwrite("LedFontana",0)
        waituntil(192)
        RPiwrite("DimTramonto",0)
        RPiwrite("FarettoVolta",0)
        waituntil(199)
        RPiwrite("Case1",1)
        waituntil(203)
        RPiwrite("Case2",1)
        waituntil(210)
        RPiwrite("FarettoVolta",1)
        waituntil(213)
        RPiwrite("LedFontana",1)
        
        #secondo ciclo
        waituntil(225)
        RPiwrite("DimAlba",1)
        waituntil(240)
        RPiwrite("Fuochi",0)
        waituntil(250)
        RPiwrite("DimGiorno",1)
        RPiwrite("Case2",0)
        waituntil(260)
        RPiwrite("DimTramonto",1)
        RPiwrite("Case1",0)
        waituntil(290)
        RPiwrite("DimAlba",0)
        RPiwrite("DimGiorno",0)
        waituntil(320)
        RPiwrite("LedFontana",0)
        RPiwrite("DimTramonto",0)
        waituntil(331)
        RPiwrite("FarettoVolta",0)
        waituntil(338)
        RPiwrite("Fuochi",1)
        waituntil(347)
        #RPiwrite("Case3",1)
        waituntil(359)
        RPiwrite("Case2",1)
        waituntil(367)
        RPiwrite("Case1",1)
        waituntil(377)
        RPiwrite("FarettoVolta",1)
        waituntil(383)
        RPiwrite("LedFontana",1)
        RPiwrite("Fuochi",1)
        waituntil(390)

        RPiwrite("Case2",0)
        RPiwrite("Fontane",0)
        waituntil(399)
        vstopaudio()
        RPiwrite("Case1",0)
        waituntil(403)
        RPiwrite("LedFontana",0)
        #RPiwrite("Case3",0)
        waituntil(409)
        RPiwrite("FarettoVolta",0)
        cycleoffset = 0
        if GPIO.input(mygpio_handler.GPIOMap["I_ThreeStateLoop"])!=1 :
            break # only reason to stay in the loop is that gpio
        else:
            time.sleep(2) # pause between cycles in loop mode

    logger.info("\nDunebugger listening. Press enter to quit\n")

try:
    # logging.config.fileConfig('./dunebuggerlogging.conf') #load logging config file
    # logger = logging.getLogger('dunebuggerLog')
    logger.info('DuneBugger started')        
    if os.path.exists('/dev/ttyUSB0') :                 # Arduino communication over serial port
        Arduino = serial.Serial('/dev/ttyUSB0',9600)
        logger.info('Arduino  : found device on /dev/ttyUSB0 and connected')
    else :
        Arduino = False
        logger.critical('Arduino  : serial port on /dev/ttyUSB0 not available: no com with Arduino')
    
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
    musicpath = "./music/"
    sfxpath = "./sfx/"
    sfxfile = "2009.mp3"
    easteregg = "ohhche.mp3"
    entrysong = "fincosong2022.mp3"
    sfxuccelli = "allodole.mp3"

    cyclespeed = 1#0.2
    ignoreThreeStateSingle = True
    ignoreQuietTime = True
    eastereggEnabled = False
    cycleoffset = 0

    testdunebuggger = True

    GPIO.add_event_detect(mygpio_handler.GPIOMap["I_StartButton"],GPIO.RISING,callback=cycle,bouncetime=5)

    GPIO.add_event_detect(mygpio_handler.GPIOMap["Motor1LimitLeft"],GPIO.RISING,callback=motor.limitTouch(),bouncetime=100)

    #GPIO.add_event_detect(mygpio_handler["ThreeStateLoop"],GPIO.RISING,callback=cycle,bouncetime=5)
    logger.info ("GPIO     : Callback function 'cycle' binded to event detection on GPIO "+str(mygpio_handler.GPIOMap["I_StartButton"]))
        
    input("\nDunebugger listening. Press enter to quit\n")

except KeyboardInterrupt:
    logger.debug ("stopped through keyboard")
	
except Exception as exc:
    logger.critical ("Exception: "+str(exc)+". Exiting." )

finally:
    logger.info ("GPIO     : removing interrupt on GPIO "+str(mygpio_handler.GPIOMap["I_StartButton"])+" and cleaning up GPIOs")
    GPIO.remove_event_detect(mygpio_handler.GPIOMap["I_StartButton"])
    mygpio_handler.cleanup()
    vstopaudio()

#NICETOHAVE:
#timing random con range di variabilità da aggiungere a funzione sleep
#cicli multipli scelta random
#WEBGUI -> velocità + contatori + calendario/orari messe + programciclo...
#Modalità riposo=notte -> attivazioni random luci/pompe
