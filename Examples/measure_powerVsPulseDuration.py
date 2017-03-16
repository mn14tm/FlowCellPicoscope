import os
import time
import winsound
import pandas as pd
import numpy as np

from tqdm import tqdm
from datetime import datetime
from labonchip.Methods.Devices.Arduino import Arduino
from labonchip.Methods.Devices.Picoscope import Picoscope
from labonchip.Methods.Devices.ITC4001 import ITC4001
from labonchip.Methods.HelperFunctions import folder_analysis, plot_analysis, copy_data


def sweeps_number(sweeps, log, arduino, scope, laserDriver):
    """ Measure and save single sweeps for a given number of sweeps. """
    log['sweeps'] = sweeps

    # Make directory to store files
    directory = "../Data/" + str(log['measurementID']) + "/raw"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Collect and save data for each sweep
    start = time.time()
    for i in tqdm(range(sweeps)):
        log['sweep_no'] = i + 1

        if time.time() - start > 3:
            arduino.get_data()
            log['tempC'] = arduino.tempC
            log['humidity'] = arduino.humidity
            arduino.request_data()
            start = time.time()
            # Update laser measured optical power (by photodiode internal)
            log['optical power'] = laserDriver.get_optical_power()

        # Collect data from picoscope (detector)
        scope.armMeasure()
        log['datetime'] = datetime.now()
        data = scope.measure()

        fname = directory + "/" + str(log['datetime'].timestamp()) + ".h5"
        storeRaw = pd.HDFStore(fname)
        storeRaw.put('log/', pd.DataFrame(log, index=[0]))

        rawData = pd.Series(data)
        storeRaw.put('data/', rawData)
        storeRaw.close()

if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID=str(datetime.now().timestamp()),
               chip='T2',
               medium='Air'
               )

    # Setup laser diode driver
    laserDriver = ITC4001()

    # Setup picoscope for logging
    scope = Picoscope()
    scope.openScope()
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Setup Arduino
    arduino = Arduino()
    log['tempC'] = arduino.tempC
    log['humidity'] = arduino.humidity

    # Set Flow Rate to desired dilution (ml/min)
    for current in np.arange(0.1, 0.6, step=0.1):
        print("Measuring at {}A power:".format(current))
        log["current"] = current  # Laser drive current(A)
        laserDriver.set_ld_current(log["current"])

        # Sweep over various pump powers
        for pulse_duration in [1, 5, 10, 20, 30, 40, 50, 70, 100]:
            # Capture and fit single sweeps
            laserDriver.turn_ld_on()
            time.sleep(5)  # Wait for laser driver to fire up
            log['optical power'] = laserDriver.get_optical_power()
            sweeps_number(sweeps=500, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
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
