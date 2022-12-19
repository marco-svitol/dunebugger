BCM = 1
OUT = 1
IN = 1
HIGH = 1
LOW = 1
PUD_DOWN = 1
RISING = 1

def output(gpio, bit):
    return 1

def input (channel):
    return 1

def setmode (gpio):
    return 1

def setup (gpio, inout, initial=HIGH, pull_up_down=PUD_DOWN):
    return 1

def add_event_detect(gpio, updown, callback, bouncetime):
    return 1

def remove_event_detect(gpio):
    return 1

def cleanup():
    return 1
    
def setwarnings(enabled):
    return 0
