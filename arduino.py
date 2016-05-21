#!/usr/bin/python
import serial
import time
import re
import datetime

port = '/dev/tty.usbmodem621'

ard = serial.Serial(port, 9600, timeout=5)
time.sleep(2)  # wait for Arduino

i = 0
while i < 3:
    # Serial read temperature and humidity
    msg = ard.readline().decode('utf-8')
    # Extract data from string
    [temp, humidity] = re.findall("\d+\.\d+", msg)
    # Print
    timestamp = datetime.datetime.now()
    print("Measurement at {}".format(timestamp))
    print("\tTemperature: {}°C".format(temp))
    print("\tHumidity: {}%\n".format(humidity))

    i += 1
else:
    print("Exiting")
exit()
