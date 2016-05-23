#!/usr/bin/python
import serial
import time
import re
from datetime import datetime


def main():
    """ Continually log the temperature and humidity from arduino until killed
     by another program. Data saved as text file with timestamps. """

    # port = '/dev/tty.usbmodem621'  # Mac
    port = 'COM3'  # Windows

    ard = serial.Serial(port, 19200, timeout=1)
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

        time.sleep(0.1)
        # exit()

def ambientLogger():
    """ Measure the temperature and humidity from arduino until killed
     by another program. Data saved as text file with timestamps.

     Code is from the http://tinyurl.com/zv5ssmv """

    # Setup serial monitor for arduino
    ser = serial.Serial(
        port='/dev/tty.usbmodem621',
        baudrate=19200,
        timeout=1
    )

    # # Wait for arduino buffer to fill up
    # time.sleep(0.1)

    buffer_string = ''

    buffer_string += ser.read(ser.inWaiting()).decode('utf-8')
    if '\n' in buffer_string:
        lines = buffer_string.split('\n')  # Guaranteed to have at least 2 entries
        last_received = lines[-2]
        # Extract data from string
        [temp, humidity] = re.findall("\d+\.\d+", last_received)

    return temp, humidity

if __name__ == "__main__":
    main()

    # for i in range(5):
    #     print(ambientLogger())
    #     time.sleep(1)
