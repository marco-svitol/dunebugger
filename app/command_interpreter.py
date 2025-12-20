import asyncio

from schedule import logger

from dunebugger_settings import settings
from dunebugger_logging import set_logger_level, get_logging_level_from_name, enable_queue_logging, disable_queue_logging


class CommandInterpreter:
    def __init__(self, mygpio_handler, sequence_handler):
        self.gpio_handler = mygpio_handler
        self.sequence_handler = sequence_handler
        self.mqueue_handler = None
        self.command_handlers = {}
        self.load_command_handlers()

    async def process_command(self, command):
        # if command.startswith("sm"):
        #     message = command[2:].strip()
        #     return await self.handle_send_log(message)
        try:
            command_verb = command.split()[0]
            command_args = command.split()[1:]
            
            if command_verb in self.command_handlers:
                handler = self.command_handlers[command_verb]["handler"]
                # Check if the handler is a coroutine function
                if asyncio.iscoroutinefunction(handler):
                    if command_args:
                        result_message = await handler(command_args)
                    else:
                        result_message = await handler()
                else:
                    if command_args:
                        result_message = handler(command_args)
                    else:
                        result_message = handler()
                return {"success": True, "message": result_message, "level": "info"}
            else:
                return {"success": False, "message": f"Unknown command {command_verb}. Type ? or h for help", "level": "error"}
        except Exception as e:
            return {"success": False, "message": f"Command processing error: {str(e)}", "level": "error"}

    def load_command_handlers(self):
        self.command_handlers = {}
        for command, details in settings.command_handlers.items():
            self.command_handlers[command] = {"handler": getattr(self, details["handler"]), "description": details["description"]}

    def get_commands_list(self):
        return settings.command_handlers
    
    def get_states_list(self):
        return settings.states
    
    def handle_load_configuration(self, args=None):
        settings.load_configuration()
        return "Configuration reloaded"

    def handle_enable_random_actions(self, args=None):
        self.sequence_handler.enable_random_actions()
        return "Random actions enabled"

    def handle_disable_random_actions(self, args=None):
        self.sequence_handler.disable_random_actions()
        return "Random actions disabled"

    def handle_gpio_command(self, command_parts = []):
        if len(command_parts) != 2:
            raise ValueError("Incorrect number of arguments for gpio command") 
        elif (command_parts[0].isdigit() is False):
            raise ValueError("Invalid GPIO number")
        elif (command_parts[1] != "on" and command_parts[1] != "off"):
            raise ValueError("Invalid action for gpio command, must be 'on' or 'off'")
        gpio = int(command_parts[0])
        # Warning: on GPIO the action is inverted: on = 0, off = 1
        gpio_value = 0 if command_parts[1] == "on" else 1
        reply_message = self.gpio_handler.gpio_set_output(gpio, gpio_value)
        if reply_message is not None:
            raise ValueError(reply_message)
        #TODO: addedd Natale 2025. Improve
        self.mqueue_handler.dispatch_message("sw "+command_parts[0]+" "+command_parts[1], "dunebugger_set", "starter")
        return f"GPIO {gpio} set to {command_parts[1]}"

    def handle_cycle_start(self, args=None):
        if self.sequence_handler.get_cycle_state():
            return "Cycle is already running"
        self.sequence_handler.cycle_trigger()
        #TODO: fix should not always print "Cycle started"
        return "Cycle started"

    def handle_cycle_stop(self, args=None):
        self.sequence_handler.cycle_stop()
        return "Cycle stopped"

    def handle_set_logger_debug(self, args=None):
        set_logger_level("dunebuggerLog", get_logging_level_from_name("DEBUG"))
        return "Logger level set to DEBUG"

    def handle_set_logger_info(self, args=None):
        set_logger_level("dunebuggerLog", get_logging_level_from_name("INFO"))
        return "Logger level set to INFO"       
    
    def handle_set_logger_queuing(self, args=None):
        enable_queue_logging(self.mqueue_handler)
        return "Logger set to queue mode"

    def handle_disable_logger_queuing(self, args=None):
        disable_queue_logging()
        return "Logger queue mode disabled"

    def handle_set_standby_mode(self, args=None):
        self.sequence_handler.setStandByMode()
        return "Standby mode state set"

    def handle_set_off_mode(self, args=None):
        self.sequence_handler.setOffMode()
        return "Off mode state set"

    def handle_initialize_motor_limits(self, args=None):
        if settings.motorEnabled:
            self.sequence_handler.motor_handler.initMotorLimits()
            return "Initializing motor limits"
        else:
            return "Motor module is disabled"

    def handle_dmx(self, args=None):
            if not settings.dmxEnabled:
                return "DMX module is disabled"
            
            parsed_dmx_command_args = self.sequence_handler.dmx_handler.validate_dmx_command_args(args) 
            if isinstance(parsed_dmx_command_args, str):
                return parsed_dmx_command_args
            _, dmx_command, channel, scene_or_value, duration = parsed_dmx_command_args

            self.sequence_handler.execute_dmx_command(dmx_command, channel, scene_or_value, duration)
            
            if dmx_command in ["fade", "fade_dimmer"]:
                return f"DMX command '{dmx_command}' started on channel {channel} with value '{scene_or_value}' over {duration}s"
            else:
                return f"DMX command '{dmx_command}' executed on channel {channel} with value '{scene_or_value}'"

    def handle_set_music_volume(self, volume=None):
        if volume is None:
            raise ValueError("Usage: mv <volume> - where volume is a number between 0-100, 'n' for normal volume, or 'q' for quiet volume")

        if volume[0].lower() == "n":
            volume = settings.normalMusicVolume
            return f"Setting music volume to normal level ({volume})"
        elif volume[0].lower() == "q":
            volume = settings.quietMusicVolume
            return f"Setting music volume to quiet level ({volume})"
        
        if volume[0].isdigit() is False:
            raise ValueError("Volume must be a number between 0-100, 'n', or 'q'.")
        volume = int(volume[0])
        self.sequence_handler.audio_handler.set_music_volume(volume)
        return f"Music volume set to {volume}"

    def handle_set_sfx_volume(self, volume=None):
        if volume is None:
            return "Usage: sv <volume> - where volume is a number between 0-100, 'n' for normal volume, or 'q' for quiet volume"

        if volume[0].lower() == "n":
            volume = settings.normalSfxVolume
            return f"Setting SFX volume to normal level ({volume})"
        elif volume[0].lower() == "q":
            volume = settings.quietSfxVolume
            return f"Setting SFX volume to quiet level ({volume})"
        else:
            volume = int(volume[0])
        self.sequence_handler.audio_handler.set_sfx_volume(volume)
        return f"SFX volume set to {volume}"


    def handle_enable_start_button(self, args=None):
        self.sequence_handler.enable_start_button()
        return "Start button enabled"

    def handle_disable_start_button(self, args=None):
        self.sequence_handler.disable_start_button()
        return "Start button disabled"

    # async def handle_send_log(self, message):
    #     await self.mqueue_handler.dispatch_message(message, "log", "remote")
    #     return "Message sent"

    def handle_validate_sequences(self, args=None):
        if self.sequence_handler.revalidate_sequences():
            return "✅ All sequence files validated successfully"
        else:
            return "❌ Sequence validation failed - check logs for details"
    
    def handle_upload_sequence(self, args=None):
        """
        Handle upload sequence file command.
        Format: us <filename> <content>
        
        Args:
            args (list): Command arguments [filename, content]
        """
        if not args or len(args) < 2:
            return {"success": False, "message": "❌ Usage: us <filename> <content>\n"
                   "   filename: name of sequence file (must end with .seq)\n" 
                   "   content: sequence file content (use quotes for multi-line)"}
        
        filename = args[0]
        
        # Join all content arguments (in case content contains spaces)
        file_content = ' '.join(args[1:])
        
        # Replace escaped newlines with actual newlines
        file_content = file_content.replace('\\n', '\n')
        
        # Upload sequence file (always overwrites existing files)
        result = self.sequence_handler.upload_sequence_file(filename, file_content)
        
        # Ensure send_reply is always True in the response
        if result["success"] == True:
            result["level"] = "info"
        else:
            result["level"] = "error"
        
        return result
                