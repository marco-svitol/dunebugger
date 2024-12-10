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
import atexit

def cycle_trigger(channel, my_random_actions_event):
    with settings.cycle_thread_lock:
        #TODO : fix bouncing
            #start_time = time.time()
            #while time.time() < start_time + settings.bouncingTreshold:
        time.sleep(settings.bouncingTreshold)    # avoid catching a bouncing
        if GPIO.input(channel) != 1:
            logger.debug ("Warning! Cycle: below treshold of "+str(settings.bouncingTreshold)+" on channel"+str(channel))
            return
    
        threading.Thread(name='_cycle_thread', target=cycle, args=([my_random_actions_event])).start()

def cycle(my_random_actions_event):
    with settings.cycle_thread_lock:
        
        logger.info("Start button pressed")

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

def main():
    set_logger_level("dunebuggerLog", settings.dunebuggerLogLevel)

    terminalInterpreter = TerminalInterpreter(mygpio_handler, sequencesHandler)

    try:
        logger.debug('Setting standby state')
        sequencesHandler.setStandBy()

        # Start a separate thread for processing terminal input
        # 'cycle' function is passed to the 'terminal_input_thread' target function to be able to call the start
        # function from the terminal
        terminal_thread = threading.Thread(target=terminal_input_thread, args=(terminalInterpreter,cycle), daemon=True)
        terminal_thread.start()
        
        # check Motor module and init the motors in case
        # This call blocks the flow until motors have completed the reset cycle
        if (settings.motorEnabled):
            logger.info("Motor module is enabled")
            motor.initMotorLimits()
  
        mygpio_handler.addEventDetect(settings.startButtonGPIOName, lambda channel: cycle_trigger(channel, settings.random_actions_event))
        logger.debug ("Start button ready")

        random_actions_thread = threading.Thread(target=sequencesHandler.random_actions(settings.random_actions_event))
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
