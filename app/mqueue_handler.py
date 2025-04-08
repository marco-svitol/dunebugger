import time
import threading
import json
from dunebugger_logging import logger
from dunebugger_settings import settings


class MessagingQueueHandler:
    """Class to handle messaging queue operations."""

    def __init__(self, state_tracker, sequence_handler, mygpio_handler, terminal_interpreter):
        self.mqueue_sender = None
        self.state_tracker = state_tracker
        self.sequence_handler = sequence_handler
        self.mygpio_handler = mygpio_handler
        self.terminal_interpreter = terminal_interpreter
        self.check_interval = int(settings.mQueueStateCheckIntervalSecs)
        self.monitor_thread = threading.Thread(target=self._monitor_states, daemon=True)
        
    def process_message(self, message):
        message_type = message.get("type")
        if message_type == "request_gpio_state":
            self.handle_request_gpio_state()
        elif message_type == "request_sequence_state":
            self.handle_request_sequence_state()
        elif message_type == "request_sequence":
            sequence = message.get("body")
            self.handle_request_sequence(sequence)
        elif message_type == "command":
            command = message.get("body")
            self.terminal_interpreter.process_terminal_input(command)
        else:
            logger.warning(f"Unknown message type: {message_type}")

    def handle_request_gpio_state(self,):
        self.dispatch_message(
            self.mygpio_handler.get_gpio_status(),
            "gpio_state"
        )
    
    def handle_request_sequence_state(self):
        self.dispatch_message(
            self.sequence_handler.get_state(),
            "sequence_state"
        )
    
    def handle_request_playing_time(self):
        self.dispatch_message(
            self.sequence_handler.get_playing_time(),
            "playing_time"
        )
    
    def handle_request_sequence(self, sequence):
        self.dispatch_message(
            self.sequence_handler.get_sequence(sequence),
            "sequence"
        )
    
    def dispatch_message(self, message_body, response_type):
        message = {
            "body": message_body,
            "type": response_type,
            "source": "dunebugger-core",
            "destination": "dunebugger-remote",
        }
        self.mqueue_sender.send(message)
    
    def _monitor_states(self):
        """
        Monitor the state tracker for changes and react accordingly.
        """
        while True:
            if self.state_tracker.has_changes():
                changed_states = self.state_tracker.get_changes()
                for state in changed_states:
                    if state == "gpios":
                        # React to GPIO state changes
                        self.handle_request_gpio_state()
                    elif state in ["random_actions", "cycle_start_stop", "start_button"]:
                        # Handle random actions state change
                        self.handle_request_sequence_state()
                    elif state == "playing_time":
                        # Handle playing time changes
                        self.handle_request_playing_time()
                    elif state == "config":
                        # Handle configuration changes
                        logger.info("Configuration changed. Reloading settings...")
                # Reset the state tracker after handling changes
                self.state_tracker.reset_changes()
            time.sleep(self.check_interval)
    
