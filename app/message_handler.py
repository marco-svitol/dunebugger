import threading
import time
from dunebuggerlogging import logger
from gpio_handler import mygpio_handler
from dunebugger_settings import settings

class MessageHandler:
    def __init__(self):
        """
        Initialize the MessageHandler.

        Parameters:
        - state_tracker (StateTracker): The state tracker instance to monitor.
        - check_interval (int): The interval (in seconds) to check for state changes.
        """
        self.websocket_client = None
        self.pipe_listener = None
        self.state_tracker = None
        self.sequence_handler = None
        self.check_interval = int(settings.stateCheckIntervalSecs)
        self.monitor_thread = threading.Thread(target=self._monitor_states, daemon=True)

    def process_message(self, message):
        message_type = message.get("type")
        connection_id = message.get("connectionId")
        if message_type == "request_gpio_state":
            self.handle_request_gpio_state(connection_id)
        if message_type == "request_sequence_state":
            self.handle_request_sequence_state(connection_id)
        elif message_type == "ping":
            self.handle_ping(connection_id)
        elif message_type == "command":
            command = message.get("body")
            self.pipe_listener.pipe_send(command)
        else:
            logger.warning(f"Unknown message type: {message_type}")

    def handle_request_gpio_state(self, connection_id = "broadcast"):
        self.dispatch_message(
            mygpio_handler.get_gpio_status(),
            "gpio_state",
            connection_id)

    def handle_request_sequence_state(self, connection_id = "broadcast"):
        self.dispatch_message(
            self.sequence_handler.get_state(),
            "sequence_state",
            connection_id
        )

    def dispatch_message(self, message_body, response_type, connection_id = "broadcast"):
        data = {
            "body": message_body,
            "type": response_type,
            "source": "controller",
            "destination": connection_id,
        }
        self.websocket_client.send_message(data)

    def handle_ping(self, connection_id = "broadcast"):
        data = {
            "body": "pong",
            "type": "ping",
            "source": "controller",
            "destination": connection_id,
        }
        self.websocket_client.send_message(data)

    def send_log(self, log_message):
        data = {
            "body": log_message,
            "type": "log",
            "source": "controller"
        }
        self.websocket_client.send_message(data)

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
                    elif state in ["random_actions", "cycle_start_stop", "broadcast", "start_button"]:
                        # Handle random actions state change
                        self.handle_request_sequence_state()
                    elif state == "config":
                        # Handle configuration changes
                        logger.info("Configuration changed. Reloading settings...")
                # Reset the state tracker after handling changes
                self.state_tracker.reset_changes()
            time.sleep(self.check_interval)