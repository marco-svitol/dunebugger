from audio_handler import audioPlayer
from gpio_handler import mygpio_handler, GPIO
from utils import validate_path
import random, os
from os import path
from dunebugger_settings import settings
import motor
from dunebuggerlogging import logger
import time
import atexit
import threading


class SequencesHandler:

    lastTimeMark = 0

    def __init__(self):
        self.sequenceFolder = path.join(path.dirname(path.abspath(__file__)), f"../sequences/{settings.sequenceFolder}")
        self.random_elements = {}
        self.random_elements_file = settings.randomElementsFile
        self.sequence_file = settings.sequenceFile
        self.standby_file = settings.standbyFile
        self.off_file = settings.offFile
        self.cycle_thread_lock = threading.Lock()
        self.cycle_event = threading.Event()
        self.cycle_stop_event = threading.Event()

        atexit.register(self.sequence_clean)

        self.sequences = self.validate_all_sequence_files(self.sequenceFolder)

    def validate_all_sequence_files(self, directory):
        try:
            for filename in os.listdir(directory):
                if filename.endswith(".seq"):
                    file_path = os.path.join(directory, filename)
                    logger.debug(f"Validating sequence {file_path}")
                    self.read_sequence_file(file_path, dry_run=True)

        except OSError as e:
            logger.error(f"Error validating sequence files in {directory}: {e}")

    def process_sequence_file(self, sequenceFile):
        try:
            file_path = os.path.join(self.sequenceFolder, sequenceFile)
            self.read_sequence_file(file_path)
            logger.info(f"Processing sequence {file_path}")
        except OSError as e:
            logger.error(f"Error processing sequence file {file_path}: {e}")

    def execute_motor_command(self, motor_number, direction, speed):
        motor_enabled = getattr(settings, f"motor{motor_number}Enabled", False)
        if motor_enabled:
            motor.start(motor_number, direction, speed)

    def execute_switch_command(self, device_name, action):
        if action.lower() == "on" or action.lower() == "off":
            mygpio_handler.gpio_set_output(device_name, action.lower())
        else:
            logger.error(f"Unknown action: {action}")

    def execute_waituntil_command(self, duration):
        self.waituntil(duration)

    def execute_audio_fadeout_command(self, fadeout_secs):
        audioPlayer.vstopaudio(fadeout_secs)

    def execute_playmusic_command(self, music_folder):
        gpio = mygpio_handler.GPIOMap[settings.startButtonGPIOName]
        if GPIO.input(gpio) == 1:
            audioPlayer.setEasterEggTrigger(True)
        audioPlayer.playMusic(music_folder)

    def execute_play_sfx_command(self, music_folder):
        audioPlayer.play_sfx(music_folder)

    def execute_command(self, command_body, dry_run=False):
        parts = command_body.split()

        verb = parts[0].lower()
        # TODO: motor stop
        if verb == "motor" and settings.motorEnabled:
            if parts[1].lower() == "start":
                motor_number = int(parts[2])
                direction = parts[3].lower()
                speed = int(parts[4])
                if not dry_run:
                    self.execute_motor_command(motor_number, direction, speed)
        else:

            # TODO verify switch works
            if verb == "switch":
                device_name = parts[1]
                action = parts[2]
                if not dry_run:
                    self.execute_switch_command(device_name, action)

            elif verb == "audio" and len(parts) >= 2:
                action = parts[1].lower()
                parameter = parts[2].lower()
                if action == "fadeout":
                    fadeout_secs = int(parameter)
                    if not dry_run:
                        self.execute_audio_fadeout_command(fadeout_secs)
                elif action == "playmusic":
                    music_folder = audioPlayer.get_music_path(parameter)
                    if dry_run:
                        if not validate_path(music_folder):
                            logger.error(f"Music folder {music_folder} does not exist")
                            return False
                    else:
                        self.execute_playmusic_command(music_folder)
                elif action == "playsfx":
                    sfx_file = audioPlayer.get_sfx_filepath(parameter)
                    if dry_run:
                        if not validate_path(sfx_file):
                            logger.error(f"Sfx file {sfx_file} does not exist")
                            return False
                    else:
                        self.execute_play_sfx_command(sfx_file)
            else:
                logger.error(f"Unknown command: {command_body}")
                return False

        return True

    def read_sequence_file(self, file_path, dry_run=False):
        try:
            with open(file_path) as file:
                for line_num, line in enumerate(file, start=1):
                    command_line = line.strip()

                    # Remove everything after #, treating it as a comment
                    command_line = command_line.split("#", 1)[0].strip()
                    command_line = command_line.split("//", 1)[0].strip()

                    if not command_line:
                        # If the line is empty after removing the comment, skip it
                        continue

                    time_mark_seconds, command_body = self.extract_time_mark(command_line)
                    if time_mark_seconds is not None:
                        if not dry_run:
                            self.execute_waituntil_command(int(time_mark_seconds))
                        # check for stop signal
                        if self.cycle_stop_event.is_set():
                            self.cycle_stop_event.clear()
                            break
                        command_result = self.execute_command(command_body, dry_run)
                        if dry_run and not command_result:
                            raise ValueError(f"Error validating sequence: {file_path} (line {line_num}). Review the command there.")
                    else:
                        raise ValueError(f"Error validating sequence: {file_path} (line {line_num}). Time mark needs a fix")

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")

    def extract_time_mark(self, command):
        parts = command.split(" ", 1)
        if len(parts) == 2:
            time_mark = parts[0].strip()
            command_body = parts[1].strip()
            if ":" in time_mark:
                # Check if the time mark contains hours, minutes, and seconds
                time_components = time_mark.split(":")
                if len(time_components) == 3:
                    # Convert HH:MM:SS format to seconds
                    hours, minutes, seconds = map(int, time_components)
                    time_mark_seconds = hours * 3600 + minutes * 60 + seconds
                elif len(time_components) == 2:
                    # Convert MM:SS format to seconds
                    minutes, seconds = map(int, time_components)
                    time_mark_seconds = minutes * 60 + seconds
                else:
                    raise ValueError("Invalid time format")
                return time_mark_seconds, command_body
            else:
                return time_mark, command_body

        return None, command

    def random_sequence_from_file(self, file_name):
        try:
            file_path = path.join(self.sequenceFolder, file_name)
            with open(file_path) as file:
                self.random_elements = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return

    def random_action(self):
        rand_elem = random.choice(self.random_elements)
        mygpio_handler.gpiomap_toggle_output(rand_elem)

    def random_actions(self):
        while not self.random_actions_event.is_set():
            self.random_actions_event.wait(timeout=random.uniform(settings.randomActionsMinSecs, settings.randomActionsMaxSecs))
            self.random_action()

    def enable_random_actions(self):
        if settings.randomActionsEnabled:
            self.random_sequence_from_file(self.random_elements_file)
            self.random_actions_event = threading.Event()
            self.random_actions_event.clear()
            self.random_actions_thread = threading.Thread(name="_random_actions", target=self.random_actions, daemon=True)
            self.random_actions_thread.start()

    def disable_random_actions(self):
        if hasattr(self, "random_actions_event"):
            self.random_actions_event.set()

    def get_random_actions_status(self):
        if hasattr(self, "random_actions_event"):
            if not self.random_actions_event.is_set():
                return True
        return False

    def setStandByMode(self):
        file_path = os.path.join(self.sequenceFolder, self.standby_file)
        self.read_sequence_file(file_path)

    def setOffMode(self):
        file_path = os.path.join(self.sequenceFolder, self.off_file)
        self.read_sequence_file(file_path)

    def start(self):
        file_path = os.path.join(self.sequenceFolder, self.sequence_file)
        self.read_sequence_file(file_path)

    def waituntil(self, sec):
        logger.debug("Waiting: " + str(sec - settings.cycleoffset))
        self.cycle_event.wait((sec - settings.cycleoffset) * settings.cyclespeed)
        settings.cycleoffset = sec

    def sequence_clean(self):
        logger.debug("Sequence clean")
        self.disable_start_button()

    def enable_start_button(self):
        mygpio_handler.addEventDetect(settings.startButtonGPIOName, lambda channel: self.cycle_trigger(channel))

    def disable_start_button(self):
        try:
            mygpio_handler.removeEventDetect(settings.startButtonGPIOName)
        except Exception as e:
            logger.debug(f"Error while disabling start button {e}")

    def cycle_stop(self):
        self.cycle_stop_event.set()

    def cycle_trigger(self, channel=False):
        with self.cycle_thread_lock:
            if False != channel:
                # TODO : fix bouncing
                # start_time = time.time()
                # while time.time() < start_time + settings.bouncingTreshold:
                time.sleep(settings.bouncingTreshold)  # avoid catching a bouncing
                if GPIO.input(channel) != 1:
                    logger.debug("Warning! Cycle: below treshold of " + str(settings.bouncingTreshold) + " on channel" + str(channel))
                    return

            logger.info("Start button pressed")
            threading.Thread(name="_cycle_thread", target=self.cycle, daemon=True).start()

    def cycle(self):
        with self.cycle_thread_lock:
            self.cycle_event.clear()
            self.cycle_stop_event.clear()
            self.disable_random_actions()
            self.start()
            self.enable_random_actions()
            settings.cycleoffset = 0
            self.setStandByMode()


try:
    sequencesHandler = SequencesHandler()
except Exception as exc:
    logger.error(f"Error while creating SequenceHandler: {exc}")
    exit()
