import os
from dunebugger_auth import AuthClient
from dunebugger_websocket import WebPubSubListener
from message_handler import MessageHandler
from terminal_interpreter import TerminalInterpreter
from pipe_handler import PipeListener
from state_tracker import state_tracker
from sequence import sequencesHandler
from dunebugger_settings import settings

auth_client = AuthClient(
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    username=os.getenv("AUTH0_USERNAME"),
    password=os.getenv("AUTH0_PASSWORD"),
)

websocket_client = WebPubSubListener()
message_handler = MessageHandler()
terminal_interpreter = TerminalInterpreter()
pipe_listener = PipeListener()
sequence_handler = sequencesHandler

message_handler.websocket_client = websocket_client
message_handler.pipe_listener = pipe_listener
message_handler.state_tracker = state_tracker
message_handler.sequence_handler = sequence_handler
websocket_client.auth_client = auth_client
websocket_client.message_handler = message_handler
terminal_interpreter.websocket_client = websocket_client
pipe_listener.terminal_interpreter = terminal_interpreter

if settings.remoteEnabled == True: 
    message_handler.monitor_thread.start()