
#
#!/usr/bin/env python3
# coding: utf8
import time
from gpio_handler import mygpio_handler, GPIO, TerminalInterpreter
import motor
from dunebuggerlogging import logger, set_logger_level
import threading
from audio_handler import audioPlayer
from dunebugger_settings import settings
from sequence import sequencesHandler
import signal_handler
import traceback
import random
import atexit

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
        time.sleep(settings.bouncingTreshold)    # avoid catching a bouncing
        if GPIO.input(channel) != 1:
            logger.debug ("Warning! Cycle: below treshold of "+str(settings.bouncingTreshold)+" on channel"+str(channel))
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
    while not signal_handler.sigint_received :
        # Wait for user input and process commands
        user_input = input("Enter command: ")
        terminalInterpreter.process_terminal_input(user_input, startFunction)

def mainClean():
    mygpio_handler.removeEventDetect("In_StartButton")
    mygpio_handler.cleanup()
    audioPlayer.vstopaudio()

def motorClean():
    mygpio_handler.removeEventDetect("In_Motor1LimitCCW")
    mygpio_handler.removeEventDetect("In_Motor1LimitCW")
    mygpio_handler.removeEventDetect("In_Motor2LimitCCW")
    mygpio_handler.removeEventDetect("In_Motor2LimitCW")

def main():
    atexit.register(mainClean)
    set_logger_level("dunebuggerLog", settings.dunebuggerLogLevel)
    terminalInterpreter = TerminalInterpreter(mygpio_handler, sequencesHandler)

    try:
        logger.debug('Setting standby state')
        sequencesHandler.setStandBy()

        # Start a separate thread for processing terminal input
        terminal_thread = threading.Thread(target=terminal_input_thread, args=(terminalInterpreter,cycle), daemon=True)
        terminal_thread.start()
        
        # Start button available only after motor reset:
        #  we put an event in the motor.limitTouch callback of MotorXLimitCCW
        #  so that execution continues only when event is set on both motors
        if (settings.motorEnabled):
            logger.warning(f"Motor module is ${settings.motorEnabled}")
            atexit.register(motorClean)
            motor1_reset_event = threading.Event()
            motor1_callback_with_params = lambda channel: motor.limitTouch(channel, motor1_reset_event)
            
            mygpio_handler.addEventDetect("In_Motor1LimitCCW",motor.limitTouch,5)
            mygpio_handler.addEventDetect("In_Motor1LimitCW", motor1_callback_with_params, 5)

            motor2_reset_event = threading.Event()
            motor2_callback_with_params = lambda channel: motor.limitTouch(channel, motor2_reset_event)

            mygpio_handler.addEventDetect("In_Motor2LimitCCW",motor.limitTouch,5)
            mygpio_handler.addEventDetect("In_Motor2LimitCW",motor2_callback_with_params,5)

            if (settings.motor1Enabled):
                motor.reset(1)
            if (settings.motor1Enabled):
                motor1_reset_event.wait()
            if (settings.motor2Enabled):
                motor.reset(2)
            if (settings.motor2Enabled):
                motor2_reset_event.wait()
        else:
            logger.warning("Motor module is disabled")

        mygpio_handler.addEventDetect("In_StartButton", lambda channel: cycle_trigger(channel, settings.random_actions_event))
        logger.debug ("Start button ready")

        random_actions_thread = threading.Thread(target=random_actions(settings.random_actions_event))
        random_actions_thread.start()

        while True:
            pass

    except KeyboardInterrupt:
        logger.debug ("stopped through keyboard")
        
    except Exception as exc:
        traceback.print_exc()
        logger.critical ("Exception: "+str(exc)+". Exiting." )

if __name__ == "__main__":
    main()

