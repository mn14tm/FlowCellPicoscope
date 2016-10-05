import time
import os
from tqdm import tqdm
import pandas as pd
import winsound
from LabOnChip.HelperFunctions import folder_analysis, plot_analysis, copy_data
from LabOnChip.Devices.ITC4001 import ITC4001
from LabOnChip.Devices.Picoscope import Picoscope
from LabOnChip.Devices.Arduino import Arduino
from datetime import datetime


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
               chip='T26',
               medium='Reflectance Standards'
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
    for reflectance in [99, 80, 60, 40, 20, 10, 5, 2, 0]:
        print("Place reflectance {} onto chip (0 is air):".format(reflectance))
        time.sleep(15)
        print("Measuring...")

        # Update concentration to save to data files
        log['concentration'] = reflectance

        # Sweep over various pump powers
        for current in [0.5, 0.4, 0.3, 0.2, 0.1]:
            log["current"] = current  # Laser drive current(A)
            laserDriver.set_ld_current(log["current"])
            laserDriver.turn_ld_on()
            time.sleep(5)  # Wait for laser driver to fire up
            log['optical power'] = laserDriver.get_optical_power()

            if current == 0.5:
                scope.show_signal()  # Show a single sweep with the fit

            # Capture and fit single sweeps
            sweeps_number(sweeps=500, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
            laserDriver.turn_ld_off()
            time.sleep(1)
        try:
            winsound.Beep(500, 1000)
        except:
            pass
        print("Measurement finished")

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
