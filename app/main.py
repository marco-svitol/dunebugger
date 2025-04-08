#!/usr/bin/env python3
from dunebugger_settings import settings
from class_factory import terminal_interpreter, mqueue_listener

def main():
    mqueue_listener.start_listener()
    
    # comment lines below to make a real server
    terminal_interpreter.process_terminal_input(settings.initializationCommandsString)
    terminal_interpreter.terminal_listen()

if __name__ == "__main__":
    main()
