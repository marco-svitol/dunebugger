import time
import threading
import random
from dunebugger_settings import settings
from dunebugger_logging import logger

class CycleHandler():

    def __init__(self, mygpio_handler, state_tracker, GPIO):
        self.cycle_thread_lock = threading.Lock()
        self.cycle_event = threading.Event()
        self.cycle_event.set()
        self.cycle_stop_event = threading.Event()
        self.cycle_playing_time = 0
        self.cycle_time_thread = None
        self.cycle_time_thread_stop_event = threading.Event()
        self.cycle_offset = 0
        self.mQueueCyclePlayingResolutionSecs = settings.mQueueCyclePlayingResolutionSecs
        self.mygpio_handler = mygpio_handler
        self.state_tracker = state_tracker
        self.GPIO = GPIO
        self.sequences_validated = False
        self.sequence_handler = None  # Will be set after SequencesHandler is created
        
    def _update_cycle_time(self):
        while not self.cycle_time_thread_stop_event.is_set():
            time.sleep(self.mQueueCyclePlayingResolutionSecs)
            self.cycle_playing_time += self.mQueueCyclePlayingResolutionSecs
            self.state_tracker.notify_update("playing_time")
            if random.random() < 0.01:
                logger.debug(f"Cycle playing time: {self.cycle_playing_time} seconds")

    def _start_cycle_time_thread(self):
        """Start a thread to update the cycle playing time."""
        self.cycle_playing_time = 0  # Reset playing time
        self.cycle_time_thread_stop_event.clear()
        self.cycle_time_thread = threading.Thread(target=self._update_cycle_time, daemon=True)
        self.cycle_time_thread.start()

    def _stop_cycle_time_thread(self):
        """Stop the cycle time thread."""
        if self.cycle_time_thread:
            self.cycle_time_thread_stop_event.set()
            self.cycle_time_thread.join()
            self.cycle_time_thread = None
            self.cycle_playing_time = 0  # Reset playing time
            self.state_tracker.notify_update("playing_time")

    def cycle_stop(self):
        self.cycle_stop_event.set()
        return "Cycle stop signal sent"

    def cycle_trigger(self, channel=False, sequence_name=None):
        if self.get_cycle_state():
            return "Cycle is already running"
        
        with self.cycle_thread_lock:
            # Check if sequences are validated before starting cycle
            if not self.sequences_validated:
                logger.error("Cannot start cycle: sequence files are not properly validated. Please check sequence files configuration.")
                return
            
            if channel is not False:
                # TODO : fix bouncing
                # start_time = time.time()
                # while time.time() < start_time + settings.bouncingTreshold:
                time.sleep(settings.bouncingTreshold)  # avoid catching a bouncing
                if self.GPIO.input(channel) != 1:
                    logger.debug("Warning! Cycle: below treshold of " + str(settings.bouncingTreshold) + " on channel" + str(channel))
                    return

            logger.info("Start button pressed")
            threading.Thread(name="_cycle_thread", target=self.cycle, args=(sequence_name,), daemon=True).start()
            return "Cycle started"

    def get_cycle_state(self):
        if self.cycle_event.is_set():
            return False
        return True

    def cycle(self, sequence_name=None):
        with self.cycle_thread_lock:
            self.cycle_event.clear()
            self.cycle_stop_event.clear()
            self._start_cycle_time_thread()
            # Use provided sequence_name or fall back to settings.playFile
            seq_name = sequence_name if sequence_name is not None else settings.playFile
            self.sequence_handler.sequence_start(seq_name)
            self._stop_cycle_time_thread()
            self.cycle_offset = 0
            self.cycle_event.set()

    def get_playing_time(self):
        return self.cycle_playing_time

    def cycle_waituntil(self, target_time_mark_seconds):
        logger.debug("Waiting: " + str(target_time_mark_seconds - self.cycle_offset))
        self.cycle_event.wait((target_time_mark_seconds - self.cycle_offset))
        self.cycle_offset = target_time_mark_seconds

    def execute_start_button_command(self, args, dry_run=False):
        if args is None or len(args) == 0:
            raise ValueError("Usage: start_button <enable|disable> : enable/disable start button handling")
        
        action = args[0].lower()
        if action not in ["enable", "disable"]:
            raise ValueError("Invalid argument. Usage: start_button <enable|disable> : enable/disable start button handling")
        else:
            if dry_run:
                return True
            else:
                if action == "enable":
                    self.enable_start_button()
                    return "Start button enabled"
                elif action == "disable":
                    self.disable_start_button()
                    return "Start button disabled"
                else:
                    raise ValueError("Invalid argument. Usage: start_button <enable|disable> : enable/disable start button handling")

    def enable_start_button(self):
        self.mygpio_handler.addEventDetect(settings.startButtonGPIOName, lambda channel: self.cycle_trigger(channel), bouncetime=int(settings.startButtonBouncetimeMillis))
        self.start_button_enabled = True
        self.state_tracker.notify_update("start_button")

    def disable_start_button(self):
        self.mygpio_handler.removeEventDetect(settings.startButtonGPIOName)
        self.start_button_enabled = False
        self.state_tracker.notify_update("start_button")