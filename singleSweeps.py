import matplotlib.pyplot as plt
import time
import winsound
import serial
import re
import os
import numpy as np
import pandas as pd
import timeit
import glob as gb
import matplotlib.dates as mdates

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
    def __init__(self, chip="None", medium="Air", concentration=np.nan):
        self.ps = ps5000a.PS5000a(connect=False)
        self.chip = chip
        self.medium = medium
        self.concentration = concentration

    def openScope(self):
        self.ps.open()

        bitRes = 16
        self.ps.setResolution(str(bitRes))
        print("Resolution =  %d Bit" % bitRes)

        self.ps.setChannel("A", coupling="DC", VRange=1000.0E-3, VOffset=-500.0E-3, enabled=True)
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
            time.sleep(0.001)
        # print("Sampling Done")
        return self.ps.getDataV("A")

    def show_signal(self):
        """ Measure a single decay and show with the fit in a plot. """

        # Collect data
        self.armMeasure()
        data = self.measure()

        # Calculate lifetime
        popt = fit_decay(self.x, data)
        residuals = data - mono_exp_decay(self.x, *popt)
        standd = np.std(residuals)

        # Do plots
        fig, (ax1, ax2) = plt.subplots(2,figsize=(15,15), sharex=False)
        ax1.set_title("Lifetime is {0:.4f} $\pm$ {1:.4f} ms".format(popt[1], standd))

        ax1.plot(self.x, data, 'k.', label="Original Noised Data")
        ax1.plot(self.x, mono_exp_decay(self.x, *popt), 'r-', label="Fitted Curve")
        ax1.axvline(popt[1], color='blue')
        ax1.grid(True, which="major")
        ax1.set_ylabel('Intensity (A.U.)')
        ax1.set_xlim(0, max(self.x))
        ax1.axhline(y=0, color='k')
        ax1.legend()

        ax2.set_xlabel("Time (ms)")
        ax2.set_ylabel('Residuals')
        ax2.axhline(y=0, color='k')
        ax2.plot(self.x, residuals)
        ax2.set_xlim(0,max(self.x))
        ax2.grid(True, which="major")

        # Bring window to the front (above pycharm)
        fig.canvas.manager.window.activateWindow()
        fig.canvas.manager.window.raise_()
        plt.show()

    def single_sweeps(self, sweeps):
        """ Measure and save single sweeps. """

        # Wait for arduino to fire up loging temp and humidity to serial
        time.sleep(3)

        # Unique measurement ID
        timestamp = datetime.now().timestamp()

        # Make directory to store files
        directory = "Data/" + str(timestamp) + "/raw"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Collect and save data for each sweep
        for i in tqdm(range(sweeps)):

            # if i == 1000:
            #     self.medium = "Intralipid"
            # elif i == 2000:
            #     self.medium = "Water"
            # elif i == 3000:
            #     self.medium = "Intralipid"

            # Collect data
            self.armMeasure()
            dt = datetime.now()
            data = self.measure()
            # start_time = timeit.default_timer()
            #####
            fname = directory + "/" + str(timestamp) + "_" + str(i) + ".h5"
            storeRaw = pd.HDFStore(fname)

            rawLog = {"timeID": timestamp,
                      "chip": self.chip,
                      "medium": self.medium,
                      "concentration": self.concentration,
                      "fs": self.res[0],
                      "sample_no": self.res[1],
                      "sweeps": sweeps,
                      "sweep_no": i,
                      "datetime": dt,
                      "tempC": tempC,
                      "humidity": humidity}
            rawLog = pd.DataFrame(rawLog, index=[0])
            storeRaw.put('log/', rawLog)

            rawData = pd.Series(data)
            storeRaw.put('data/', rawData)
            storeRaw.close()
            ######
            # elapsed = timeit.default_timer() - start_time
            # print(elapsed)

        winsound.Beep(600, 1000)

    def infiniteCapture(self):
        try:
            while True:
                self.single_sweeps(1)
        except KeyboardInterrupt:
            exit()


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


def analyseData():

    # Get most recently created folder
    folder = max(gb.iglob("Data/*"), key=os.path.getctime)
    timestamp = os.path.split(folder)[-1]

    # Empty data frame to append results to
    df = pd.DataFrame()

    # for folder in timestamped folder folder:
    for file in gb.glob("Data/" + timestamp + "/raw/*.h5"):
        # print("Analysing file:" + file)

        # Load HDF file
        store = pd.HDFStore(file)
        df_file = store['log']

        # Create time axis in ms
        fs = store['log']['fs'][0]
        samples = store['log']['sample_no'][0]
        x = np.arange(samples) * fs * 1E3

        # Load decay data
        y = store['data']

        # Calculate lifetime
        popt = fit_decay(x, y)
        tau = popt[1]

        # Append lifetime to dataframe
        df_file['tau'] = tau

        # Add sweep data to measurement dataframe
        df = df.append(df_file)

        # Close hdf5 file
        store.close()

    # Sort rows in measurement dataframe by datetime
    df = df.set_index('datetime').sort_index()
    df = df.reset_index()

    # Save dataframe
    df.to_csv("Data/" + timestamp + "/analysis.csv")

    # Create plot of lifetime vs time
    fig, ax = plt.subplots()
    ax.plot(df['datetime'], df['tau'], 'o', alpha=0.3)
    # ax.plot(df['datetime'], df['tempC'], '-')

    # format the ticks
    ax.xaxis.set_major_locator(mdates.MinuteLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    # ax.xaxis.set_minor_locator(mdates.SecondLocator(bysecond=np.arange(0, 60, 10)))

    ax.grid(True)
    fig.autofmt_xdate()

    plt.xlabel('Time (H:M)')
    plt.ylabel('Lifetime (ms)')
    # plt.tight_layout()
    plt.ticklabel_format(useOffset=False, axis='y')

    plt.savefig("Data/" + timestamp + '/lifetimeVsTime.png', dpi=1000)

    # Create histogram plot
    fig2, ax2 = plt.subplots()
    ax2.hist(df['tau'], bins=100)

    plt.ticklabel_format(useOffset=False)
    plt.xlabel('Lifetime (ms)')
    plt.ylabel('Frequency')

    plt.savefig("Data/" + timestamp + '/histogram.png', dpi=1000)

    # Bring window to the front (above pycharm)
    fig.canvas.manager.window.activateWindow()
    fig.canvas.manager.window.raise_()
    fig2.canvas.manager.window.activateWindow()
    fig2.canvas.manager.window.raise_()

    plt.show()


def run():
    chip = 'T16'
    medium = 'Air'
    concentration = np.nan
    # info = "Medium doped with glucose in mmol. Flow cell setup."

    dm = DecayMeasure(chip, medium, concentration)
    dm.openScope()
    dm.single_sweeps(sweeps=20)
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
    thread1.join()

    print("Analysing data files...")
    analyseData()
    print("Done!")