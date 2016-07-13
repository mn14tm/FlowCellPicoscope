#!/usr/bin/python
import serial
import re
import time
from datetime import datetime


def main():
    # Setup serial port to communicate with arduino
    ser = serial.Serial(
        port='COM3',
        baudrate=115200,
        timeout=1
    )

    # Allow arduino to fire up
    time.sleep(2)

    global tempC, humidity, t_in, t_out

    buffer_string = ''
    while True:
        buffer_string += ser.read(ser.inWaiting()).decode('utf-8')
        if '\n' in buffer_string:
            print(buffer_string)
            last_received = buffer_string[:-2]  # Remove \n and \r
            # Extract data from string
            [tempC, humidity, t_in, t_out] = re.findall(r"\d+\.\d+", last_received)
            buffer_string = ''
        # time.sleep(1)

if __name__ == "__main__":
    main()
