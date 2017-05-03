import time

import matplotlib.pyplot as plt

from labonchip.Methods.Devices.Arduino import Arduino
from labonchip.Methods.Devices.ITC4001 import ITC4001
from labonchip.Methods.Devices.Picoscope import Picoscope
from labonchip.Methods.HelperFunctions import folder_analysis, plot_analysis, sweeps_number

if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID='T21_air_mirror',  # datetime.now().timestamp(),
               chip='T21',
               medium='Air',
               n=1.0)

    # Make directory to store files
    import os
    directory = '../Data/' + str(log['measurementID']) + "/raw"
    if not os.path.exists(directory):
        os.makedirs(directory)
        os.makedirs('../Data/' + str(log['measurementID']) + "/Plots")

    # Setup devices
    laserDriver = ITC4001()
    laserDriver.setup_980nm_ld()
    laserDriver.set_ld_shape('PULS')
    current = 0.5
    laserDriver.set_ld_current(current)
    laserDriver.set_qcw(period=170e-3, width=50e-3)
    arduino = Arduino()
    scope = Picoscope()
    scope.openScope()

    # Update Experimental Log
    log["current"] = current  # Laser drive current(A)
    log['tempC'] = arduino.tempC
    log['humidity'] = arduino.humidity
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Begin laser pulse
    laserDriver.turn_ld_on()
    time.sleep(5)  # Wait for laser driver to fire up
    log['optical power'] = laserDriver.get_optical_power()

    # Save plot of the decay
    fig = scope.plot(show=False)
    fig.savefig('../Data/' + str(log['measurementID']) + '/Plots/pulse_duration_50ms_current_500mA_canola.png')
    plt.close(fig)  # close the figure

    # Capture and fit single sweeps
    sweeps_number(sweeps=400, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
    # sweeps_time(mins=1, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
    laserDriver.turn_ld_off()

    # Stop and close all instruments
    scope.closeScope()
    laserDriver.turn_ld_off()
    arduino.close()
    print('Finished measurements.')

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])
    print("Done! Now plotting...")
    plot_analysis(df, folder=log['measurementID'])
    print("Finito!")
