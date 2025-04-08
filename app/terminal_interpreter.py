import readline
import os
import time
import atexit
import threading
import traceback

from dunebugger_settings import settings
from dunebugger_logging import logger, set_logger_level, get_logging_level_from_name, COLORS

class TerminalInterpreter:
    def __init__(self, mygpio_handler, sequence_handler, motor_handler):
        self.gpio_handler = mygpio_handler
        self.sequence_handler = sequence_handler
        self.motor_handler = motor_handler
        self.mqueue_handler = None
        history_path = "~/.python_history"
        self.enableHistory(history_path)
        atexit.register(self.save_history, history_path)
        self.stop_terminal_event = threading.Event()
        self.command_handlers = {}
        # Load command handlers from configuration file
        self.load_command_handlers()

        if not settings.ON_RASPBERRY_PI:
            help_insert_1 = "not "
            help_insert_2 = " (OUTPUT gpios only)"
        else:
            help_insert_1 = ""
            help_insert_2 = ""

        # Dynamically create the help string
        self.help = f"I am {help_insert_1}a Raspberry. You can ask me to:\n"
        for command, details in self.command_handlers.items():
            self.help += f"    {command}: {details['description']}\n"
        self.help += f"    <#gpionum or label> on: set gpio status High{help_insert_2}\n"
        self.help += f"    <#gpionum or label> off: set gpio status Low{help_insert_2}\n"
        self.show_gpio_status = self.gpio_handler.get_gpio_status

    def load_command_handlers(self):
        self.command_handlers = {}
        for command, details in settings.terminal_interpreter_command_handlers.items():
            self.command_handlers[command] = {
                "handler": getattr(self, details["handler"]),
                "description": details["description"],
            }

    def terminal_listen(self):
        # Start a separate thread for processing terminal input
        terminal_thread = threading.Thread(target=self.terminal_input_thread, daemon=True)
        terminal_thread.start()

        try:
            while not self.stop_terminal_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_terminal_event.set()
            logger.debug("Stopping main thread...")
        except Exception as exc:
            traceback.print_exc()
            logger.critical("Exception: " + str(exc) + ". Exiting.")

    def terminal_input_thread(self):
        while not self.stop_terminal_event.is_set():
            try:
                # Wait for user input and process commands
                user_input = input("Enter command: ")
                self.process_terminal_input(user_input)
            except KeyboardInterrupt:
                self.stop_terminal_event.set()
                logger.debug("Stopping terminal input thread...")

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
        gpio_status = self.show_gpio_status(self.gpio_handler)
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
        random_actions_status = "on" if self.sequence_handler.get_random_actions_state() else "off"
        print(f"Random actions is now: {random_actions_status}")

    def handle_load_configuration(self):
        settings.load_configuration()

    def handle_quit(self):
        self.stop_terminal_event.set()

    def handle_enable_random_actions(self):
        if settings.randomActionsEnabled:
            self.sequence_handler.enable_random_actions()
            print("Random actions enabled")
        else:
            print("Random actions is disabled in the configuration")

    def handle_disable_random_actions(self):
        self.sequence_handler.disable_random_actions()
        print("Random actions disabled")

    def handle_gpio_command(self, command_parts):
        if len(command_parts) == 2 and (command_parts[1] == "on" or command_parts[1] == "off"):
            gpio = int(command_parts[0])
            # Warning: on GPIO the action is inverted: on = 0, off = 1
            gpio_value = 0 if command_parts[1] == "on" else 1
            self.gpio_handler.gpio_set_output(gpio, gpio_value)

    def handle_cycle_start(self):
        print("Cycle started")
        self.sequence_handler.cycle_trigger()

    def handle_cycle_stop(self):
        print("Stopping cycle")
        self.sequence_handler.cycle_stop()

    def handle_set_logger_debug(self):
        set_logger_level("dunebuggerLog", get_logging_level_from_name("DEBUG"))

    def handle_set_logger_info(self):
        set_logger_level("dunebuggerLog", get_logging_level_from_name("INFO"))

    def handle_set_standby_mode(self):
        self.sequence_handler.setStandByMode()
        print("Standby mode state set")

    def handle_set_off_mode(self):
        self.sequence_handler.setOffMode()
        print("Off mode state set")

    def handle_initialize_motor_limits(self):
        if settings.motorEnabled:
            print("Initializing motor limits")
            self.motor_handler.initMotorLimits()
        else:
            print("Motor module is disabled")

    def handle_enable_start_button(self):
        self.sequence_handler.enable_start_button()
        print("Start button enabled")

    def handle_disable_start_button(self):
        self.sequence_handler.disable_start_button()
        print("Start button disabled")

    def handle_send_log(self, message):
        self.mqueue_handler.dispatch_message(message, "log")
        print("Message sent")

    def process_terminal_input(self, input_str):

        # Process commands received through the terminal
        command_strs = input_str.split(",")

        for command_str in command_strs:
            if command_str == "":
                continue

            if command_str.startswith("#"):
                command_parts = command_str[1:].split()  # Remove "#" from the beginning
                self.handle_gpio_command(command_parts)
                continue

            if command_str.startswith("sm"):
                message = command_str[2:].strip()
                self.handle_send_log(message)
                continue

            if command_str in self.command_handlers:
                self.command_handlers[command_str]["handler"]()
            else:
                print(f"Unknown command {command_str}. Type ? or h for help")
