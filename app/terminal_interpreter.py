import readline
import os
import time
from dunebugger_settings import settings
import atexit
from dunebuggerlogging import logger, set_logger_level, get_logging_level_from_name
import motor
import threading
import traceback
from sequence import sequencesHandler
from gpio_handler import mygpio_handler

class TerminalInterpreter:
    def __init__(self):
        self.gpio_handler = mygpio_handler
        self.sequencesHandler = sequencesHandler

        history_path = "~/.python_history"
        self.enableHistory(history_path)
        atexit.register(self.save_history, history_path)
        self.stop_terminal_event = threading.Event()

        if settings.ON_RASPBERRY_PI: 
            self.help = f"I am a Raspberry. You can ask me to:\n\
                s: show gpio status\n\
                t: show dunebugger conf\n\
                l: reload dunebugger conf\n\
                sb: set standby state\n\
                esb: enable start button (add event detect)\n\
                dsb: disable start button (removes event detect)\n\
                mi: motor init\n\
                so: set off state\n\
                <#gpionum or label> on: set gpio status High (OUTPUT gpios only)\n\
                <#gpionum or label> off: set gpio status Low (OUTPUT gpios only)\n\
                er: enable random actions\n\
                dr: disable random actions\n\
                c: cycle start\n\
                cs: cycle stop (send stop signal)\n\
                ld: set logger verbosity to DEBUG\n\
                li: set logger verbosity to INFO\n\
                q: quit\n\
                ? or h: help\
                "
            self.show_gpio_status = self.gpio_handler.show_gpio_status
        else:
            self.help = f"I am not a Raspberry. You can ask me to:\n\
                s: show gpio status\n\
                t: show dunebugger conf\n\
                l: reload dunebugger conf\n\
                sb: set standby state\n\
                esb: enable start button (add event detect)\n\
                dsb: disable start button (removes event detect)\n\
                mi: motor init\n\
                so: set off state\n\
                <#gpionum or label> on: set gpio status High\n\
                <#gpionum or label> off: set gpio status Low\n\
                er: enable random actions\n\
                dr: disable random actions\n\
                c: cycle start\n\
                cs: cycle stop (send stop signal)\n\
                ld: set logger verbosity to DEBUG\n\
                li: set logger verbosity to INFO\n\
                q: quit\n\
                ? or h: help\
                "
            self.show_gpio_status = self.gpio_handler.GPIO.show_gpio_status

    def terminal_listen(self):
        # Start a separate thread for processing terminal input
        terminal_thread = threading.Thread(target=self.terminal_input_thread, daemon=True)
        terminal_thread.start()

        try:
            while not self.stop_terminal_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_terminal_event.set()
            logger.debug ("Stopping main thread...")
        except Exception as exc:
            traceback.print_exc()
            logger.critical ("Exception: "+str(exc)+". Exiting." )

    def terminal_input_thread(self):
        while not self.stop_terminal_event.is_set():
            try:
                # Wait for user input and process commands
                user_input = input("Enter command: ")
                self.process_terminal_input(user_input)
            except KeyboardInterrupt:
                self.stop_terminal_event.set()
                logger.debug ("Stopping terminal input thread...")

    def enableHistory(self, historyPath):
        history_file = os.path.expanduser(historyPath)
        if os.path.exists(history_file):
            readline.read_history_file(history_file)

    def save_history(self, historyPath):
        history_file = os.path.expanduser(historyPath)
        readline.write_history_file(history_file)

    def process_terminal_input(self, input_str):
        # Process commands received through the terminal
        command_strs = input_str.split(',')

        for command_str in command_strs:
            if command_str == "":
                continue

            elif command_str in {"h", "?"}:
                print(self.help)
                continue

            elif command_str == "s":
                self.show_gpio_status(self.gpio_handler)
                continue
            
            elif command_str == "t":
                settings.show_configuration()
                # Print state of random_actions_event
                random_actions_status =  "on" if sequencesHandler.get_random_actions_status() else "off"
                print(f"Random actions is now: {random_actions_status}")
                continue

            elif command_str == "l":
                settings.load_configuration()
                continue

            elif command_str == "quit":
                self.stop_terminal_event.set()
                continue

            elif command_str in {"er"}:
                if settings.randomActionsEnabled:
                    sequencesHandler.enable_random_actions()
                    print(f"Random actions enabled")
                else:
                    print(f"Random actions is disabled in the configuration")
                continue
            
            elif command_str in {"dr"}:
                sequencesHandler.disable_random_actions()
                print(f"Random actions disabled")
                continue

            elif command_str.startswith("#"):
                # Handle commands starting with "#"
                command_parts = command_str[1:].split()  # Remove "#" from the beginning
                if len(command_parts) == 2 and (command_parts[1] == "on" or command_parts[1] == "off"):
                    gpio = int(command_parts[0])
                    self.gpio_handler.gpio_set_output(gpio, command_parts[1])
                    continue
            
            elif command_str == "c":
                print(f"Cycle started")
                sequencesHandler.cycle_trigger()
                continue

            elif command_str == "cs":
                print(f"Stopping cycle")
                sequencesHandler.cycle_stop()
                continue
            
            elif command_str == "ld":
                set_logger_level("dunebuggerLog", get_logging_level_from_name("DEBUG"))
                continue

            elif command_str == "li":
                set_logger_level("dunebuggerLog",  get_logging_level_from_name("INFO"))
                continue

            elif command_str == "sb":
                self.sequencesHandler.setStandByMode()
                print("Standby mode state set")
                continue
            
            elif command_str == "so":
                self.sequencesHandler.setOffMode()
                print("Off mode state set")
                continue

            elif command_str == "mi":
                if (settings.motorEnabled):
                    print("Initializing motor limits")
                    motor.initMotorLimits()
                else:
                    print(f"Motor module is disabled")
                continue

            elif command_str == "esb":
                self.sequencesHandler.enable_start_button()
                print("Start button enabled")
                continue

            elif command_str == "dsb":
                self.sequencesHandler.disable_start_button()
                print("Start button disabled")
                continue

            else:
                # Handle other commands
                command_parts = command_str.split()
                if len(command_parts) == 2 and (command_parts[1] == "on" or command_parts[1] == "off"):
                    gpiomap = command_parts[0]
                    self.gpio_handler.gpio_set_output(gpiomap, command_parts[1])
                    continue

            print(f"Unkown command {command_str}")

terminal_interpreter = TerminalInterpreter()
