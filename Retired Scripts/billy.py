from __future__ import division
from __future__ import print_function

import matplotlib.pyplot as plt
import time
import numpy as np

from tqdm import *
from picoscope import ps5000a
from scipy.optimize import curve_fit


def func(t, a, tau, c):
    """ Mono-exponential fitting function. t is the time."""
    return a * np.exp(-t / tau) + c


def fit_decay(t, y):
    """ Function to fit the data,y, to the mono-exponential fitting."""
    # Guess initial fitting parameters
    a_guess = max(y) - min(y)
    tau_guess = 10
    c_guess =  min(y)
    # Fit curve
    popt, pcov = curve_fit(func, t, y, p0=(a_guess, tau_guess, c_guess))
    print('\nLifetime is: %.2f' % popt[1])
    return popt


class DecayMeasure:
    def __init__(self):
        self.ps = ps5000a.PS5000a(connect=False)

    def openScope(self):
        self.ps.open()

        bitRes = 16
        self.ps.setResolution(str(bitRes))
        print("Resolution =  %d Bit" % bitRes)

        self.ps.setChannel("A", coupling="DC", VRange=200.0E-3, VOffset=-150.0E-3, enabled=True)
        self.ps.setChannel("B", coupling="DC", VRange=5.0, VOffset=0, enabled=False)
        self.ps.setSimpleTrigger(trigSrc="External", threshold_V=2.0, direction="Falling", timeout_ms=5000)

        waveformDuration = 100E-3
        obsDuration = 1*waveformDuration

        sampleFreq = 1E6
        sampleInterval = 1.0 / sampleFreq

        res = self.ps.setSamplingInterval(sampleInterval, obsDuration)
        print("Sampling frequency = %.3f MHz" % (1E-6/res[0]))
        print("Sampling interval = %.f ns" % (res[0] * 1E9))
        print("Taking  samples = %d" % res[1])
        print("Maximum samples = %d" % res[2])
        self.res = res

    def closeScope(self):
        self.ps.close()

    def armMeasure(self):
        self.ps.runBlock()

    def measure(self):
        # print("Waiting for trigger")
        while not self.ps.isReady():
            time.sleep(0.01)
        # print("Sampling Done")

        return self.ps.getDataV("A")

    def accumulate(self, sweep_no):
        # Average datapoints
        x = 1
        if self.res[1] % x != 0:
            raise ValueError('Error with number of datapoints chosen to average.')
        # Create axis data
        dataTimeAxis = np.arange(self.res[1]) * self.res[0] * 1E3
        dataTimeAxis = dataTimeAxis.reshape(-1, x).mean(axis=1)
        data = np.zeros(len(dataTimeAxis))

        # Create plot
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.grid(True, which='major')
        plt.ylabel("Voltage (V)")
        plt.xlabel("Time (ms)")

        # Sum loops of data
        for i in tqdm(range(0, sweep_no)):
            # Collect data
            self.armMeasure()
            newData = self.measure()
            # Average over time
            newData = newData.reshape(-1, x).mean(axis=1)
            # Add to existing data
            data = data + newData

        # Remove first erronious data point
        dataTimeAxis = dataTimeAxis[1:]
        data = data[1:]

        # Calculate lifetime
        popt = fit_decay(dataTimeAxis, data)
        lifetime = str('%.2f' % popt[1])

        # Plot figure
        plt.plot(dataTimeAxis, data, label='Raw Data')
        plt.plot(dataTimeAxis, func(dataTimeAxis, *popt), 'r--', label=lifetime)
        plt.legend(loc="best")
        plt.savefig('accumulate3.png', dpi=500)
        plt.show()

        # Save data to .txt file
        chip = 'T2'
        pulse = '25ms'
        ref = 'noFocus'
        title = time.strftime("%d%m%y_%H%M%S", time.gmtime())
        fname = "Data\\" + chip + '_' + ref + '_' + pulse + '_' + title + '.txt'
        dataTimeAxis = np.array(dataTimeAxis)
        saveData = np.c_[dataTimeAxis, data]
        # np.savetxt(fname, saveData, newline='\r\n')


if __name__ == "__main__":
    # Accumulate a number of decays
    dm = DecayMeasure()
    dm.openScope()
    dm.accumulate(sweep_no=1)
    dm.closeScope()

