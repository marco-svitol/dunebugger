import threading

class DunebuggerSettings:
    def __init__(self):
        self.ArduinoConnected = False
        self.cyclelength = 372
        self.bouncingTreshold = 0.10
        self.eastereggEnabled = False
        self.cycleoffset = 0
        self.cycle_thread_lock = threading.Lock()
        #Motors
        self.motor1Enabled = True
        self.motor2Enabled = True
        # debug
        self.cyclespeed = 1  # 0.2
        self.testdunebugger = False


settings = DunebuggerSettings()


