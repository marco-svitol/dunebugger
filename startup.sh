#!/bin/bash
tmux new -d -s cycle -c './app' 'python ./supervisor/switchonoff.py'
