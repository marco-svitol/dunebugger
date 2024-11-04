#!/usr/bin/env python3
# coding: utf8
import time
from gpio_handler import mygpio_handler, GPIO, terminalInterpreter
import motor
from dunebuggerlogging import logger
import threading
from audio_handler import audioPlayer
from dunebugger_settings import settings
from sequence import sequencesHandler
import traceback
import random

def random_actions(event):
    while (settings.randomActionsEnabled):
        event.wait(timeout=random.uniform(settings.randomActionsMinSecs,settings.randomActionsMaxSecs))
        if not event.is_set():
            sequencesHandler.random_action()
    logger.debug("Random actions exiting")

def cycle_trigger(channel, my_random_actions_event):
    with settings.cycle_thread_lock:
        #TODO : fix bouncing
            #start_time = time.time()
            #while time.time() < start_time + settings.bouncingTreshold:
        time.sleep(0.05)    # avoid catching a bouncing
        if GPIO.input(channel) != 1:
            #logger.debug ("Warning! Cycle: below treshold of "+str(settings.bouncingTreshold)+" on channel"+str(channel))
            return
    
    threading.Thread(name='_cycle_thread', target=cycle, args=(channel,my_random_actions_event)).start()

def cycle(channel, my_random_actions_event):
    with settings.cycle_thread_lock:

        #TODO : fix bouncing

            #start_time = time.time()
            #while time.time() < start_time + settings.bouncingTreshold:

        # time.sleep(0.05)    # avoid catching a bouncing
        # if GPIO.input(channel) != 1:
        #     #logger.debug ("Warning! Cycle: below treshold of "+str(settings.bouncingTreshold)+" on channel"+str(channel))
        #     return
        
        logger.info("Start button pressed on channel")
    
        logger.debug("Starting music")
        easterEggOn = False
        if settings.eastereggEnabled:
            time.sleep(1)
            if GPIO.input(channel) == 1:
                easterEggOn = True
        audioPlayer.startAudio(easterEggOn)
        
        my_random_actions_event.set()

        sequencesHandler.start()

        my_random_actions_event.clear()

        settings.cycleoffset = 0
        logger.info("\nDunebugger listening.\n")

def terminal_input_thread(terminalInterpreter, startFunction):
    while True:
        # Wait for user input and process commands
        user_input = input("Enter command:")
        terminalInterpreter.process_terminal_input(user_input, startFunction)

def main():
    try:
        logger.info('Setting standby state')
        sequencesHandler.setStandBy()

        # Start a separate thread for processing terminal input
        terminal_thread = threading.Thread(target=terminal_input_thread, args=(terminalInterpreter,cycle), daemon=True)
        terminal_thread.start()
        
        # Start button available only after motor reset:
        #  we put an event in the motor.limitTouch callback of MotorXLimitCCW
        #  so that execution continues only when event is set on both motors
        '''
        motor1_reset_event = threading.Event()
        motor1_callback_with_params = lambda channel: motor.limitTouch(channel, motor1_reset_event)
        
        GPIO.add_event_detect(mygpio_handler.GPIOMap["In_Motor1LimitCCW"],GPIO.RISING,callback=motor.limitTouch,bouncetime=5)
        GPIO.add_event_detect(mygpio_handler.GPIOMap["In_Motor1LimitCW"], GPIO.RISING, callback=motor1_callback_with_params, bouncetime=5)

        motor2_reset_event = threading.Event()
        motor2_callback_with_params = lambda channel: motor.limitTouch(channel, motor2_reset_event)

        GPIO.add_event_detect(mygpio_handler.GPIOMap["In_Motor2LimitCCW"],GPIO.RISING,callback=motor.limitTouch,bouncetime=5)
        GPIO.add_event_detect(mygpio_handler.GPIOMap["In_Motor2LimitCW"],GPIO.RISING,callback=motor2_callback_with_params,bouncetime=5)

        if (settings.motor1Enabled):
            motor.reset(1)
        if (settings.motor1Enabled):
            motor1_reset_event.wait()
        if (settings.motor2Enabled):
            motor.reset(2)
        if (settings.motor2Enabled):
            motor2_reset_event.wait()
        '''
        #random_actions_event = threading.Event()

        mygpio_handler.setupStartButton(lambda channel: cycle_trigger(channel, settings.random_actions_event))
        logger.info ("Start button ready")

        random_actions_thread = threading.Thread(target=random_actions(settings.random_actions_event))
        #random_actions_thread.daemon = True
        random_actions_thread.start()

        while True:
            pass

    except KeyboardInterrupt:
        logger.debug ("stopped through keyboard")
        
    except Exception as exc:
        traceback.print_exc()
        logger.critical ("Exception: "+str(exc)+". Exiting." )

    finally:
        logger.info ("GPIO     : removing interrupt on GPIO "+str(mygpio_handler.GPIOMap["In_StartButton"])+" and cleaning up GPIOs")
        mygpio_handler.removeStartButton()
        mygpio_handler.cleanup()
        audioPlayer.vstopaudio()

if __name__ == "__main__":
    main()

