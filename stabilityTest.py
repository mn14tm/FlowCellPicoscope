from __future__ import division
from __future__ import print_function

import matplotlib.pyplot as plt
import time
import datetime
import numpy as np
import winsound

from tqdm import *
from picoscope import ps5000a
from scipy.optimize import curve_fit


def func(t, a, tau, c):
    """ Mono-exponential decay function. t is the time."""
    return a * np.exp(-t / tau) + c


def fit_decay(t, y):
    """ Function to fit the data,y, to the mono-exponential decay."""
    # Guess initial fitting parameters
    a_guess = max(y) - min(y)

    y_tau = y - min(y)
    t_loc = np.where(y_tau/max(y_tau) <= 1/np.e)
    tau_guess = t[t_loc[0][0]]
    # tau_guess = 10

    c_guess = min(y)
    # Fit curve
    popt, pcov = curve_fit(func, t, y, p0=(a_guess, tau_guess, c_guess))
    # print('\nLifetime is: %.4f' % popt[1])
    return popt


class DecayMeasure:
    def __init__(self):
        self.ps = ps5000a.PS5000a(connect=False)

    def openScope(self):
        self.ps.open()

        bitRes = 16
        self.ps.setResolution(str(bitRes))
        print("Resolution =  %d Bit" % bitRes)

        self.ps.setChannel("A", coupling="DC", VRange=10000.0E-3, VOffset=-9000.0E-3, enabled=True)
        self.ps.setChannel("B", coupling="DC", VRange=5.0, VOffset=0, enabled=False)
        self.ps.setSimpleTrigger(trigSrc="External", threshold_V=2.0, direction="Falling", timeout_ms=5000)

        # Set capture duration, s
        waveformDuration = 100E-3
        obsDuration = 1*waveformDuration

        # Set sampling rate, Hz
        sampleFreq = 1E4
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
        # Create axis data
        dataTimeAxis = np.arange(self.res[1]) * self.res[0] * 1E3

        # # Average datapoints
        # x = 1
        # if self.res[1] % x != 0:
        #     raise ValueError('Error with number of datapoints chosen to average.')
        # dataTimeAxis = dataTimeAxis.reshape(-1, x).mean(axis=1)

        # Reject time
        iloc = np.where(dataTimeAxis >= 0.1)
        dataTimeAxis = dataTimeAxis[iloc]
        data = np.zeros(len(dataTimeAxis))
        # Create plot
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.grid(True, which='major')
        plt.ylabel("Voltage (V)")
        plt.xlabel("Time (ms)")

        # Sum loops of data
        for i in tqdm(range(sweep_no)):
            # Collect data
            self.armMeasure()
            newData = self.measure()
            # # Average over time
            # newData = newData.reshape(-1, x).mean(axis=1)
            # Reject Time
            newData = newData[iloc]
            # Add to existing data
            data = data + newData

        # Calculate lifetime
        popt = fit_decay(dataTimeAxis, data)
        lifetime = str('%.4f' % popt[1])

        # Plot figure
        plt.plot(dataTimeAxis, data, label='Raw Data')
        plt.plot(dataTimeAxis, func(dataTimeAxis, *popt), 'r--', label=lifetime)
        plt.legend(loc="best")
        plt.savefig('Data/SingleSweep.png', dpi=900)
        plt.show()

        # # Save data to .txt file
        # ref = time.strftime('%d%m%y_%H%M%S', time.gmtime())
        # fname = 'Data\\stabilityTest\\' + ref + '.txt'
        # dataTimeAxis = np.array(dataTimeAxis)
        # saveData = np.c_[dataTimeAxis, data]
        # np.savetxt(fname, saveData, newline='\r\n')

    def single_sweeps(self, sweep_no, reference):
        """Measure and save single sweeps"""

        # Create time axis
        dataTimeAxis = np.arange(self.res[1]) * self.res[0] * 1E3
        dataTimeAxis = np.array(dataTimeAxis)

        # Reject time of 1ms
        # iloc = np.where(dataTimeAxis >= 0.5)
        # dataTimeAxis = dataTimeAxis[iloc]

        record = []
        tau = []
        for i in tqdm(range(sweep_no)):
            # Collect data
            self.armMeasure()
            ref = datetime.datetime.now().strftime("%H%M%S.3%f")
            data = self.measure()

            # Reject Time
            # data = data[iloc]

            # Calculate lifetime
            popt = fit_decay(dataTimeAxis, data)
            record.append(float(ref))
            tau.append(popt[1])

        # Plot histogram
        plt.figure(figsize=(10.0, 5.0))
        plt.hist(tau, bins=100)
        plt.ticklabel_format(useOffset=False)
        plt.xlabel('Lifetime (ms)')
        plt.ylabel('Frequency')
        plt.savefig('./Data/' + reference + '.png', dpi=1000)
        # plt.show()

        # Save fitted lifetimes
        record = np.asarray(record)
        tau = np.asarray(tau)
        saveData = np.c_[record, tau]
        fname = 'Data/' + reference + '.txt'
        np.savetxt(fname, saveData, newline='\r\n')

        winsound.Beep(600, 1000)


if __name__ == "__main__":
    dm = DecayMeasure()
    dm.openScope()

    ## Accumulate a set number of sweeps before plotting
    dm.accumulate(sweep_no=1)

    ## Capture and fit single sweeps
    # dm.single_sweeps(sweep_no=900, reference='T27/Syrup_in_IL/60Gin2IL')

    dm.closeScope()
