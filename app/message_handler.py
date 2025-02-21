from dunebuggerlogging import logger
class MessageHandler:
    def __init__(self):
        self.websocket_client = None
        self.pipe_listener = None

    def process_message(self, message):
        message_type = message.get("type")
        if message_type == "request_initial_state":
            self.handle_request_state()
        elif message_type == "ping":
            self.handle_ping()
        elif message_type == "command":
            command = message.get("body")
            self.pipe_listener.pipe_send(command)
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
