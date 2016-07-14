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


# Helper Functions
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


def analysis(timestamp):
    # Analyse data in the folder named timestamp kwarg

    # Empty data frame to append results to
    df = pd.DataFrame()

    # for folder in timestamped folder folder:
    for file in gb.glob("Data/" + str(timestamp) + "/raw/*.h5"):
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

        # Append lifetime to dataframe
        df_file['A'] = popt[0]
        df_file['tau'] = popt[1]
        df_file['c'] = popt[2]

        # Add sweep data to measurement dataframe
        df = df.append(df_file)

        # Close hdf5 file
        store.close()

    # Sort rows in measurement dataframe by datetime
    df = df.set_index('datetime').sort_index()
    df = df.reset_index()

    # Save dataframe
    df.to_csv("Data/" + str(timestamp) + "/analysis.csv")

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

    plt.savefig("Data/" + str(timestamp) + '/lifetimeVsTime.png', dpi=500)

    # Create histogram plot
    fig2, ax2 = plt.subplots()
    ax2.hist(df['tau'], bins=20)

    plt.ticklabel_format(useOffset=False)
    plt.xlabel('Lifetime (ms)')
    plt.ylabel('Frequency')

    plt.savefig("Data/" + str(timestamp) + '/histogram.png', dpi=500)

    # Bring window to the front (above pycharm)
    fig.canvas.manager.window.activateWindow()
    fig.canvas.manager.window.raise_()
    fig2.canvas.manager.window.activateWindow()
    fig2.canvas.manager.window.raise_()

    plt.show()


class Picoscope:
    def __init__(self, *args, **kwargs):
        super(Picoscope, self).__init__()
        self.ps = ps5000a.PS5000a(connect=False)

    def openScope(self):
        self.ps.open()

        bitRes = 16
        self.ps.setResolution(str(bitRes))
        print("Resolution =  %d Bit" % bitRes)

        self.ps.setChannel("A", coupling="DC", VRange=10.0, VOffset=-8.0, enabled=True)
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
            time.sleep(0.0005)
        # print("Sampling Done")
        return self.ps.getDataV("A")


class Arduino:
    def __init__(self):
        super(Arduino, self).__init__()
        # Setup serial port to communicate with arduino
        self.ser = serial.Serial(
            port='COM3',
            baudrate=115200,
            timeout=5
        )

        # Initialise variables
        self.tempC = 0
        self.humidity = 0
        self.t_in = 0
        self.t_out = 0

        # Wait for arduino to fire up
        time.sleep(3)

        # Initialise variables
        self.request_arduino_data()
        time.sleep(3)
        self.get_arduino_data()

    def request_arduino_data(self):
        # Serial request temperature, humidity and thermocouple data (ArduinoV3)
        self.ser.write(b'UPDATE\n')

    def get_arduino_data(self):
        buffer_string = ''
        buffer_string += self.ser.read(self.ser.inWaiting()).decode('utf-8')
        if '\n' in buffer_string:
            last_received = buffer_string[:-2]  # Remove \n and \r
            # print(last_received)
            # Extract data from string
            [self.tempC, self.humidity, self.t_in, self.t_out] = re.findall(r"\d+\.\d+", last_received)
            # print(self.tempC, self.humidity, self.t_in, self.t_out)

    def log_arduino(self):
        ## Used when arduino is constantly pumping out updates (i.e. threading required)
        buffer_string = ''
        while True:
            buffer_string += self.ser.read(self.ser.inWaiting()).decode('utf-8')
            if '\n' in buffer_string:
                last_received = buffer_string[:-2]  # Remove \n and \r
                print(last_received)
                # Extract data from string
                [self.tempC, self.humidity, self.t_in, self.t_out] = re.findall(r"\d+\.\d+", last_received)
                buffer_string = ''  # Reset buffer string
                print(self.tempC, self.humidity, self.t_in, self.t_out)


