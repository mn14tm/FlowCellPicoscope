import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
import winsound

from tqdm import tqdm
from datetime import datetime
from LabOnChip.Devices.Picoscope import Picoscope
from LabOnChip.Devices.Arduino import Arduino
from LabOnChip.Devices.SyringePump import SyringePump
from LabOnChip.HelperFunctions import fit_decay, mono_exp_decay


class System(Picoscope, Arduino, SyringePump):
    def __init__(self, *args, **kwargs):
        # Initialise super classes
        super(System, self).__init__(*args, **kwargs)

        # Measurement Data
        self.chip = kwargs['chip']
        self.current = kwargs['current']
        self.power = kwargs['power']
        self.medium = kwargs['medium']
        self.concentration = kwargs['concentration']
        self.timestamp = kwargs['timestamp']

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
        fig, (ax1, ax2) = plt.subplots(2,figsize=(15, 15), sharex=False)
        # creating a timer object and setting an interval of 3000 milliseconds
        timer = fig.canvas.new_timer(interval=3000)
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
        directory = "Data/" + str(self.timestamp) + "/raw"
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
            fname = directory + "/" + str(self.timestamp) + "_" + str(i) + ".h5"
            storeRaw = pd.HDFStore(fname)

            rawLog = {"timeID": self.timestamp,
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
        try:
            winsound.Beep(600, 1000)
        except:
            pass

        self.closeScope()

    def sweeps_time(self, mins):
        """ Measure and save single sweeps over a given run_time. """
        self.openScope()

        # Make directory to store files
        directory = "Data/" + str(self.timestamp) + "/raw"
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

            fname = directory + "/" + str(self.timestamp) + "_" + str(sweep) + ".h5"
            storeRaw = pd.HDFStore(fname)

            rawLog = {"timeID": self.timestamp,
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
