from dunebugger_settings import settings
from dunebugger_logging import execute_logger_command


class CommandInterpreter:
    def __init__(self, mygpio_handler, dmx_handler, motor_handler, audio_handler, cycle_handler):
        self.gpio_handler = mygpio_handler
        self.cycle_handler = cycle_handler
        self.dmx_handler = dmx_handler
        self.motor_handler = motor_handler
        self.audio_handler = audio_handler
        self.sequence_handler = None  # Will be set after SequencesHandler is created
        self.mqueue_handler = None # Will be set after MessagingQueueHandler is created
        self.command_handlers = {}
        self.load_command_handlers()

    def process_command(self, command, dry_run=None):
        try:
            command_verb = command.split()[0]
            command_args = command.split()[1:] if len(command.split()) > 1 else None
            
            if command_verb in self.command_handlers:
                handler = self.command_handlers[command_verb]["handler"]
                if dry_run is None:
                    result_message = handler(command_args)
                else:
                    result_message = handler(command_args, dry_run=dry_run)
                
                # Check if result_message is already a dict with the expected structure
                if isinstance(result_message, dict) and "success" in result_message and "message" in result_message:
                    return result_message
                else:
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
    
    def handle_load_configuration(self, args=None):
        settings.load_configuration()
        return "Configuration reloaded"

    # Below handlers can be used in dunebugger programs
    def handle_gpio_command(self, args=None, dry_run=False):
        return self.gpio_handler.execute_gpio_command(args, dry_run=dry_run)

    def handle_dmx(self, args=None, dry_run=False):
        return self.dmx_handler.execute_dmx_command(args, dry_run=dry_run)

    def handle_motor(self, args=None, dry_run=False):
        return self.motor_handler.execute_motor_command(args, dry_run=dry_run)

    def handle_start_button(self, args=None, dry_run=False):
        return self.cycle_handler.execute_start_button_command(args, dry_run=dry_run)

    def handle_audio(self, args=None, dry_run=False):
        return self.audio_handler.execute_audio_command(args, dry_run=dry_run)

    def handle_random_actions(self, args=None, dry_run=False):
        return self.sequence_handler.execute_random_actions_command(args, dry_run=dry_run)
    
    # Below handlers can be used only in dunebugger mqueue calls or dunebugger CLI
    def handle_logger(self, args=None):
        return execute_logger_command(args, self.mqueue_handler)
    
    def handle_sequence(self, args=None):
        return self.sequence_handler.execute_sequence_command(args)
                