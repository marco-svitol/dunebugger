from dunebugger_settings import settings
from dunebugger_logging import logger


class InitializationHandler:
    def __init__(self, command_interpreter):
        self.command_interpreter = command_interpreter

    async def execute_initialization_commands(self):
        """Execute initialization commands if they exist in settings."""
        if not hasattr(settings, 'initializationCommandsString'):
            logger.debug("No initializationCommandsString setting found, skipping initialization commands")
            return

        commands_string = settings.initializationCommandsString
        if not commands_string or commands_string.strip() == "":
            logger.debug("initializationCommandsString is empty, skipping initialization commands")
            return

        # Split commands by comma and process each one
        commands = [cmd.strip() for cmd in commands_string.split(",") if cmd.strip()]
        
        logger.info(f"Executing {len(commands)} initialization commands")
        
        for command in commands:
            logger.debug(f"Executing initialization command: {command}")
            try:
                await self.command_interpreter.process_command(command)
                logger.debug(f"Successfully executed command: {command}")
            except Exception as e:
                logger.error(f"Error executing initialization command '{command}': {e}")