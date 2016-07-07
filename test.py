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

        # Setup serial port to communicate with arduino
        self.ser = serial.Serial(
            port='COM3',
            baudrate=115200,
            timeout=1
        )

    def openScope(self):
        self.ps.open()

        bitRes = 16
        self.ps.setResolution(str(bitRes))
        print("Resolution =  %d Bit" % bitRes)

        self.ps.setChannel("A", coupling="DC", VRange=1, VOffset=-0.8, enabled=True)
        self.ps.setChannel("B", coupling="DC", VRange=5.0, VOffset=0, enabled=False)
        self.ps.setSimpleTrigger(trigSrc="External", threshold_V=2.0, direction="Falling", timeout_ms=5000)

        # Set capture duration, s
        waveformDuration = 100E-3
        obsDuration = 1*waveformDuration

        # Set sampling rate, Hz
        sampleFreq = 1E4
        sampleInterval = 1.0 / sampleFreq

        res = self.ps.setSamplingInterval(sampleInterval, obsDuration)
        print(res)

        # Print final capture settings
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
            time.sleep(0.001)
        # print("Sampling Done")
        return self.ps.getDataV("A")

    def show_signal(self):
        """ Measure a single decay and show with the fit in a plot. """

        # Create a time axis for the plots
        self.x = np.arange(self.res[1]) * self.res[0]
        # Convert time axis to milliseconds
        self.x *= 1E3

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

        # Unique measurement ID
        self.timestamp = datetime.now().timestamp()

        # Make directory to store files
        directory = "Data/" + str(self.timestamp) + "/raw"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Allow arduino to fire up
        time.sleep(2)
        # Request data from arduino
        self.requestData()
        time.sleep(2)
        tempC, humidity = self.getAmbient()
        t_in, t_out = self.getThermocouple()
        self.requestData()

        # Collect and save data for each sweep
        start = time.time()
        for i in tqdm(range(sweeps)):

            # Collect arduino output data every 20 sweeps
            if time.time() - start > 2:
                tempC, humidity = self.getAmbient()
                t_in, t_out = self.getThermocouple()
                # Request data from arduino
                self.requestData()
                start = time.time()

            # Collect data
            self.armMeasure()
            dt = datetime.now()
            data = self.measure()

            # start_time = timeit.default_timer()
            #####
            fname = directory + "/" + str(self.timestamp) + "_" + str(i) + ".h5"
            storeRaw = pd.HDFStore(fname)

            rawLog = {"timeID": self.timestamp,
                      "chip": self.chip,
                      "medium": self.medium,
                      "concentration": self.concentration,
                      "fs": self.res[0],
                      "sample_no": self.res[1],
                      "sweeps": sweeps,
                      "sweep_no": i,
                      "datetime": dt,
                      "tempC": tempC,
                      "humidity": humidity,
                      "thermocouple_in": t_in,
                      "thermocouple_out": t_out
                      }
            rawLog = pd.DataFrame(rawLog, index=[0])
            storeRaw.put('log/', rawLog)

            rawData = pd.Series(data)
            storeRaw.put('data/', rawData)
            storeRaw.close()
            ######
            # elapsed = timeit.default_timer() - start_time
            # print(elapsed)

        winsound.Beep(600, 1000)

    def requestData(self):
        # Serial read temperature and humidity
        self.ser.write(b'SHT\n')
        # Serial read temperature and humidity
        self.ser.write(b'TK\n')

    def getAmbient(self):
        msg = self.ser.readline().decode('utf-8')  # Add [:-2]

        # Extract data from string
        [tempC, humidity] = re.findall(r'\d+\.\d+', msg)
        # print("\tTemperature: {}°C".format(tempC))
        # print("\tHumidity:    {}%\n".format(humidity))

        return tempC, humidity

    def getThermocouple(self):
        msg = self.ser.readline().decode('utf-8')  # Add [:-2]

        # Extract data from string
        [t_in, t_out] = re.findall(r'\d+\.\d+', msg)
        # print("\tTemperature in:  {}°C".format(t_in))
        # print("\tTemperature out: {}°C\n".format(t_out))

        return t_in, t_out

    def analyseData(self):

        # Empty data frame to append results to
        df = pd.DataFrame()

        # for folder in timestamped folder folder:
        for file in gb.glob("Data/" + str(self.timestamp) + "/raw/*.h5"):
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
            A = popt[1]
            tau = popt[1]

            # Append lifetime to dataframe
            df_file['A'] = A
            df_file['tau'] = tau

            # Add sweep data to measurement dataframe
            df = df.append(df_file)

            # Close hdf5 file
            store.close()

        # Sort rows in measurement dataframe by datetime
        df = df.set_index('datetime').sort_index()
        df = df.reset_index()

        # Save dataframe
        df.to_csv("Data/" + str(self.timestamp) + "/analysis.csv")

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

        plt.savefig("Data/" + str(self.timestamp) + '/lifetimeVsTime.png', dpi=1000)

        # Create histogram plot
        fig2, ax2 = plt.subplots()
        ax2.hist(df['tau'], bins=100)

        plt.ticklabel_format(useOffset=False)
        plt.xlabel('Lifetime (ms)')
        plt.ylabel('Frequency')

        plt.savefig("Data/" + str(self.timestamp) + '/histogram.png', dpi=1000)

        # Bring window to the front (above pycharm)
        fig.canvas.manager.window.activateWindow()
        fig.canvas.manager.window.raise_()
        fig2.canvas.manager.window.activateWindow()
        fig2.canvas.manager.window.raise_()

        plt.show()


def setConcentration(i):
    if i == 0:
        return 0
    elif i == 2:
        return 2
    elif i == 4:
        return 4
    elif i == 6:
        return 6
    elif i == 8:
        return 8
    elif i == 10:
        return 10
    elif i == 12:
        return 12
    elif i == 14:
        return 14
    elif i == 16:
        return 16
    elif i == 20:
        return 20
    elif i == 50:
        return 50
    else:
        print("Error")
        exit()


if __name__ == "__main__":

    # Show a single sweep with the fit
    # dm = DecayMeasure()
    # dm.openScope()
    # dm.show_signal()
    # dm.closeScope()

    # Capture and fit single sweeps while logging temperature
    chip = 'T22'
    medium = 'Air'
    concentration = np.nan
    # medium = 'Water'
    # concentration = setConcentration(0)
    print("Measuring concentration {0}".format(concentration))

    dm = DecayMeasure(chip, medium, concentration)
    dm.openScope()
    dm.single_sweeps(sweeps=20)
    dm.closeScope()

    print("Analysing data files...")
    dm.analyseData()
    print("Done!")
