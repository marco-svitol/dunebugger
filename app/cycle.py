#!/usr/bin/env python3
# coding: utf8
import os, time, RPi.GPIO as GPIO, serial
from gpio_handler import mygpio_handler, DebouncedButton
import motor
from dunebuggerlogging import logger
import threading
from audio_handler import audioPlayer
from dunebugger_settings import settings
import sequence
import traceback
import random

def random_actions(event):
    while (settings.randomActionsEnabled):
        event.wait(timeout=random.uniform(settings.randomActionsMinSecs,settings.randomActionsMaxSecs))
        if not event.is_set():
            sequence.random_sequence(event)
    logger.debug("Random actions exiting")

def cycle_trigger(channel, my_random_actions_event):
    threading.Thread(name='_cycle_thread', target=cycle, args=(channel,my_random_actions_event)).start()

def cycle(channel, my_random_actions_event):
    with settings.cycle_thread_lock:

        time.sleep(settings.bouncingTreshold)    # avoid catching a bouncing
        if GPIO.input(channel) != 1:
            logger.debug ("Warning! Cycle: below treshold of "+str(settings.bouncingTreshold)+" on channel"+str(channel))
            return
        
        logger.info("Start button pressed on channel "+str(channel)) #if function is triggered from button then check three state mode
        
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

        my_random_actions_event.set()
        if settings.testdunebugger:
            sequence.testCommands()
        else:
            sequence.sequence()

        my_random_actions_event.clear()

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
        logger.info('Setting standby state')
        sequence.setStandBy()

        # Start button available only after motor reset:
        #  we put an event in the motor.limitTouch callback of MotorXLimitCCW
        #  so that execution continues only when event is set on both motors
        motor1_reset_event = threading.Event()
        
        Motor1LimitCCW = DebouncedButton("Motor1LimitCCW",mygpio_handler.GPIOMap["Motor1LimitCCW"], settings.bouncingTreshold, motor.limitTouch)
        #Motor1LimitCW = DebouncedButton("Motor1LimitCW",mygpio_handler.GPIOMap["Motor1LimitCW"], settings.bouncingTreshold, motor.limitTouch, motor1_reset_event)

        motor2_reset_event = threading.Event()
        #Motor2LimitCCW = DebouncedButton("Motor2LimitCCW",mygpio_handler.GPIOMap["Motor2LimitCCW"], settings.bouncingTreshold, motor.limitTouch)
        #Motor2LimitCW = DebouncedButton("Motor2LimitCW",mygpio_handler.GPIOMap["Motor2LimitCW"], settings.bouncingTreshold, motor.limitTouch,motor2_reset_event)

        I_StartButton = None

        if (settings.motor1Enabled):
            motor.reset(1)
        if (settings.motor2Enabled):
            motor.reset(2)
        if (settings.motor1Enabled):
            motor1_reset_event.wait()
        if (settings.motor2Enabled):
            motor2_reset_event.wait()

        random_actions_event = threading.Event()
        I_StartButton = DebouncedButton("I_StartButton",mygpio_handler.GPIOMap["I_StartButton"], settings.bouncingTreshold, cycle_trigger, random_actions_event)
        logger.info ("GPIO     : Callback function 'cycle_trigger' binded to event detection on GPIO "+str(mygpio_handler.GPIOMap["I_StartButton"]))
        random_actions_thread = threading.Thread(target=random_actions(random_actions_event))
        #random_actions_thread.daemon = True
        random_actions_thread.start()

        input("\nDunebugger listening. Press enter to quit\n")

    except KeyboardInterrupt:
        logger.debug ("stopped through keyboard")
        
    except Exception as exc:
        traceback.print_exc()
        logger.critical ("Exception: "+str(exc)+". Exiting." )

    finally:
        logger.info ("GPIO     : removing interrupt on GPIO "+str(mygpio_handler.GPIOMap["I_StartButton"])+" and cleaning up GPIOs")
        GPIO.remove_event_detect(mygpio_handler.GPIOMap["I_StartButton"])
        Motor1LimitCCW.cleanup()
        Motor1LimitCW.cleanup()
        Motor2LimitCCW.cleanup()
        Motor2LimitCW.cleanup()
        if I_StartButton is not None:
            I_StartButton.cleanup()
        mygpio_handler.cleanup()
        audioPlayer.vstopaudio()

if __name__ == "__main__":
    main()

