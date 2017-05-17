import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from picoscope import ps5000a

from labonchip.Methods.HelperFunctions import sweeps_number, text_when_done


class Picoscope:
    def __init__(self):
        self.ps = ps5000a.PS5000a(connect=False)

    def openScope(self, bitRes=16, obsDuration=120e-3, sampleFreq=1E4):
        self.ps.open()

        # Set bit resolution
        self.ps.setResolution(str(bitRes))

        # Set trigger and channels
        self.ps.setSimpleTrigger(trigSrc="External", threshold_V=2.0, direction="Rising", timeout_ms=5000)
        self.ps.setChannel("A", coupling="DC", VRange=2.0, VOffset=-1.0, enabled=True, BWLimited=True)
        self.ps.setChannel("B", coupling="DC", VRange=5.0, VOffset=0, enabled=False)

        # Set capture duration (s) and sampling frequency (Hz)
        sampleInterval = 1.0 / sampleFreq
        self.res = self.ps.setSamplingInterval(sampleInterval, obsDuration)

        # Print final capture settings to command line
        print("Resolution =  %d Bit" % bitRes)
        print("Sampling frequency = %.3f MHz" % (1E-6 / self.res[0]))
        print("Sampling interval = %.f ns" % (self.res[0] * 1E9))
        print("Taking  samples = %d" % self.res[1])
        print("Maximum samples = %d" % self.res[2])

    def armMeasure(self):
        self.ps.runBlock()

    def measure(self):
        # print("Waiting for trigger")
        while not self.ps.isReady():
            time.sleep(0.001)
        # print("Sampling Done")
        return self.ps.getDataV("A")

    def closeScope(self):
        self.ps.close()

    def get_time(self, milli=True):
        """Return time array corresponding to measurement in ms. Set milli=False for time in seconds."""
        x = np.arange(self.res[1]) * self.res[0]
        # Convert to milliseconds
        if milli:
            x *= 1E3
        return x

    def plot(self, show=True, fit=True):
        self.armMeasure()
        y = self.measure()
        x = self.get_time()

        if fit:
            # Fit decay
            import photonics.photodiode as fl
            popt, perr = fl.fit_decay(x, y)
            fig = fl.plot_decay(x, y, fl.decay_fn, popt, log=False, norm=False, show=show)
        else:
            fig, ax = plt.subplots()
            ax.plot(x, y)
        return fig


def measure():
    from labonchip.Methods.Devices.Arduino import Arduino
    from labonchip.Methods.Devices.ITC4001 import ITC4001

    # How long to capture the decay for (ms) [same as picoscope]
    pulse_duration = 100E-3
    decay_time = 100E-3

    # Measurement Info Dictionary
    log = dict(measurementID=str(datetime.now().timestamp()),
               chip='T22',
               medium='Air'
               )

    # Directory to store data
    dataf = 'E:/Data/'

    # Make directory to store files
    import os
    directory = dataf + str(log['measurementID'])
    if not os.path.exists(directory):
        os.makedirs(directory + "/raw")
        os.makedirs(directory + "/Plots")
        os.makedirs(directory + "/Plots/Temp")

    # Setup devices
    laserDriver = ITC4001()
    laserDriver.setup_980nm_ld()
    laserDriver.set_ld_shape('PULS')
    log['pulse_width'] = pulse_duration
    laserDriver.set_qcw(period=(pulse_duration + decay_time), width=pulse_duration)

    arduino = Arduino()
    log['tempC'] = arduino.tempC
    log['humidity'] = arduino.humidity

    scope = Picoscope()
    scope.openScope(obsDuration=(pulse_duration + decay_time))
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Sweep over pump powers (A)
    for current in np.linspace(0.1, 0.5, num=11, endpoint=True):
        print('Measuring at {0:.2} A'.format(current))
        log["current"] = current  # Laser drive current(A)
        laserDriver.set_ld_current(current)
        laserDriver.turn_ld_on()
        time.sleep(3)
        log['optical power'] = laserDriver.get_optical_power()

        # Save plot of the decay
        fig = scope.plot(show=False, fit=False)
        fig.savefig(directory + '/Plots/Temp/current{0}.png'.format(current))
        plt.close(fig)  # close the figure

        sweeps_number(1000, log, scope, laserDriver, dataf=dataf, arduino=arduino, thermocouple=False)
        laserDriver.turn_ld_off()
        time.sleep(1)

    # Stop and close all instruments
    scope.closeScope()
    arduino.close()
    print('Finished measurement.')

    return log['measurementID']


if __name__ == "__main__":
    time.sleep(15 * 60)
    # Do measurement
    measurementID = measure()
    text_when_done()
    print("Finito!")
