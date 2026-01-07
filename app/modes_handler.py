import atexit
import os
from os import path
import configparser

from dunebugger_settings import settings
from dunebugger_logging import logger


class ModesHandler:

    def __init__(self, state_tracker, command_interpreter):
        self.modesFolder = path.join(path.dirname(path.abspath(__file__)), f"{settings.modesFolder}")
        self.modes = {}
        self.modes_validated = False
        self.init_mode_file = None
        self.command_interpreter = command_interpreter
        self.state_tracker = state_tracker

    def initialize(self):
        try:
            self.set_modes_validated(self.validate_all_mode_files(self.modesFolder))
            logger.info(f"Modes initialized successfully from {self.modesFolder}")
            
            # Execute init_mode if one exists
            if self.init_mode_file:
                logger.info(f"Executing init mode: {self.init_mode_file}")
                file_path = os.path.join(self.modesFolder, self.init_mode_file)
                self.execute_mode_file(file_path)
        except Exception as e:
            logger.error(f"Initial modes validation error: {str(e)}")

    def revalidate_modes(self):
        """Re-validate all mode files. Useful after configuration changes."""
        logger.info("Re-validating mode files...")
        self.set_modes_validated(self.validate_all_mode_files(self.modesFolder))
        return f"All mode files validated successfully in directory: {self.modesFolder}"
    
    def set_modes_validated(self, validation_result: bool):
        if isinstance(validation_result, bool):
            if self.modes_validated != validation_result:
                self.modes_validated = validation_result
                self.state_tracker.notify_update("modes_validated")
        else:
            return validation_result

    def validate_single_mode_file(self, file_path):
        """Validate a single mode file for correct structure and syntax."""
        config = configparser.ConfigParser()
        
        try:
            config.read(file_path)
            
            # Check required sections
            if 'metadata' not in config:
                raise ValueError(f"Missing [metadata] section in {file_path}")
            if 'commands' not in config:
                raise ValueError(f"Missing [commands] section in {file_path}")
            
            # Check required metadata fields
            metadata = config['metadata']
            if 'name' not in metadata:
                raise ValueError(f"Missing 'name' in [metadata] section in {file_path}")
            if 'desc' not in metadata:
                raise ValueError(f"Missing 'desc' in [metadata] section in {file_path}")
            
            # Validate commands section by doing a dry run
            commands = config['commands']
            for command_line in commands.values():
                command_reply_message = self.command_interpreter.process_command(command_line, dry_run=True)
                if command_reply_message["level"] == "error":
                    raise RuntimeError(f"Invalid command in {file_path}: {command_line} - {command_reply_message['message']}")
            
            logger.debug(f"Mode validation passed for {file_path}")
            return True
            
        except configparser.Error as e:
            raise ValueError(f"Configuration parsing error in {file_path}: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found during mode validation: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Error validating mode file {file_path}: {e}")

    def validate_all_mode_files(self, directory):
        try:
            # Clear and populate self.modes with all .mod files
            self.modes = {}
            self.init_mode_file = None
            init_modes_found = []
            
            # Check if directory exists
            if not os.path.exists(directory):
                raise OSError(f"Modes directory does not exist: {directory}")
            
            # Validate all .mod files and check for init_mode
            for filename in os.listdir(directory):
                if filename.endswith(".mod"):
                    file_path = os.path.join(directory, filename)
                    logger.debug(f"Validating mode {file_path}")
                    self.validate_single_mode_file(file_path)
                    
                    # Check if this mode is marked as init_mode
                    config = configparser.ConfigParser()
                    config.read(file_path)
                    metadata = config['metadata']
                    mode_name_key = metadata.get('name', '').lower()
                    self.modes[mode_name_key] = filename
                    
                    init_mode = metadata.get('init_mode', 'False').lower() in ['true', '1', 'yes']
                    if init_mode:
                        init_modes_found.append(filename)
            
            # Validate that only one init_mode exists
            if len(init_modes_found) > 1:
                raise ValueError(f"Multiple init_mode files found: {', '.join(init_modes_found)}. Only one init_mode is allowed.")
            
            if init_modes_found:
                self.init_mode_file = init_modes_found[0]
                logger.info(f"Init mode set to: {self.init_mode_file}")
            else:
                logger.warning("No init_mode found. No mode will be executed during initialization.")
            
            if not self.modes:
                logger.warning(f"No mode files found in {directory}")
            
            return True
            
        except OSError as e:
            raise OSError(f"Error validating mode files in {directory}: {e}")

    def get_modes_list_with_metadata(self):
        """Retrieve list of modes with their metadata in JSON format."""
        modes_list = []
        
        try:
            for mode_filename in self.modes.values():
                file_path = os.path.join(self.modesFolder, mode_filename)
                config = configparser.ConfigParser()
                config.read(file_path)
                
                metadata = config['metadata']
                commands_dict = dict(config['commands'])
                
                modes_list.append({
                    "filename": mode_filename,
                    "name": metadata.get('name', '').lower(),
                    "desc": metadata.get('desc', ''),
                    "commands": commands_dict
                })
            
            return {"modes": modes_list}
            
        except Exception as e:
            logger.error(f"Error retrieving modes list with metadata: {e}")
            return {"error": str(e)}

    def execute_mode_command(self, args=None):
        """Execute mode commands: execute, list, validate, or upload.
        
        Args:
            args: List of arguments where first element is the subcommand
            
        Returns:
            Result message or raises ValueError/RuntimeError on errors
        """
        if args is None or len(args) == 0:
            raise ValueError("Usage: mode [execute <mode_name>|list|validate|upload <filename> <content>]")
        
        subcommand = args[0].lower()
        
        if subcommand == "execute":
            # Execute a mode - needs a mode name
            if len(args) < 2:
                raise ValueError("Usage: mode execute <mode_name>")
            
            mode_name = args[1]
            mode_name_lower = mode_name.lower()
            
            # Check if mode exists
            if mode_name_lower not in self.modes:
                available = ", ".join(self.modes.keys()) if self.modes else "none"
                raise ValueError(f"Mode '{mode_name}' not found. Available modes: {available}")
            
            # Execute the mode
            mode_filename = self.modes[mode_name_lower]
            file_path = os.path.join(self.modesFolder, mode_filename)
            return self.execute_mode_file(file_path)
        
        elif subcommand == "list":
            # List all available modes with metadata in human-readable format
            return self._format_modes_list_human_readable()
        
        elif subcommand == "validate":
            # Re-validate all mode files
            return self.revalidate_modes()
        
        elif subcommand == "upload":
            # Upload a new mode file
            if len(args) < 3:
                raise ValueError("Usage: mode upload <filename> <file_content>")
            
            # Pass remaining args to upload command
            return self.execute_upload_mode_command(args[1:])
        
        else:
            raise ValueError(f"Unknown mode subcommand: '{subcommand}'. Valid subcommands: execute, list, validate, upload")

    def _format_modes_list_human_readable(self):
        """Format modes list in human-readable format."""
        if not self.modes:
            return "No modes available."
        
        try:
            modes_list = []
            for mode_filename in self.modes.values():
                file_path = os.path.join(self.modesFolder, mode_filename)
                config = configparser.ConfigParser()
                config.read(file_path)
                
                metadata = config['metadata']
                commands_dict = dict(config['commands'])
                
                modes_list.append({
                    "name": metadata.get('name', ''),
                    "desc": metadata.get('desc', ''),
                    "filename": mode_filename,
                    "commands": commands_dict
                })
            
            output_lines = [f"Available Modes ({len(modes_list)}):"]
            output_lines.append("=" * 60)
            
            for mode in modes_list:
                output_lines.append(f"\n[{mode['name']}]")
                output_lines.append(f"  Description: {mode['desc']}")
                output_lines.append(f"  File: {mode['filename']}")
                output_lines.append(f"  Commands ({len(mode['commands'])})")
                for key, command in mode['commands'].items():
                    output_lines.append(f"    {key}: {command}")
            
            return "\n".join(output_lines)
            
        except Exception as e:
            logger.error(f"Error formatting modes list: {e}")
            return f"Error retrieving modes list: {str(e)}"

    def execute_mode_file(self, file_path):
        """Read and execute all commands from a mode file."""
        config = configparser.ConfigParser()
        
        try:
            config.read(file_path)
            commands = config['commands']
            mode_name = config['metadata'].get('name', os.path.basename(file_path))
            
            executed_commands = []
            
            for key, command_line in commands.items():
                command_reply_message = self.command_interpreter.process_command(command_line)
                
                if command_reply_message["level"] == "warning":
                    logger.warning(f"Warning executing command '{command_line}' in mode {mode_name}: {command_reply_message['message']}")
                elif command_reply_message["level"] == "error":
                    raise RuntimeError(f"Error executing command '{command_line}' in mode {mode_name}: {command_reply_message['message']}")
                else:
                    logger.debug(f"Executed command '{command_line}' in mode {mode_name}: {command_reply_message['message']}")
                    executed_commands.append(command_line)
            
            result_message = f"Mode '{mode_name}' executed successfully"
            
            logger.info(result_message)
            return result_message
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Mode file not found: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Error executing mode file {file_path}: {e}")

    def get_mode_details(self, mode_name):
        """Get detailed information about a specific mode including metadata and commands."""
        mode_name_lower = mode_name.lower()
        
        if mode_name_lower not in self.modes:
            return {"error": f"Mode '{mode_name}' not found"}
        
        mode_filename = self.modes[mode_name_lower]
        file_path = os.path.join(self.modesFolder, mode_filename)
        config = configparser.ConfigParser()
        
        try:
            config.read(file_path)
            
            metadata = config['metadata']
            commands_dict = dict(config['commands'])
            
            return {
                "mode_name": mode_name,
                "name": metadata.get('name', ''),
                "desc": metadata.get('desc', ''),
                "commands": commands_dict
            }
            
        except Exception as e:
            logger.error(f"Error reading mode file {file_path}: {e}")
            return {"error": str(e)}

    def execute_upload_mode_command(self, args):
        """Helper method to process mode upload command arguments.
        
        Args:
            args: List where first element is filename and rest is file content
            
        Returns:
            Upload result dictionary
        """
        if args is None or len(args) < 2:
            raise ValueError("Usage: mode upload <filename> <file_content>")
        
        filename = args[0]
        file_content = " ".join(args[1:])
        
        # Replace escaped newlines with actual newlines
        file_content = file_content.replace('\\n', '\n')

        return self.upload_mode_file(filename, file_content)

    def upload_mode_file(self, filename, file_content):
        """Upload a new mode file to the modes folder."""
        try:
            # Validate filename
            if not filename.endswith('.mod'):
                raise ValueError("Filename must end with .mod extension")
            
            # Sanitize filename to prevent path traversal attacks
            filename = os.path.basename(filename)
            if not filename or filename in ['', '.', '..']:
                raise ValueError("Invalid filename")
            
            # Set file path (will overwrite if exists)
            file_path = os.path.join(self.modesFolder, filename)
            
            # Validate file content by creating a temporary file and testing it
            import tempfile
            import shutil
            
            filename_prefix = f"{os.path.splitext(filename)[0]}_"
            with tempfile.NamedTemporaryFile(mode='w', prefix=filename_prefix, suffix='.mod', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            self.validate_single_mode_file(temp_file_path)

            backup_created = False
            backup_path = None
                
            # Create backup if file already exists
            if os.path.exists(file_path):
                backup_filename = f"{os.path.splitext(filename)[0]}.bak"
                backup_path = os.path.join(self.modesFolder, backup_filename)
                
                try:
                    shutil.copy2(file_path, backup_path)
                    backup_created = True
                    logger.info(f"Created backup of existing file: {backup_filename}")
                except Exception as e:
                    logger.warning(f"Failed to create backup for {filename}: {e}")
                    # Continue with upload even if backup fails
                
            # If validation passes, write the file to the modes folder
            with open(file_path, 'w') as f:
                f.write(file_content)
                
            logger.info(f"Successfully uploaded mode file: {filename}")
            
            success_message = f"Mode file {filename} uploaded successfully"

            self.state_tracker.notify_update("mode")

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

    def get_state(self):
        return {
            "modes_validated": self.modes_validated,
            "modes_count": len(self.modes),
            "available_modes": list(self.modes.keys())
        }
