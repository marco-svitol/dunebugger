import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

def button_callback(channel):
        global cou
        cou+=1
        print("Button was pushed on channel "+str(channel)+" call n."+str(cou))

cou = 0
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BCM) # Use physical pin numbering

GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)

GPIO.add_event_detect(6,GPIO.RISING,callback=button_callback,bouncetime=600) # Setup event on pin 10 rising edge

message = input("Press enter to quit\n\n") # Run until someone presses enter
GPIO.cleanup() # Clean up
