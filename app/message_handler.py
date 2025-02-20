# comm_logic.py
from dunebuggerlogging import logger


class MessageHandler:
    def __init__(self, websocket_client):
        self.websocket_client = websocket_client

    def process_message(self, message):
        message_type = message.get("type")
        if message_type == "request_initial_state":
            self.handle_request_state()
        elif message_type == "ping":
            self.handle_ping()
        else:
            logger.warning(f"Unknown message type: {message_type}")

    def handle_request_state(self):
        data = {
            "body": {"Grotta": "on", "Stella": "off"},
            "type": "state",
            "source": "controller",
            "destination": "client",
        }
        self.websocket_client.send_message(data)

    def handle_ping(self):
        data = {
            "body": "pong",
            "type": "ping",
            "source": "controller",
            "destination": "client",
        }
        self.websocket_client.send_message(data)

    def send_log(self, log_message):
        data = {
            "body": log_message,
            "type": "log",
            "source": "controller",
            "destination": "client",
        }
        self.websocket_client.send_message(data)
