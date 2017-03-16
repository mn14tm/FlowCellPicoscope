import os
import time
import pandas as pd
import numpy as np
from datetime import datetime
from labonchip.Methods.Devices.Arduino import Arduino
from labonchip.Methods.Devices.Picoscope import Picoscope
from labonchip.Methods.Devices.ITC4001 import ITC4001
from labonchip.Methods.HelperFunctions import folder_analysis, plot_analysis, copy_data, sweeps_number


if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID=str(datetime.now().timestamp()),
               chip='T2',
               medium='Air'
               )
    # How long to capture the decay for (ms) [same as picoscope]
    decay_time = 120

    # Setup devices
    laserDriver = ITC4001()
    arduino = Arduino()
    scope = Picoscope()
    scope.openScope()
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Sweep over pump powers (A)
    for current in np.arange(0.1, 0.6, step=0.1):
        print("Measuring at {}A power:".format(current))
        log["current"] = current  # Laser drive current(A)
        laserDriver.set_ld_current(current)

        # Sweep over pulse times (ms)
        for pulse_duration in [1, 5, 10, 20, 30, 40, 50, 70, 100]:
            laserDriver.set_qcw(period=(pulse_duration+decay_time)*1e-3, width=pulse_duration*1e-3)

            laserDriver.turn_ld_on()
            arduino.request_data()
            time.sleep(5)
            arduino.get_data()
            log['tempC'] = arduino.tempC
            log['humidity'] = arduino.humidity
            log['optical power'] = laserDriver.get_optical_power()

            sweeps_number(sweeps=500, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver, thermocouple=False)
            laserDriver.turn_ld_off()
            time.sleep(1)

    # Stop and close all instruments
    scope.closeScope()
    print('Finished measurement.')

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])
    print("Done! Now plotting...")
    plot_analysis(df, folder=log['measurementID'])
    print("Copying files to network...")
    copy_data(str(log['measurementID']))
    print("Finito!")
