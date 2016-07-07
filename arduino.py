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
    requestData(ser)
    time.sleep(2)
    getAmbient(ser)
    getThermocouple(ser)


def requestData(ser):
    # Serial read temperature and humidity
    ser.write(b'SHT\n')
    # Serial read temperature and humidity
    ser.write(b'TK\n')


def getAmbient(ser):
    msg = ser.readline().decode('utf-8')  # Add [:-2]

    # Extract data from string
    [temp, humidity] = re.findall(r'\d+\.\d+', msg)

    print("\tTemperature: {}°C".format(temp))
    print("\tHumidity:    {}%\n".format(humidity))


def getThermocouple(ser):
    msg = ser.readline().decode('utf-8')  # Add [:-2]

    # Extract data from string
    [t_in, t_out] = re.findall(r'\d+\.\d+', msg)

    print("\tTemperature in:  {}°C".format(t_in))
    print("\tTemperature out: {}%\n".format(t_out))


if __name__ == "__main__":
    main()
