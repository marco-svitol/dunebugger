import threading
import random
from os import path

from dunebugger_settings import settings
from dunebugger_logging import logger


class RandomActions:
    """Handles random GPIO actions at random intervals."""
    
    def __init__(self, mygpio_handler, state_tracker):
        self.sequence_folder = path.join(path.dirname(path.abspath(__file__)), f"{settings.sequenceFolder}")
        self.random_elements_file = settings.randomElementsFile
        self.random_elements = []
        self.mygpio_handler = mygpio_handler
        self.state_tracker = state_tracker
        self.random_actions_event = None
        self.random_actions_thread = None
    
    def validate_random_elements_file(self):
        """Validate that all elements in the random elements file exist in GPIO maps."""
        try:
            file_path = path.join(self.sequence_folder, self.random_elements_file)
            with open(file_path) as file:
                raw_elements = [line.strip() for line in file if line.strip()]
            
            # Get available GPIO maps
            available_gpio_maps = set(self.mygpio_handler.gpio_map.keys())
            invalid_elements = []
            
            for element in raw_elements:
                # Remove any comments from the element
                element_clean = element.split('#')[0].split('//')[0].strip()
                if element_clean and element_clean not in available_gpio_maps:
                    invalid_elements.append(element_clean)
            
            if invalid_elements:
                error_msg = f"Invalid GPIO map(s) in random elements file '{self.random_elements_file}': {', '.join(invalid_elements)}. " \
                           f"Available GPIO maps: {', '.join(sorted(available_gpio_maps))}"
                raise ValueError(error_msg)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise RuntimeError(f"Error validating random elements file {file_path}: {e}")

    def random_sequence_from_file(self, file_name):
        try:
            file_path = path.join(self.sequence_folder, file_name)
            with open(file_path) as file:
                self.random_elements = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Error reading random elements file {file_path}: {e}")

    def random_action(self):
        try:
            rand_elem = random.choice(self.random_elements)
            random_action_message = self.mygpio_handler.execute_gpio_command([rand_elem, "toggle"])
            logger.debug(f"Random action executed: {rand_elem} - {random_action_message}")
        except IndexError:
            logger.error("No random elements loaded to perform random action")
        except Exception as e:
            logger.error(f"Error performing random action: {e}", exc_info=True)

    def random_actions(self):
        while not self.random_actions_event.is_set():
            self.random_actions_event.wait(timeout=random.uniform(settings.randomActionsMinSecs, settings.randomActionsMaxSecs))
            self.random_action()

    def execute_random_actions_command(self, args, dry_run=False):
        if args is None or len(args) == 0:
            raise ValueError("Usage: random_actions <enable|disable> : enable or disable random actions")
        
        action = args[0].lower()
        if action not in ["enable", "disable"]:
            raise ValueError("Invalid argument. Usage: random_actions <enable|disable> : enable or disable random actions")
        else:
            if dry_run:
                return True
            else:
                if action == "enable":
                    self.enable_random_actions()
                    return "Random actions enabled"
                elif action == "disable":
                    self.disable_random_actions()
                    return "Random actions disabled"
                else:
                    raise ValueError("Invalid argument. Usage: random_actions <enable|disable> : enable or disable random actions")

    def enable_random_actions(self):
        self.random_sequence_from_file(self.random_elements_file)
        self.random_actions_event = threading.Event()
        self.random_actions_event.clear()
        self.random_actions_thread = threading.Thread(name="_random_actions", target=self.random_actions, daemon=True)
        self.random_actions_thread.start()
        self.state_tracker.notify_update("random_actions")

    def disable_random_actions(self):
        if hasattr(self, "random_actions_event") and self.random_actions_event:
            self.random_actions_event.set()
            self.state_tracker.notify_update("random_actions")

    def get_random_actions_state(self):
        if hasattr(self, "random_actions_event") and self.random_actions_event:
            if not self.random_actions_event.is_set():
                return True
        return False
