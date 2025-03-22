#!/usr/bin/env python3
from dunebugger_settings import settings
from class_factory import websocket_client, terminal_interpreter, pipe_listener

def main():
    pipe_listener.pipe_listen()
    if settings.remoteEnabled == True:
        websocket_client.start()

    # comment lines below to make a real server
    pipe_listener.pipe_send(settings.initializationCommandsString)
    terminal_interpreter.terminal_listen()

if __name__ == "__main__":
    main()
