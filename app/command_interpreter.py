import asyncio

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
        if command.startswith("#"):
            command_parts = command[1:].split()  # Remove "#" from the beginning
            return self.handle_gpio_command(command_parts)

        if command.startswith("sm"):
            message = command[2:].strip()
            return await self.handle_send_log(message)

        # Handle volume commands with parameters
        if command.startswith("mv ") or command.startswith("sv "):
            parts = command.split(" ", 1)
            cmd = parts[0]
            param = parts[1] if len(parts) > 1 else None
            if cmd == "mv":
                return self.handle_set_music_volume(param)
            elif cmd == "sv":
                return self.handle_set_sfx_volume(param)

        #todo: refactor to avoid duplication with dmx_handler
        if command.startswith("dmx "):
            parts = command.split()
            if len(parts) >= 4:
                try:
                    dmx_command = parts[1]
                    channel = int(parts[2])
                    scene_or_value = parts[3]
                    duration = 2.0  # default duration
                    
                    # Check for optional duration parameter
                    if len(parts) >= 5 and dmx_command in ["fade", "fade_dimmer"]:
                        try:
                            duration = float(parts[4])
                        except ValueError:
                            return f"Invalid duration value: {parts[4]}"
                    
                    return self.handle_dmx(dmx_command, channel, scene_or_value, duration)
                except Exception as e:
                    return f"Invalid DMX command: {e}"
            else:
                return "Usage: dmx <command> <channel> <scene_or_value> [duration]. Commands: set, fade, dimmer, fade_dimmer. Scenes: warm_white, cool_white, red, green, blue. Dimmer values: 0.0-1.0"

        if command in self.command_handlers:
            handler = self.command_handlers[command]["handler"]
            # Check if the handler is a coroutine function
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                return handler()
        else:
            return f"Unknown command {command}. Type ? or h for help"

    def load_command_handlers(self):
        self.command_handlers = {}
        for command, details in settings.command_handlers.items():
            self.command_handlers[command] = {"handler": getattr(self, details["handler"]), "description": details["description"]}

    def handle_load_configuration(self):
        settings.load_configuration()
        return "Configuration reloaded"

    def handle_enable_random_actions(self):
        self.sequence_handler.enable_random_actions()
        return "Random actions enabled"


    def handle_disable_random_actions(self):
        self.sequence_handler.disable_random_actions()
        return "Random actions disabled"

    def handle_gpio_command(self, command_parts):
        if len(command_parts) == 2 and (command_parts[1] == "on" or command_parts[1] == "off"):
            gpio = int(command_parts[0])
            # Warning: on GPIO the action is inverted: on = 0, off = 1
            gpio_value = 0 if command_parts[1] == "on" else 1
            self.gpio_handler.gpio_set_output(gpio, gpio_value)
            return f"GPIO {gpio} set to {command_parts[1]}"

    def handle_cycle_start(self):
        self.sequence_handler.cycle_trigger()
        #TODO: fix should not always print "Cycle started"
        return "Cycle started"

    def handle_cycle_stop(self):
        self.sequence_handler.cycle_stop()
        return "Stopping cycle"

    def handle_set_logger_debug(self):
        set_logger_level("dunebuggerLog", get_logging_level_from_name("DEBUG"))
        return "Logger level set to DEBUG"

    def handle_set_logger_info(self):
        set_logger_level("dunebuggerLog", get_logging_level_from_name("INFO"))
        return "Logger level set to INFO"

    def handle_set_logger_queuing(self):
        enable_queue_logging(self.mqueue_handler)
        return "Logger set to queue mode"

    def handle_disable_logger_queuing(self):
        disable_queue_logging()
        return "Logger queue mode disabled"

    def handle_set_standby_mode(self):
        self.sequence_handler.setStandByMode()
        return "Standby mode state set"

    def handle_set_off_mode(self):
        self.sequence_handler.setOffMode()
        return "Off mode state set"

    def handle_initialize_motor_limits(self):
        if settings.motorEnabled:
            self.sequence_handler.motor_handler.initMotorLimits()
            return "Initializing motor limits"
        else:
            return "Motor module is disabled"

    def handle_dmx(self, command=None, channel=None, scene_or_value=None, duration=2.0):
        if command is None or channel is None or scene_or_value is None:
            return "Usage: dmx <command> <channel> <scene_or_value> [duration]. Commands: set, fade, dimmer, fade_dimmer"
        
        # Validate command
        if command not in ["set", "fade", "dimmer", "fade_dimmer"]:
            return f"Invalid DMX command: {command}. Must be 'set', 'fade', 'dimmer', or 'fade_dimmer'"
        
        # Validate channel
        try:
            channel = int(channel)
            if channel < 1 or channel > 512:
                return f"DMX channel must be between 1 and 512, got: {channel}"
        except (ValueError, TypeError):
            return f"Invalid channel value: {channel}"
        
        # For dimmer commands, validate intensity value
        if command in ["dimmer", "fade_dimmer"]:
            try:
                intensity = float(scene_or_value)
                if not (0.0 <= intensity <= 1.0):
                    return f"DMX dimmer intensity must be between 0.0 and 1.0, got: {intensity}"
            except ValueError:
                return f"Invalid dimmer intensity value: {scene_or_value}"
        
        # Validate duration for fade commands
        if command in ["fade", "fade_dimmer"]:
            try:
                duration = float(duration)
                if duration < 0:
                    return f"Duration must be positive, got: {duration}"
            except (ValueError, TypeError):
                return f"Invalid duration value: {duration}"
        
        self.sequence_handler.execute_dmx_command(command, channel, scene_or_value, duration)
        
        if command in ["fade", "fade_dimmer"]:
            return f"DMX command '{command}' executed on channel {channel} with value '{scene_or_value}' over {duration}s"
        else:
            return f"DMX command '{command}' executed on channel {channel} with value '{scene_or_value}'"

    def handle_set_music_volume(self, volume=None):
        if volume is None:
            return "Usage: mv <volume> - where volume is a number between 0-100, 'n' for normal volume, or 'q' for quiet volume"

        try:
            if volume.lower() == "n":
                volume = settings.normalMusicVolume
                return f"Setting music volume to normal level ({volume})"
            elif volume.lower() == "q":
                volume = settings.quietMusicVol
                return f"Setting music volume to quiet level ({volume})"
            else:
                volume = int(volume)

            self.sequence_handler.audio_handler.set_music_volume(volume)
            return f"Music volume set to {volume}"
        except ValueError:
            return f"Invalid volume value: {volume}. Must be a number between 0-100, 'n', or 'q'."

    def handle_set_sfx_volume(self, volume=None):
        if volume is None:
            return "Usage: sv <volume> - where volume is a number between 0-100, 'n' for normal volume, or 'q' for quiet volume"

        try:
            if volume.lower() == "n":
                volume = settings.normalSfxVolume
                return f"Setting SFX volume to normal level ({volume})"
            elif volume.lower() == "q":
                volume = settings.quietSfxVol
                return f"Setting SFX volume to quiet level ({volume})"
            else:
                volume = int(volume)

            self.sequence_handler.audio_handler.set_sfx_volume(volume)
            return f"SFX volume set to {volume}"
        except ValueError:
            return f"Invalid volume value: {volume}. Must be a number between 0-100, 'n', or 'q'."

    def handle_enable_start_button(self):
        self.sequence_handler.enable_start_button()
        return "Start button enabled"

    def handle_disable_start_button(self):
        self.sequence_handler.disable_start_button()
        return "Start button disabled"

    async def handle_send_log(self, message):
        await self.mqueue_handler.dispatch_message(message, "log", "remote")
        return "Message sent"

    def handle_validate_sequences(self):
        if self.sequence_handler.revalidate_sequences():
            return "✅ All sequence files validated successfully"
        else:
            return "❌ Sequence validation failed - check logs for details"
