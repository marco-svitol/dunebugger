import readline
import os
import asyncio
import atexit
import traceback

from dunebugger_settings import settings
from dunebugger_logging import logger, COLORS


class TerminalInterpreter:
    def __init__(self, command_interpreter):
        
        history_path = "~/.python_history"
        self.enableHistory(history_path)
        atexit.register(self.save_history, history_path)
        self.command_interpreter = command_interpreter
        self.running = True

        if not settings.ON_RASPBERRY_PI:
            help_insert_1 = "not "
            help_insert_2 = " (OUTPUT gpios only)"
        else:
            help_insert_1 = ""
            help_insert_2 = ""

        # Dynamically create the help string
        self.help = f"I am {help_insert_1}a Raspberry. You can ask me to:\n"
        for command, details in self.command_interpreter.command_handlers.items():
            self.help += f"    {command}: {details['description']}\n"
        self.help += f"    <#gpionum or label> on: set gpio status High{help_insert_2}\n"
        self.help += f"    <#gpionum or label> off: set gpio status Low{help_insert_2}\n"
        self.help += f"    h, ?: show this help\n"
        self.help += f"    s: show GPIO status\n"
        self.help += f"    t: show dunebugger configuration\n"
        self.help += f"    q, quit, exit: exit the program\n"

    async def terminal_listen(self):
        # Create asyncio tasks for terminal input
        terminal_task = asyncio.create_task(self.terminal_input_loop())

        try:
            # Wait for tasks to complete
            await terminal_task
        except KeyboardInterrupt:
            self.running = False
            logger.debug("Stopping main task...")
        except Exception as exc:
            traceback.print_exc()
            logger.critical("Exception: " + str(exc) + ". Exiting.")
        finally:
            self.running = False

    async def terminal_input_loop(self):
        # Create an event loop for the stdin reader
        loop = asyncio.get_event_loop()

        while self.running:
            try:
                # Use run_in_executor to handle blocking input() in a non-blocking way
                print("Enter command: ", end="", flush=True)
                user_input = await loop.run_in_executor(None, input)

                if user_input:
                    # Split user_input by ";" to handle multiple commands
                    commands = [cmd.strip() for cmd in user_input.split(";") if cmd.strip()]
                    for command in commands:
                        if command.lower() in ["exit", "quit", "q"]:
                            self.running = False
                            print("Exiting terminal input loop...")
                            break
                        elif command.lower() in ["h", "?"]:
                            self.handle_help()
                        elif command.lower() in ["s"]:
                            self.handle_show_gpio_status()
                        elif command.lower() in ["t"]:
                            self.handle_show_configuration()
                        else:
                            command_reply_message = (await self.command_interpreter.process_command(command))
                            print(command_reply_message)
                else:
                    print(f"\r")
            except KeyboardInterrupt:
                self.running = False
                logger.debug("Stopping terminal input loop...")
            except asyncio.CancelledError:
                self.running = False
                break

    def enableHistory(self, historyPath):
        history_file = os.path.expanduser(historyPath)
        if os.path.exists(history_file):
            readline.read_history_file(history_file)

    def save_history(self, historyPath):
        history_file = os.path.expanduser(historyPath)
        readline.write_history_file(history_file)

    # terminal input command handlers
    def handle_help(self):
        print(self.help)

    def handle_show_gpio_status(self):
        gpio_status = self.command_interpreter.gpio_handler.get_gpio_status()
        print("Current GPIO Status:")
        for gpio_info in gpio_status:
            gpio = gpio_info["pin"]
            label = gpio_info["label"]
            mode = gpio_info["mode"]
            state = gpio_info["state"]
            switchstate = gpio_info["switch"]

            color = COLORS["RESET"]
            switchcolor = COLORS["RESET"]

            if mode == "INPUT":
                color = COLORS["BLUE"]
            elif mode == "OUTPUT":
                color = COLORS["RESET"]

            if state == "HIGH":
                switchcolor = COLORS["MAGENTA"]
            elif state == "LOW":
                switchcolor = COLORS["GREEN"]

            if state == "ERROR":
                color = COLORS["RED"]
                switchcolor = color

            print(
                f"{color}Pin {gpio} label: {label} \
mode: {mode}, state: {state}, switch: {COLORS['RESET']}{switchcolor}{switchstate}{COLORS['RESET']}"
            )

    def handle_show_configuration(self):
        settings.show_configuration()
        random_actions_status = "on" if self.command_interpreter.sequence_handler.get_random_actions_state() else "off"
        print(f"Random actions is now: {random_actions_status}")
        print(f"Music is now: {self.command_interpreter.sequence_handler.audio_handler.get_music_volume()}")
        print(f"SFX is now: {self.command_interpreter.sequence_handler.audio_handler.get_sfx_volume()}")