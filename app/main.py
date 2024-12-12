#!/usr/bin/env python3
# coding: utf8
from terminal_interpreter import TerminalInterpreter

def main():

    terminalInterpreter = TerminalInterpreter()
    
    # Set standby mode
    terminalInterpreter.process_terminal_input("sb")
    # Initialize motors if module is enabled
    terminalInterpreter.process_terminal_input("mi")
    # Enable start button
    terminalInterpreter.process_terminal_input("esb")

    terminalInterpreter.terminal_listen()

if __name__ == "__main__":
    main()
