#!/bin/bash
tmux new -d -s cycle -c './app' 'python ./app/supervisor/switchonoff.py'