class System(Picoscope, Arduino):
    def __init__(self, *args, **kwargs):
        # Initialise super classes
        super(System, self).__init__(*args, **kwargs)

        # Measurement Data
        self.chip = kwargs['chip']
        self.current = kwargs['current']
        self.power = kwargs['power']
        self.medium = kwargs['medium']
        self.concentration = kwargs['concentration']

    def show_signal(self):
        """ Measure a single decay and show with the fit in a plot. """
        self.openScope()

        # Create a time axis for the plots
        self.x = np.arange(self.res[1]) * self.res[0]
        # Convert time axis to milliseconds
        self.x *= 1E3

        # Collect data
        self.armMeasure()
        data = self.measure()
        self.closeScope()

        # Calculate lifetime
        popt = fit_decay(self.x, data)
        residuals = data - mono_exp_decay(self.x, *popt)
        standd = np.std(residuals)

        # Do plots
        fig, (ax1, ax2) = plt.subplots(2,figsize=(15,15), sharex=False)
        timer = fig.canvas.new_timer(interval=3000) # creating a timer object and setting an interval of 3000 milliseconds
        timer.add_callback(plt.close)

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

        timer.start()
        plt.show()

    def sweeps_number(self, sweeps):
        """ Measure and save single sweeps. """
        self.openScope()

        # Make directory to store files
        directory = "Data/" + str(timestamp) + "/raw"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Collect and save data for each sweep
        start = time.time()
        # elapsed = []
        for i in tqdm(range(sweeps)):

            if time.time() - start > 2:
                self.get_arduino_data()
                self.request_arduino_data()
                start = time.time()

            # Collect data
            self.armMeasure()
            dt = datetime.now()
            data = self.measure()

            #####
            # start_time = timeit.default_timer()
            #####
            fname = directory + "/" + str(timestamp) + "_" + str(i) + ".h5"
            storeRaw = pd.HDFStore(fname)

            rawLog = {"timeID": timestamp,
                      "chip": self.chip,
                      "current": self.current,
                      "power": self.power,
                      "medium": self.medium,
                      "concentration": self.concentration,
                      "fs": self.res[0],
                      "sample_no": self.res[1],
                      "sweeps": sweeps,
                      "sweep_no": i,
                      "datetime": dt,
                      "tempC": self.tempC,
                      "humidity": self.humidity,
                      "thermocouple_in": self.t_in,
                      "thermocouple_out": self.t_out
                      }
            rawLog = pd.DataFrame(rawLog, index=[0])
            storeRaw.put('log/', rawLog)

            rawData = pd.Series(data)
            storeRaw.put('data/', rawData)
            storeRaw.close()
            ######
            # elapsed.append(timeit.default_timer() - start_time)
        # mean = np.mean(np.asarray(elapsed))
        # std = np.std(np.asarray(elapsed))
        # print(mean, std)
        #####

        # winsound.Beep(600, 1000)

        self.closeScope()

    def sweeps_time(self, mins):
        """ Measure and save single sweeps over a given run_time. """
        self.openScope()

        # Make directory to store files
        directory = "Data/" + str(timestamp) + "/raw"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Collect and save data for each sweep
        self.request_arduino_data()
        sweep = 0

        timeout = time.time() + 60*mins  # mins minutes from now
        print("Finished at: {end}".format(end=time.asctime(time.localtime(timeout))))
        start = time.time()
        while True:
            if time.time() > timeout:
                break
            sweep += 1

            # Arduino Update every 3 seconds
            if time.time() - start > 3:
                self.get_arduino_data()
                self.request_arduino_data()
                start = time.time()

            # Collect data
            self.armMeasure()
            dt = datetime.now()
            data = self.measure()

            fname = directory + "/" + str(timestamp) + "_" + str(sweep) + ".h5"
            storeRaw = pd.HDFStore(fname)

            rawLog = {"timeID": timestamp,
                      "chip": self.chip,
                      "current": self.current,
                      "power": self.power,
                      "medium": self.medium,
                      "concentration": self.concentration,
                      "fs": self.res[0],
                      "sample_no": self.res[1],
                      "run_time": mins,
                      "sweep_no": sweep,
                      "datetime": dt,
                      "tempC": self.tempC,
                      "humidity": self.humidity,
                      "thermocouple_in": self.t_in,
                      "thermocouple_out": self.t_out
                      }
            rawLog = pd.DataFrame(rawLog, index=[0])
            storeRaw.put('log/', rawLog)

            rawData = pd.Series(data)
            storeRaw.put('data/', rawData)
            storeRaw.close()

        self.closeScope()

if __name__ == "__main__":
    chip = 'T6'
    current = 0.5  # Laser drive current(A)
    power = 0.3  # power at the photodiode (W)

    # Unique measurement ID
    timestamp = datetime.now().timestamp()
    # self.timestamp = timestamp  # Allow Analysis to access this variable

    medium = 'Air'
    # medium = 'Water'
    concentration = np.nan
    # medium = 'water intralipid water intralipid(%%)'
    # concentration = 7
    # medium = 'Aqueous Glucose (%% Weight)'
    # concentration = 48
    print("Measuring concentration: {conc}".format(conc=concentration))

    dm = System(chip=chip,
                current=current,
                power=power,
                medium=medium,
                concentration=concentration,
                timestamp=timestamp)

    # # Show a single sweep with the fit
    dm.show_signal()

    # Capture and fit single sweeps while logging temperature
    dm.sweeps_number(sweeps=200)
    # dm.sweeps_time(mins=10)

    print("Analysing data files...")
    analysis(timestamp=timestamp)
    print("Done!")