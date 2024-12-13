#!/usr/bin/env python3
# coding: utf8
from terminal_interpreter import terminal_interpreter
from pipe_handler import pipe_listener

def main():
    pipe_listener.pipe_listen()
    pipe_listener.pipe_send("sb\nmi\nesb\ner\n")
    terminal_interpreter.terminal_listen()

if __name__ == "__main__":
    main()
