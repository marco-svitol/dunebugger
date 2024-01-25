from utils import waituntil
from audio_handler import audioPlayer
from gpio_handler import RPiwrite, RPiToggle
import random, os
from os import path
from dunebugger_settings import settings
import motor
from dunebuggerlogging import logger

class SequencesHandler:
    
    lastTimeMark = 0

    def __init__(self):
        self.sequenceFolder = path.join(path.dirname(path.abspath(__file__)), f"../sequences/{settings.sequenceFolder}")
        self.random_elements = {}
        if (settings.randomActionsEnabled == True):
            self.random_sequence_from_file("randomelements")
        self.sequences = self.validate_all_sequence_files(self.sequenceFolder)
    
    def validate_all_sequence_files(self, directory):
        try:
            for filename in os.listdir(directory):
                if filename.endswith(".seq"):
                    file_path = os.path.join(directory, filename)
                    logger.info(f"Validating sequence {file_path}")
                    self.read_sequence_file(file_path, testcommand=True)
                    
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
        if action.lower() == "on":
            RPiwrite(device_name, 1)
        elif action.lower() == "off":
            RPiwrite(device_name, 0)
        else:
            logger.error(f"Unknown action: {action}")

    def execute_waituntil_command(self, duration):
        waituntil(duration)

    def execute_audio_fadeout_command(self):
        audioPlayer.vstopaudio()

    def execute_command(self, command, testmode = False):
        # Remove everything after #, treating it as a comment
        command = command.split('#', 1)[0].strip()

        if not command:
            # If the line is empty after removing the comment, skip it
            return True
        
        parts = command.split()

        verb = parts[0].lower()
        # TODO: motor stop
        if verb == "motor" and parts[1].lower() == "start":
            motor_number = int(parts[2])
            direction = parts[3].lower()
            speed = int(parts[4])
            if not testmode:
                self.execute_motor_command(motor_number, direction, speed)
        else:

            # TODO verify switch works
            if verb == "switch":
                device_name = parts[1]
                action = parts[2]
                if not testmode:
                    self.execute_switch_command(device_name, action)

            elif verb == "waituntil":
                timeMark = int(parts[1])
                if not testmode:
                    self.execute_waituntil_command(timeMark)
                else:
                    if timeMark <= self.lastTimeMark:
                        logger.error(f"TimeMark {timeMark} is lower or equal previous one: {self.lastTimeMark}")
                        return False

            elif verb == "audio" and len(parts) >= 2 and parts[1] == "fadeout": 
                action = parts[1]
                if not testmode:
                    if action == "fadeout":
                        self.execute_audio_fadeout_command()

            else:
                logger.error(f"Unknown command: {command}")
                return False
        
        return True

    def read_sequence_file(self, file_path, testcommand = False):
        try:
            with open(file_path, "r") as file:
                self.lastTimeMark = 0
                for line_num, line in enumerate(file, start=1):
                    command = line.strip()
                    if command:
                        commandResult = self.execute_command(command, testcommand)
                        if testcommand and not commandResult:
                            raise ValueError(f"Error validating sequence: {file_path} (line {line_num}). Fix sequence")
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")

    def random_sequence_from_file(self, file_name):
        try:
            file_path = path.join(self.sequenceFolder, file_name)
            with open(file_path, "r") as file:
                self.random_elements = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return

    def random_action(self):
        rand_elem = random.choice(self.random_elements)
        RPiToggle(rand_elem)

    def setStandBy(self):
        file_path = os.path.join(self.sequenceFolder, 'standby.seq')
        self.read_sequence_file(file_path)
    
    def start(self):
        sequence = 'main.seq'
        if settings.testdunebugger:
            sequence = 'test.seq'
        file_path = os.path.join(self.sequenceFolder, sequence)
        self.read_sequence_file(file_path)
try:
    sequencesHandler = SequencesHandler()
except Exception as exc:
    logger.error(f"Error while creating SequenceHandler: {exc}")
    exit()


