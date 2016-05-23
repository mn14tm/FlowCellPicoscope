import matplotlib.pyplot as plt
import time
import winsound
import serial
import re
import timeit
import numpy as np
import pandas as pd

from tqdm import *
from picoscope import ps5000a
from scipy.optimize import curve_fit
from datetime import datetime
from threading import Thread


# Initialise global values
tempC = 0
humidity = 0


def mono_exp_decay(t, a, tau, c):
    """ Mono-exponential decay function. t is the time."""
    return a * np.exp(-t / tau) + c


def fit_decay(t, y):
    """ Function to fit the data, y, to the mono-exponential decay."""
    # Guess initial fitting parameters
    a_guess = max(y) - min(y)

    y_norm = y - min(y)
    y_norm = y_norm / max(y_norm)
    t_loc = np.where(y_norm <= 1/np.e)
    tau_guess = t[t_loc[0][0]]

    c_guess = min(y)
    # Fit decay
    popt, pcov = curve_fit(mono_exp_decay, t, y, p0=(a_guess, tau_guess, c_guess))
    return popt


class DecayMeasure:
    def __init__(self, chip="None", medium="Air", concentration=0):
        self.ps = ps5000a.PS5000a(connect=False)
        self.chip = chip
        self.medium = medium
        self.concentration = concentration

    def openScope(self):
        self.ps.open()

        bitRes = 16
        self.ps.setResolution(str(bitRes))
        print("Resolution =  %d Bit" % bitRes)

        self.ps.setChannel("A", coupling="DC", VRange=500.0E-3, VOffset=-300.0E-3, enabled=True)
        self.ps.setChannel("B", coupling="DC", VRange=5.0, VOffset=0, enabled=False)
        self.ps.setSimpleTrigger(trigSrc="External", threshold_V=2.0, direction="Falling", timeout_ms=5000)

        # Set capture duration, s
        waveformDuration = 100E-3
        obsDuration = 1*waveformDuration

        # Set sampling rate, Hz
        sampleFreq = 1E4
        sampleInterval = 1.0 / sampleFreq

        res = self.ps.setSamplingInterval(sampleInterval, obsDuration)

        # Print final capture settings
        print("Sampling frequency = %.3f MHz" % (1E-6/res[0]))
        print("Sampling interval = %.f ns" % (res[0] * 1E9))
        print("Taking  samples = %d" % res[1])
        print("Maximum samples = %d" % res[2])
        self.res = res
        # Create a time axis for the plots
        self.x = np.arange(res[1]) * res[0] * 1E3

    def closeScope(self):
        self.ps.close()

    def armMeasure(self):
        self.ps.runBlock()

    def measure(self):
        # print("Waiting for trigger")
        while not self.ps.isReady():
            time.sleep(0.005)
        # print("Sampling Done")
        return self.ps.getDataV("A")

    def show_signal(self):
        """ Measure a single decay and show with the fit in a plot. """

        # Collect data
        self.armMeasure()
        data = self.measure()

        # Calculate lifetime
        popt = fit_decay(self.x, data)

        # Plot figure
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(self.x, data, label="Raw Data")
        ax.plot(self.x, mono_exp_decay(self.x, *popt), 'r--', label="Fitted")
        ax.grid(True, which="major")
        plt.title("Lifetime is {:.4f} ms".format(popt[1]))
        plt.ylabel("Voltage (V)")
        plt.xlabel("Time (ms)")
        plt.legend(loc="best")
        plt.show()

    def single_sweeps(self, sweeps):
        """ Measure and save single sweeps. """

        # Create/open HDF file
        store = pd.HDFStore('Data/' + self.chip + '.h5')

        # Store general measurement settings
        log = pd.DataFrame({"tempC": tempC,
                    "humidity": humidity,
                    "datetimeStart": datetime.now(),
                    "chip": self.chip,
                    "medium": self.medium,
                    "concentration": self.concentration,
                    "fs (Hz)": self.res[0],
                    "samples collected": self.res[1],
                    "sweeps": sweeps,
                    }, index=[0])
        store.put('log', log)
        store.put('raw/timeAxis', pd.Series(self.x))
        # Wait for arduino to fire up loging temp and humidity to serial
        time.sleep(3)

        for i in tqdm(range(sweeps)):
            # Collect data
            self.armMeasure()
            dt = datetime.now()
            data = self.measure()

            # start_time = timeit.default_timer()
            # Store raw data
            raw = pd.DataFrame({"datetime":dt,
                                "data": data,
                                "tempC": tempC,
                                "humidity": humidity,
                                "sweep": i})
            fname = 'raw/sweep' + str(i+1)
            store.put(fname, raw)
            # elapsed = timeit.default_timer() - start_time
            # print(elapsed)
        store.close()

            # start_time = timeit.default_timer()
            # # Calculate lifetime
            # popt = fit_decay(self.x, data)
            # record.append(dt.timestamp())
            # tau.append(popt[1])
            # elapsed = timeit.default_timer() - start_time
            # print(elapsed)

        winsound.Beep(600, 1000)

        # # Plot histogram
        # plt.figure(figsize=(10.0, 5.0))
        # plt.hist(tau, bins=100)
        # plt.ticklabel_format(useOffset=False)
        # plt.xlabel('Lifetime (ms)')
        # plt.ylabel('Frequency')
        # plt.show()  # Breaks on multithreading for some reason


def ambientLogger():
    """ Measure the temperature and humidity from arduino until killed
     by another program. Code inspired from the http://tinyurl.com/zv5ssmv """

    # Arduino port on computer
    # port = '/dev/tty.usbmodem621'  # Mac
    port = 'COM3'  # Windows

    # Setup serial monitor for arduino
    ser = serial.Serial(
        port=port,
        baudrate=19200,
        timeout=1
    )

    global tempC, humidity

    buffer_string = ''
    while True:
        buffer_string += ser.read(ser.inWaiting()).decode('utf-8')
        if '\n' in buffer_string:
            lines = buffer_string.split('\n')  # Guaranteed to have at least 2 entries
            last_received = lines[-2]
            # Extract data from string
            [tempC, humidity] = re.findall("\d+\.\d+", last_received)


def run():
    chip = 'T16'
    medium = 'Air'
    concentration = 0
    # info = "Medium doped with glucose in mmol. Flow cell setup."

    dm = DecayMeasure(chip, medium, concentration)
    dm.openScope()
    dm.single_sweeps(sweeps=50)
    dm.closeScope()

if __name__ == "__main__":

    # # Show a single sweep with the fit
    # dm = DecayMeasure()
    # dm.openScope()
    # dm.show_signal()
    # dm.closeScope()

    # Capture and fit single sweeps while logging temperature
    thread1 = Thread(target=run)
    thread2 = Thread(target=ambientLogger)
    thread2.setDaemon(True)
    thread1.start()
    thread2.start()

