import atexit
import os
from os import path

from dunebugger_settings import settings
from dunebugger_logging import logger
from random_actions_handler import RandomActions

class SequencesHandler:

    def __init__(self, random_actions_handler, state_tracker, command_interpreter, cycle_handler):
        self.sequenceFolder = path.join(path.dirname(path.abspath(__file__)), f"{settings.sequenceFolder}")
        self.play_file = settings.playFile
        self.sequences = []
        self.sequences_validated = False
        self.command_interpreter = command_interpreter
        self.state_tracker = state_tracker
        self.start_button_enabled = False
        self.random_actions_handler = random_actions_handler
        self.cycle_handler = cycle_handler
        
        atexit.register(self.sequence_clean)

    def initialize(self):
        try:
            self.set_sequences_validated(self.validate_all_sequence_files(self.sequenceFolder))
        except Exception as e:
            logger.error(f"Initial sequence validation error: {str(e)}")

    def revalidate_sequences(self):
        """Re-validate all sequence files. Useful after configuration changes."""
        logger.info("Re-validating sequence files...")
        self.set_sequences_validated(self.validate_all_sequence_files(self.sequenceFolder))
        return f"All sequence files validated successfully in directory: {self.sequenceFolder}"
    
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
                self.cycle_handler.sequences_validated = validation_result
        else:
            return validation_result

    def validate_single_sequence_file(self, file_path):
        # First validate syntax by doing a dry run
        self.read_sequence_file(file_path, dry_run=True)
        
        # Then validate timestamp order
        self.validate_timestamps_order(file_path)
        return True

    def validate_required_files_exist(self):
        """Check if all required sequence files exist in self.sequences."""
        required_files = [
            self.play_file,
        ]
        
        missing_files = []
        for required_file in required_files:
            if required_file not in self.sequences:
                missing_files.append(required_file)
        
        if missing_files:
            raise FileNotFoundError(f"Missing required sequence files: {', '.join(missing_files)}")
        
        return True

    def validate_all_sequence_files(self, directory):
        try:
            # Clear and populate self.sequences with all .seq files
            self.sequences = []
            
            # Validate all .seq files for syntax and timestamp order
            for filename in os.listdir(directory):
                if filename.endswith(".seq"):
                    file_path = os.path.join(directory, filename)
                    logger.debug(f"Validating sequence {file_path}")
                    self.validate_single_sequence_file(file_path)
                    self.sequences.append(filename)
            
            # Validate that required configuration files exist
            self.validate_required_files_exist()

            # Validate random elements file
            self.random_actions_handler.validate_random_elements_file()

            return True
            
        except OSError as e:
            raise OSError(f"Error validating sequence files in {directory}: {e}")


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
                        self.cycle_handler.cycle_waituntil(int(time_mark_seconds))
                    
                    # check for stop signal
                    if self.cycle_handler.cycle_stop_event.is_set():
                        self.cycle_handler.cycle_stop_event.clear()
                        logger.info("Sequence execution stopped by stop signal.")
                        break
                    
                    command_reply_message = self.command_interpreter.process_command(command_body, dry_run)
                    if command_reply_message["level"] == "warning":
                        logger.warning(f"Warning executing command '{command_body}' at line {line_num}: {command_reply_message['message']}")
                    elif command_reply_message["level"] == "error":
                        raise RuntimeError(f"Error executing command '{command_body}' at line {line_num}: {command_reply_message['message']}")
                    else:
                        if not dry_run:
                            logger.debug(f"Executed command '{command_body}' at line {line_num}: {command_reply_message['message']}")
                            #logger.debug(f"Received reply: {command_reply_message}")

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

    # Delegate methods to RandomActions handler
    def execute_random_actions_command(self, args, dry_run=False):
        """Delegate to RandomActions handler."""
        return self.random_actions_handler.execute_random_actions_command(args, dry_run)
    
    def get_random_actions_state(self):
        """Delegate to RandomActions handler."""
        return self.random_actions_handler.get_random_actions_state()

    def execute_sequence_command(self, args=None):
        """Execute sequence commands: start, stop, validate, or upload.
        
        Args:
            args: List of arguments where first element is the subcommand
        
        Returns:
            Result message or raises ValueError/RuntimeError on errors
        """
        if args is None or len(args) == 0:
            raise ValueError("Usage: sequence <play|stop|validate|upload> [arguments]")
        
        subcommand = args[0].lower()
        
        if subcommand == "play":
            # Play a sequence - needs a sequence name
            if len(args) < 2:
                raise ValueError("Usage: sequence play <sequence_name>")
            
            sequence_name = args[1]
            
            # Check if sequence name is in self.sequences
            if sequence_name not in self.sequences:
                available = ", ".join(self.sequences) if self.sequences else "none"
                raise ValueError(f"Sequence '{sequence_name}' not found. Available sequences: {available}")
            
            # Execute the sequence
            self.cycle_handler.cycle_trigger(sequence_name=sequence_name)
            return f"Playing sequence: {sequence_name}"
        
        elif subcommand == "stop":
            # Stop the current running sequence thread
            self.cycle_handler.cycle_stop()
            return "Stop signal sent to running sequence"
        
        elif subcommand == "validate":
            # Re-validate all sequence files
            return self.revalidate_sequences()
        
        elif subcommand == "upload":
            # Upload a new sequence file
            if len(args) < 3:
                raise ValueError("Usage: sequence upload <filename> <file_content>")
            
            # Pass remaining args to upload command
            return self.execute_upload_sequence_command(args[1:])
        
        else:
            raise ValueError(f"Unknown sequence subcommand: '{subcommand}'. Valid subcommands: play, play_thread, stop_thread, validate, upload")

    def sequence_start(self, sequence_name):
        file_path = os.path.join(self.sequenceFolder, sequence_name)
        self.read_sequence_file(file_path)

    def sequence_clean(self):
        logger.debug("Sequence clean")
        self.disable_start_button()

    def get_start_button_state(self):
        return self.start_button_enabled

    def get_state(self):
        return {
            "random_actions": self.get_random_actions_state(),
            "cycle_running": self.cycle_handler.get_cycle_state(),
            "start_button_enabled": self.get_start_button_state(),
            "sequences_validated": self.sequences_validated,
        }

    def get_sequence(self, sequence_name):
        if sequence_name == "play":
            file_path = os.path.join(self.sequenceFolder, self.play_file)
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

    def execute_upload_sequence_command(self, args):
        if args is None or len(args) < 2:
            raise ValueError("Usage: us <filename> <file_content>")
        
        filename = args[0]
        file_content = " ".join(args[1:])
        
        # Replace escaped newlines with actual newlines
        file_content = file_content.replace('\\n', '\n')

        return self.upload_sequence_file(filename, file_content)

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
