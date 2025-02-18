#!/usr/bin/env python3
# coding: utf8
from dunebugger_settings import settings
from terminal_interpreter import terminal_interpreter
from pipe_handler import pipe_listener
from dunebugger_websocket import websocket_listener

def main():
    pipe_listener.pipe_listen()
    websocket_listener.start()
    #TODO: comment lines below to make a real server
    pipe_listener.pipe_send(settings.initializationCommandsString)
    terminal_interpreter.terminal_listen()
    
if __name__ == "__main__":
    main()
