#!/usr/bin/python
import serial
import time
import re
from datetime import datetime


def main():
    """ Continually log the temperature and humidity from arduino until killed
     by another program. Data saved as text file with timestamps. """

    port = '/dev/tty.usbmodem621'

    ard = serial.Serial(port, 9600, timeout=5)
    time.sleep(2)  # wait for Arduino startup

    while True:
        # Serial read temperature and humidity
        msg = ard.readline().decode('utf-8')

        # Extract data from string
        [temp, humidity] = re.findall("\d+\.\d+", msg)
        # Print
        timestamp = datetime.now()
        print("Measurement at {}".format(timestamp))
        print("\tTemperature: {}°C".format(temp))
        print("\tHumidity:    {}%\n".format(humidity))
        # exit()

if __name__ == "__main__":
    main()
