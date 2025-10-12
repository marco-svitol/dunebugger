import signal
import os
import sys

sigint_received = False


def sigint_handler(signum, frame):
    global sigint_received
    sigint_received = True
    sys.exit(0)


def dunequit():
    global sigint_received
    sigint_received = True
    # Get the process ID (PID) of the current process
    pid = os.getpid()
    # Send the SIGINT signal (equivalent to Ctrl+C)
    os.kill(pid, signal.SIGINT)


signal.signal(signal.SIGINT, sigint_handler)
