import threading

class DunebuggerSettings:
    def __init__(self):
        self.ArduinoConnected = False
        self.cyclelength = 372
        self.bouncingTreshold = 0.10
        self.eastereggEnabled = False
        self.cycleoffset = 0
        self.cycle_thread_lock = threading.Lock()
        # debug
        self.cyclespeed = 1  # 0.2

settings = DunebuggerSettings()


