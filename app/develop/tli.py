import serial
ser = serial.Serial('/dev/ttyUSB0', 9600)
while True :
    try:
        state=ser.readline()
        print(state)
    except:
        pass
