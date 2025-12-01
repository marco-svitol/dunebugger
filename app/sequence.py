import asyncio
import time
import atexit
import threading
import random
import os
from os import path

from dunebugger_settings import settings
from dunebugger_logging import logger
from utils import validate_path


class SequencesHandler:

    lastTimeMark = 0

    def __init__(self, mygpio_handler, GPIO, audio_handler, state_tracker, motor_handler, dmx_handler):
        self.sequenceFolder = path.join(path.dirname(path.abspath(__file__)), f"/etc/dunebugger/sequences/{settings.sequenceFolder}")
        self.random_elements = {}
        self.random_elements_file = settings.randomElementsFile
        self.sequence_file = settings.sequenceFile
        self.standby_file = settings.standbyFile
        self.off_file = settings.offFile
        self.sequences_validated = False
        self.cycle_thread_lock = threading.Lock()
        self.cycle_event = threading.Event()
        self.cycle_stop_event = threading.Event()
        self.state_tracker = state_tracker
        self.mygpio_handler = mygpio_handler
        self.audio_handler = audio_handler
        self.motor_handler = motor_handler
        self.dmx_handler = dmx_handler
        self.GPIO = GPIO
        self.start_button_enabled = False
        self.cycle_playing_time = 0
        self.cycle_time_thread = None
        self.cycle_time_thread_stop_event = threading.Event()
        self.cycle_offset = 0
        self.mQueueCyclePlayingResolutionSecs = int(settings.mQueueCyclePlayingResolutionSecs)

        atexit.register(self.sequence_clean)
        try:
            self.set_sequences_validated(self.validate_all_sequence_files(self.sequenceFolder))
        except Exception as e:
            logger.error(f"Initial sequence validation error: {str(e)}")

    def update_cycle_time(self):
        while not self.cycle_time_thread_stop_event.is_set():
            time.sleep(self.mQueueCyclePlayingResolutionSecs)
            self.cycle_playing_time += self.mQueueCyclePlayingResolutionSecs
            self.state_tracker.notify_update("playing_time")
            if random.random() < 0.01:
                logger.debug(f"Cycle playing time: {self.cycle_playing_time} seconds")

    def start_cycle_time_thread(self):
        """Start a thread to update the cycle playing time."""
        self.cycle_playing_time = 0  # Reset playing time
        self.cycle_time_thread_stop_event.clear()
        self.cycle_time_thread = threading.Thread(target=self.update_cycle_time, daemon=True)
        self.cycle_time_thread.start()

    def stop_cycle_time_thread(self):
        """Stop the cycle time thread."""
        if self.cycle_time_thread:
            self.cycle_time_thread_stop_event.set()
            self.cycle_time_thread.join()
            self.cycle_time_thread = None
            self.cycle_playing_time = 0  # Reset playing time
            self.state_tracker.notify_update("playing_time")

    def validate_timestamps_order(self, file_path):
        try:
            timestamps = []
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
                        try:
                            # Convert time_mark_seconds to int if it's a string
                            if isinstance(time_mark_seconds, str):
                                time_mark_seconds = int(time_mark_seconds)
                            timestamps.append((time_mark_seconds, line_num))
                        except ValueError:
                            raise ValueError(f"Invalid format at line {line_num}: {time_mark_seconds}")
                    else:
                        raise ValueError(f"Missing or invalid timestamp at line {line_num}")

            # Check if timestamps are in consecutive order
            for i in range(1, len(timestamps)):
                current_time, current_line = timestamps[i]
                previous_time, previous_line = timestamps[i-1]
                
                if current_time < previous_time:
                    raise ValueError(f"Line {current_line} has timestamp {current_time}s which is less than "
                               f"line {previous_line} timestamp {previous_time}s")

            logger.debug(f"Timestamp validation passed for {file_path}")
            return True

        except FileNotFoundError:
            raise FileNotFoundError(f"File not found during timestamp validation: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Error validating timestamps in {file_path}: {e}")

    def set_sequences_validated(self, validation_result: bool):
        if isinstance(validation_result, bool):
            if self.sequences_validated != validation_result:
                self.sequences_validated = validation_result
                self.state_tracker.notify_update("sequences_validated")
        else:
            return validation_result

    def validate_single_sequence_file(self, file_path):
        # First validate syntax by doing a dry run
        self.read_sequence_file(file_path, dry_run=True)
        
        # Then validate timestamp order
        self.validate_timestamps_order(file_path)
        return True

    def validate_all_sequence_files(self, directory):
        try:
            # First, validate that required configuration files exist
            required_files = [
                self.sequence_file,
                self.standby_file,
                self.off_file,
                self.random_elements_file
            ]
            
            missing_files = []
            for required_file in required_files:
                file_path = os.path.join(directory, required_file)
                if not os.path.exists(file_path):
                    missing_files.append(required_file)
            
            if missing_files:
                raise FileNotFoundError(f"Missing required sequence files in {directory}: {', '.join(missing_files)}")
            
            # Then validate all .seq files for syntax and timestamp order
            for filename in os.listdir(directory):
                if filename.endswith(".seq"):
                    file_path = os.path.join(directory, filename)
                    logger.debug(f"Validating sequence {file_path}")
                    self.validate_single_sequence_file(file_path)

            logger.info(f"All sequence files validated successfully in {directory}")
            return True
            
        except OSError as e:
            raise OSError(f"Error validating sequence files in {directory}: {e}")

    def revalidate_sequences(self):
        """Re-validate all sequence files. Useful after configuration changes."""
        logger.info("Re-validating sequence files...")
        self.set_sequences_validated(self.validate_all_sequence_files(self.sequenceFolder))
        return self.sequences_validated

    def execute_motor_command(self, motor_number, direction, speed):
        motor_enabled = getattr(settings, f"motor{motor_number}Enabled", False)
        if motor_enabled:
            self.motor_handler.start(motor_number, direction, speed)

    def execute_dmx_command(self, dmx_command, channel, scene_or_value, duration=2.0):
        if not settings.dmxEnabled:
            raise ValueError("DMX module is disabled")
        else:
            if self.dmx_handler.serial_conn is None:
                raise ConnectionError("DMX module is not connected")
        
        if dmx_command == "fade":
            self.dmx_handler.fade_to_scene(scene_or_value, channel, duration)
        elif dmx_command == "set":
            self.dmx_handler.set_scene(scene_or_value, channel)
        elif dmx_command == "dimmer":
            self.dmx_handler.set_dimmer(scene_or_value, channel)
        elif dmx_command == "fade_dimmer":
            self.dmx_handler.fade_to_dimmer(scene_or_value, channel, duration)
        else:
            raise ValueError(f"Unknown DMX command: {dmx_command}")

    def execute_switch_command(self, device_name, action):
        if action.lower() == "on" or action.lower() == "off":
            # Warning: on GPIO the action is inverted: on = 0, off = 1
            gpio_value = 0 if action.lower() == "on" else 1
            self.mygpio_handler.gpio_set_output(device_name, gpio_value)
        else:
            logger.error(f"Unknown action: {action}")

    def execute_waituntil_command(self, duration):
        self.waituntil(duration)

    def execute_audio_fadeout_command(self, fadeout_secs):
        self.audio_handler.vstopaudio(fadeout_secs)

    def execute_playmusic_command(self, music_folder):
        gpio = self.mygpio_handler.GPIOMap[settings.startButtonGPIOName]
        if self.GPIO.input(gpio) == 1:
            self.audio_handler.setEasterEggTrigger(True)
        self.audio_handler.playMusic(music_folder)

    def execute_play_sfx_command(self, music_folder):
        self.audio_handler.play_sfx(music_folder)

    def execute_command(self, command_body, dry_run=False):
        parts = command_body.split()

        verb = parts[0].lower()
        # TODO: motor stop
        if verb == "motor" and settings.motorEnabled:
            if parts[1].lower() == "start":
                motor_number = int(parts[2])
                direction = parts[3].lower()
                speed = int(parts[4])

                # Validate motor number
                if not isinstance(motor_number, int) or motor_number < 1 :
                    raise ValueError(f"Invalid motor number: {motor_number}")

                # Validate direction
                if direction not in ["ccw", "cw"]:
                    raise ValueError(f"Invalid motor direction: {direction}")
                # Validate speed
                if  not isinstance(speed, int) or speed < 1:
                    raise ValueError(f"Invalid motor speed: {speed}")
                    
                if not dry_run:
                    self.execute_motor_command(motor_number, direction, speed)
                        
        else:
            # Verify switch command
            if verb == "switch":
                device_name = parts[1]
                action = parts[2].lower()

                # Validate device name
                if device_name not in self.mygpio_handler.GPIOMap:
                    raise ValueError(f"Invalid device name: {device_name}")

                # Validate action
                if action not in ["on", "off"]:
                    raise ValueError(f"Invalid action: {action}. Action must be 'on' or 'off'.")
                if not dry_run:
                    self.execute_switch_command(device_name, action)

            elif verb == "audio" and len(parts) >= 2:
                action = parts[1].lower()
                parameter = parts[2].lower()

                if action == "fadeout":
                    fadeout_secs = int(parameter)
                    if  not isinstance(fadeout_secs, int) or fadeout_secs < 0:
                        raise ValueError(f"Invalid fadeout seconds: {fadeout_secs}")
                    if not dry_run:
                        self.execute_audio_fadeout_command(fadeout_secs)

                elif action == "playmusic":
                    music_folder = self.audio_handler.get_music_path(parameter)
                    if not validate_path(music_folder):
                        raise ValueError(f"Music folder {music_folder} does not exist")
                    else:
                        if not dry_run:
                            self.execute_playmusic_command(music_folder)
                            
                elif action == "playsfx":
                    sfx_file = self.audio_handler.get_sfx_filepath(parameter)
                    if not validate_path(sfx_file):
                        raise ValueError(f"Sfx file {sfx_file} does not exist")
                    else:
                        if not dry_run:
                            self.execute_play_sfx_command(sfx_file)
                else:
                    raise ValueError(f"Unknown audio action: {action}")

            #TODO: revisit the command interpreter vs sequence parser. Refactor to avoid code duplication.
            elif verb == "dmx":
                parsed_dmx_command_args = self.dmx_handler.validate_dmx_command_args(parts[1:])
                if isinstance(parsed_dmx_command_args, str):
                    raise ValueError(parsed_dmx_command_args)
                _, dmx_command, channel, scene_or_value, duration = parsed_dmx_command_args

                if not dry_run:
                    try:
                        self.execute_dmx_command(dmx_command, channel, scene_or_value, duration)
                        if dmx_command in ["fade", "fade_dimmer"]:
                            logger.debug(f"DMX command '{dmx_command}' executed on channel {channel} with value '{scene_or_value}' over {duration}s")
                        else:
                            logger.debug(f"DMX command '{dmx_command}' executed on channel {channel} with value '{scene_or_value}'")
                    except Exception as e:
                        logger.error(f"Error executing DMX command: {e}")
                else:
                    if not settings.dmxEnabled:
                        logger.warning("DMX module is disabled")
                    else:
                        if self.dmx_handler.serial_conn is None:
                            logger.warning("DMX module is not connected")
                        
            else:
                raise ValueError(f"Unknown command: {command_body}")

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
                    if not dry_run:
                        self.execute_waituntil_command(int(time_mark_seconds))
                    # check for stop signal
                    if self.cycle_stop_event.is_set():
                        self.cycle_stop_event.clear()
                        break
                    self.execute_command(command_body, dry_run)

        except FileNotFoundError:
           raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Error reading sequence file {file_path} line {line_num}: {e}")


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

        raise ValueError("Invalid command format")

    def random_sequence_from_file(self, file_name):
        try:
            file_path = path.join(self.sequenceFolder, file_name)
            with open(file_path) as file:
                self.random_elements = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Error reading random elements file {file_path}: {e}")

    def random_action(self):
        rand_elem = random.choice(self.random_elements)
        self.mygpio_handler.gpiomap_toggle_output(rand_elem)

    def random_actions(self):
        while not self.random_actions_event.is_set():
            self.random_actions_event.wait(timeout=random.uniform(settings.randomActionsMinSecs, settings.randomActionsMaxSecs))
            self.random_action()

    def enable_random_actions(self):
        self.random_sequence_from_file(self.random_elements_file)
        self.random_actions_event = threading.Event()
        self.random_actions_event.clear()
        self.random_actions_thread = threading.Thread(name="_random_actions", target=self.random_actions, daemon=True)
        self.random_actions_thread.start()
        self.state_tracker.notify_update("random_actions")

    def disable_random_actions(self):
        if hasattr(self, "random_actions_event"):
            self.random_actions_event.set()
            self.state_tracker.notify_update("random_actions")

    def get_random_actions_state(self):
        if hasattr(self, "random_actions_event"):
            if not self.random_actions_event.is_set():
                return True
        return False

    def restore_random_actions_state(self, state):
        if state:
            self.enable_random_actions()
        else:
            self.disable_random_actions()

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
        logger.debug("Waiting: " + str(sec - self.cycle_offset))
        self.cycle_event.wait((sec - self.cycle_offset) * settings.cyclespeed)
        self.cycle_offset = sec

    def sequence_clean(self):
        logger.debug("Sequence clean")
        self.disable_start_button()

    def enable_start_button(self):
        self.mygpio_handler.addEventDetect(settings.startButtonGPIOName, lambda channel: self.cycle_trigger(channel))
        self.start_button_enabled = True
        self.state_tracker.notify_update("start_button")

    def disable_start_button(self):
        self.mygpio_handler.removeEventDetect(settings.startButtonGPIOName)
        self.start_button_enabled = False
        self.state_tracker.notify_update("start_button")

    def get_start_button_state(self):
        return self.start_button_enabled

    def cycle_stop(self):
        self.cycle_stop_event.set()

    def cycle_trigger(self, channel=False):
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
            threading.Thread(name="_cycle_thread", target=self.cycle, daemon=True).start()

    def get_cycle_state(self):
        if self.cycle_event.is_set():
            return True
        return False

    def cycle(self):
        with self.cycle_thread_lock:
            self.cycle_event.clear()
            self.cycle_stop_event.clear()
            self.save_random_actions_state = self.get_random_actions_state()
            self.disable_random_actions()
            self.start_cycle_time_thread()
            self.start()
            self.stop_cycle_time_thread()
            self.restore_random_actions_state(self.save_random_actions_state)
            self.cycle_offset = 0
            self.setStandByMode()

    def get_state(self):
        return {
            "random_actions": self.get_random_actions_state(),
            "cycle_running": self.get_cycle_state(),
            "start_button_enabled": self.get_start_button_state(),
            "sequences_validated": self.sequences_validated,
        }

    def get_playing_time(self):
        return self.cycle_playing_time

    def get_sequence(self, sequence_name):
        if sequence_name == "main":
            file_path = os.path.join(self.sequenceFolder, self.sequence_file)
        elif sequence_name == "standby":
            file_path = os.path.join(self.sequenceFolder, self.standby_file)
        elif sequence_name == "off":
            file_path = os.path.join(self.sequenceFolder, self.off_file)
        else:
            return {"error": "Unknown sequence name"}

        try:
            sequence_data = self._parse_sequence_file(file_path)
            return {"sequence": sequence_data}
        except FileNotFoundError:
            logger.error(f"Sequence file not found: {file_path}")
            return {"error": "Sequence file not found"}
        except Exception as e:
            logger.error(f"Error reading sequence file {file_path}: {e}")
            return {"error": str(e)}

    def _parse_sequence_file(self, file_path):
        sequence_data = []
        with open(file_path) as file:
            for line in file:
                command_line = line.strip()

                # Remove comments
                command_line = command_line.split("#", 1)[0].strip()
                command_line = command_line.split("//", 1)[0].strip()

                if not command_line:
                    continue

                time_mark, command_body = self.extract_time_mark(command_line)
                if time_mark is not None:
                    parts = command_body.split()
                    command = parts[0]#.lower()
                    action = parts[1] if len(parts) > 1 else None #parts[1].lower() if len(parts) > 1 else None
                    parameter = " ".join(parts[2:]) if len(parts) > 2 else None

                    sequence_data.append({"time": time_mark, "command": command, "action": action, "parameter": parameter})
                else:
                    logger.error(f"Invalid time mark in sequence file: {file_path}")
        return sequence_data

    def upload_sequence_file(self, filename, file_content):
        try:
            # Validate filename
            if not filename.endswith('.seq'):
                raise ValueError("Filename must end with .seq extension")
            
            # Sanitize filename to prevent path traversal attacks
            filename = os.path.basename(filename)
            if not filename or filename in ['', '.', '..']:
                raise ValueError("Invalid filename")
            
            # Set file path (will overwrite if exists)
            file_path = os.path.join(self.sequenceFolder, filename)
            
            # Validate file content by creating a temporary file and testing it
            import tempfile
            import shutil
            
            filename_prefix = f"{os.path.splitext(filename)[0]}_"
            with tempfile.NamedTemporaryFile(mode='w', prefix=filename_prefix, suffix='.seq', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            self.validate_single_sequence_file(temp_file_path)

            backup_created = False
            backup_path = None
                
            # Create backup if file already exists
            if os.path.exists(file_path):
                backup_filename = f"{os.path.splitext(filename)[0]}.bak"
                backup_path = os.path.join(self.sequenceFolder, backup_filename)
                
                try:
                    shutil.copy2(file_path, backup_path)
                    backup_created = True
                    logger.info(f"Created backup of existing file: {backup_filename}")
                except Exception as e:
                    logger.warning(f"Failed to create backup for {filename}: {e}")
                    # Continue with upload even if backup fails
                
            # If validation passes, write the file to the sequence folder
            with open(file_path, 'w') as f:
                f.write(file_content)
                
            logger.info(f"Successfully uploaded sequence file: {filename}")
            
            # Re-validate all sequences after upload
            # self.revalidate_sequences()
            
            success_message = f"Sequence file {filename} uploaded successfully"

            self.state_tracker.notify_update("sequence")

            if backup_created:
                success_message += f" (backup created: {os.path.basename(backup_path)})"
            
            return {
                "success": True, 
                "message": success_message,
                "file_path": file_path,
                "backup_path": backup_path if backup_created else None
            }
                
                                    
        except Exception as e:
            raise RuntimeError(str(e).replace(temp_file_path, filename))

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
