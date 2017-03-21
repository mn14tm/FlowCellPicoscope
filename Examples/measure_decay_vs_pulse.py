import time
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from labonchip.Methods.Devices.Arduino import Arduino
from labonchip.Methods.Devices.Picoscope import Picoscope
from labonchip.Methods.Devices.ITC4001 import ITC4001
from labonchip.Methods.HelperFunctions import folder_analysis, plot_analysis, copy_data, sweeps_number, text_when_done

if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID=str(datetime.now().timestamp()),
               chip='T20',
               medium='Air'
               )

    # Make directory to store files
    import os
    directory = '../Data/' + str(log['measurementID']) + "/raw"
    if not os.path.exists(directory):
        os.makedirs(directory)
        os.makedirs('../Data/' + str(log['measurementID']) + "/Plots")

    # How long to capture the decay for (ms) [same as picoscope]
    decay_time = 120

    # Setup devices
    laserDriver = ITC4001()
    laserDriver.setup_980nm_ld()
    laserDriver.set_ld_shape('PULS')
    arduino = Arduino()
    scope = Picoscope()
    scope.openScope()

    # Update Experimental Log
    log['tempC'] = arduino.tempC
    log['humidity'] = arduino.humidity
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Sweep over pump powers (A)
    for current in np.arange(0.1, 0.6, step=0.1)[::-1]:
        print("Measuring at {0:3f}A power:".format(current))
        log["current"] = current  # Laser drive current(A)
        laserDriver.set_ld_current(current)

        # Sweep over pulse times (ms)
        for pulse_duration in [1, 5, 10, 20, 30, 40, 50, 70, 100][::-1]:
            print("Pulse width: {0:.2f}".format(pulse_duration))
            log['pulse_width'] = pulse_duration
            laserDriver.set_qcw(period=(pulse_duration+decay_time)*1e-3, width=pulse_duration*1e-3)

            laserDriver.turn_ld_on()
            time.sleep(3)
            log['optical power'] = laserDriver.get_optical_power()

            # Save plot of the decay
            fig = scope.plot(show=False)
            fig.savefig('../Data/' + str(log['measurementID']) + '/Plots/pulse_duration_{0}_current_{1}.png'.format(pulse_duration, current))
            plt.close(fig)  # close the figure

            sweeps_number(sweeps=100, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver, thermocouple=False)
            laserDriver.turn_ld_off()
            time.sleep(1)

    # Stop and close all instruments
    scope.closeScope()
    arduino.close()
    print('Finished measurement.')

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])
    try:
        text_when_done()
    except:
        pass
    print("Done! Now plotting...")
    plot_analysis(df, folder=log['measurementID'])
    # print("Copying files to network...")
    # copy_data(str(log['measurementID']))
    print("Finito!")
