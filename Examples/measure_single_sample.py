import time
import numpy as np

from LabOnChip.Devices.ITC4001 import ITC4001
from LabOnChip.Devices.Picoscope import Picoscope
from LabOnChip.Devices.Arduino import Arduino
from LabOnChip.HelperFunctions import folder_analysis, plot_analysis, dilution, sweeps_time, sweeps_number, copy_data
from datetime import datetime

if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID='T2_refractive_index_liquids4',  # datetime.now().timestamp(),
               chip='T2',
               medium='IPA',
               n=1.37)

    # Setup laser diode driver
    log["current"] = 0.5  # Laser drive current(A)
    laserDriver = ITC4001()
    laserDriver.set_ld_current(log["current"])
    laserDriver.turn_ld_on()
    log['optical power'] = laserDriver.get_optical_power()

    # Setup picoscope for logging
    scope = Picoscope()
    scope.openScope()
    scope.show_signal()  # Show a single sweep with the fit
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]
    laserDriver.turn_ld_off()

    # Setup Arduino
    arduino = Arduino()
    log['t_in'] = arduino.t_in
    log['t_out'] = arduino.t_out
    log['tempC'] = arduino.tempC
    log['humidity'] = arduino.humidity

    # Sweep over various pump powers
    for current in [0.5, 0.4, 0.3, 0.2, 0.1]:
        log["current"] = current  # Laser drive current(A)
        laserDriver.set_ld_current(log["current"])
        laserDriver.turn_ld_on()
        time.sleep(10)  # Wait for laser driver to fire up
        log['optical power'] = laserDriver.get_optical_power()

        # Capture and fit single sweeps
        sweeps_number(sweeps=400, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
        # sweeps_time(mins=1, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
        laserDriver.turn_ld_off()

    # Stop and close all instruments
    scope.closeScope()
    laserDriver.turn_ld_off()
    print('Finished measurements.')

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])
    print("Done! Now plotting...")
    plot_analysis(df, folder=log['measurementID'])
    print("Finito!")
