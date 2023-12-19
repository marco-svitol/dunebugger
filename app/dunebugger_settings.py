import threading

class DunebuggerSettings:
    def __init__(self):
        self.ArduinoConnected = False
        self.cyclelength = 372
        self.bouncingTreshold = 0.15
        self.eastereggEnabled = False
        self.cycleoffset = 0
        self.cycle_thread_lock = threading.Lock()
        self.randomActionsEnabled = False
        self.randomActionsMinSecs = 5
        self.randomActionsMaxSecs = 12
        #Motors
        self.motor1Enabled = True
        self.motor2Enabled = True
        self.motor1Freq = 5000
        self.motor2Freq = 5000
        # debug
        self.cyclespeed = 1  # 0.2
        self.testdunebugger = True


settings = DunebuggerSettings()


