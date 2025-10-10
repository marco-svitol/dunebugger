class PWMHandler:
    def __init__(self, GPIO, GPIOnum, frequency=5000, duty_cycle=100):
        self.GPIOnum = GPIOnum
        self.frequency = frequency
        self.duty_cycle = duty_cycle

        self.pwm = GPIO.PWM(self.GPIOnum, self.frequency)
        self.pwm.start(self.duty_cycle)

    def set_duty_cycle(self, duty_cycle):
        self.duty_cycle = duty_cycle
        self.pwm.ChangeDutyCycle(self.duty_cycle)

    def cleanup(self):
        self.pwm.stop()
