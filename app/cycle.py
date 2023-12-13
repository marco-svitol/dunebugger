#!/usr/bin/env python3
# coding: utf8
import os, time, RPi.GPIO as GPIO, serial
from gpio_handler import mygpio_handler
import motor
from dunebuggerlogging import logger
import threading
from utils import RPiwrite, waituntil
from audio_handler import audioPlayer
from dunebugger_settings import settings

testdunebuggger = False

def cycle_trigger(channel):
    threading.Thread(name='_cycle_thread', target=cycle, args=(channel,)).start()

def cycle(channel):
    with settings.cycle_thread_lock:

        time.sleep(settings.bouncingTreshold)    # avoid catching a bouncing
        if GPIO.input(channel) != 1:
            logger.debug ("Warning! Below treshold of "+str(settings.bouncingTreshold)+" on channel"+str(channel))
            return
        
        logger.info("Start button pressed on channel "+str(channel)) #if function is triggered from button then check three state mode

        if testdunebuggger:
            waituntil(3)
            motor.start(1,"ccw",30)
            return
        
        audioPlayer.initMusic()
        logger.debug("Starting music")
        if settings.eastereggEnabled:
            time.sleep(1)
            if GPIO.input(channel) == 1:
                audioPlayer.vplaymusic(True)
            else:
                audioPlayer.vplaymusic(False)
        else:
            audioPlayer.vplaymusic(False)
        
        audioPlayer.musicSetVolume(audioPlayer.musicVolume)
        audioPlayer.sfxSetVolume(audioPlayer.sfxVolume)

        logger.debug("Starting SFX")
        audioPlayer.vplaysfx(audioPlayer.sfxfile)

#---------------- cycle
        RPiwrite("Fuochi",1)
        motor.start(1,"ccw",30)
        waituntil(150)
        audioPlayer.vstopaudio()
#--------------- end cycle

        settings.cycleoffset = 0
        logger.info("\nDunebugger listening. Press enter to quit\n")

def main():
    try:
        logger.info('DuneBugger started')        
        
        if (settings.ArduinoConnected):
            if os.path.exists('/dev/ttyUSB0') :                 # Arduino communication over serial port
                Arduino = serial.Serial('/dev/ttyUSB0',9600)
                logger.info('Arduino  : found device on /dev/ttyUSB0 and connected')
            else :
                Arduino = False
                logger.critical('Arduino  : serial port on /dev/ttyUSB0 not available: no com with Arduino')
        
        # set initial state
        RPiwrite("SchedaMotori",1)
        RPiwrite("Fuochi",1)
        RPiwrite("Accensione",1)

        motor_reset_event = threading.Event()
        # Add event detection for motor limit touch with functools.partial
        callback_with_params = lambda channel: motor.limitTouch(channel, motor_reset_event)
        motor_reset_thread = threading.Thread(target=motor.reset_motor_and_set_event, args=(motor_reset_event,1))
        motor_reset_event = threading.Event()
        GPIO.add_event_detect(mygpio_handler.GPIOMap["Motor1LimitCCW"],GPIO.RISING,callback=motor.limitTouch,bouncetime=200)
        GPIO.add_event_detect(mygpio_handler.GPIOMap["Motor1LimitCW"], GPIO.RISING, callback=callback_with_params, bouncetime=200)
        GPIO.add_event_detect(mygpio_handler.GPIOMap["Motor2LimitCCW"],GPIO.RISING,callback=motor.limitTouch,bouncetime=200)
        GPIO.add_event_detect(mygpio_handler.GPIOMap["Motor2LimitCW"],GPIO.RISING,callback=motor.limitTouch,bouncetime=200)
        motor_reset_thread.start()
        motor_reset_event.wait()
        #motor.reset(2)
        
        GPIO.add_event_detect(mygpio_handler.GPIOMap["I_StartButton"],GPIO.RISING,callback=cycle_trigger,bouncetime=5)
        logger.info ("GPIO     : Callback function 'cycle_trigger' binded to event detection on GPIO "+str(mygpio_handler.GPIOMap["I_StartButton"]))
        input("\nDunebugger listening. Press enter to quit\n")

    except KeyboardInterrupt:
        logger.debug ("stopped through keyboard")
        
    #except Exception as exc:
    #    logger.critical ("Exception: "+str(exc)+". Exiting." )

    finally:
        logger.info ("GPIO     : removing interrupt on GPIO "+str(mygpio_handler.GPIOMap["I_StartButton"])+" and cleaning up GPIOs")
        GPIO.remove_event_detect(mygpio_handler.GPIOMap["I_StartButton"])
        mygpio_handler.cleanup()
        audioPlayer.vstopaudio()

if __name__ == "__main__":
    main()

