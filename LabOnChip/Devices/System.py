import numpy as np
import pandas as pd
import time
import os
import winsound

from tqdm import tqdm
from datetime import datetime
from LabOnChip.Devices.Picoscope import Picoscope
from LabOnChip.Devices.Arduino import Arduino


class System(Picoscope, Arduino):
    def __init__(self, *args, **kwargs):
        # Initialise super classes
        # TODO: can use in future instead of explicitly calling measurement data kwargs?
        # self.myvalue = kwargs.pop('myvalue', None)
        super(System, self).__init__(*args, **kwargs)

        # Measurement Data
        self.measurementID = kwargs['measurementID']
        self.chip = kwargs['chip']
        self.current = kwargs['current']
        self.medium = kwargs['medium']
        self.concentration = np.nan

    def set_concentration(self, concentration):
        """ Set concentration of medium being tested. """
        self.concentration = concentration

    def set_power(self, power):
        # TODO: remove
        self.power = power

    def single_sweep(self):
        # Make directory to store files
        directory = "../Data/" + str(self.measurementID) + "/raw"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Collect data
        self.armMeasure()
        dt = datetime.now()
        data = self.measure()

        fname = directory + "/" + str(datetime.now().timestamp()) + ".h5"
        storeRaw = pd.HDFStore(fname)

        rawLog = {"measurementID": self.measurementID,
                  "chip": self.chip,
                  "current": self.current,
                  "power": self.power,
                  "medium": self.medium,
                  "concentration": self.concentration,
                  "fs": self.res[0],
                  "sample_no": self.res[1],
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

        self.get_arduino_data()
        time.sleep(3)
        self.request_arduino_data()

    def sweeps_number(self, sweeps):
        """ Measure and save single sweeps for a given number of sweeps. """

        # Make directory to store files
        directory = "Data/" + str(self.measurementID) + "/raw"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Collect and save data for each sweep
        start = time.time()
        for i in tqdm(range(sweeps)):

            if time.time() - start > 3:
                self.get_arduino_data()
                self.request_arduino_data()
                start = time.time()

            # Collect data
            self.armMeasure()
            dt = datetime.now()
            data = self.measure()

            fname = directory + "/" + str(datetime.now().timestamp()) + ".h5"
            storeRaw = pd.HDFStore(fname)

            rawLog = {"measurementID": self.measurementID,
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
        try:
            winsound.Beep(600, 1000)
        except:
            pass

    def sweeps_time(self, mins):
        """ Measure and save single sweeps over a given run_time. """

        # Make directory to store files
        directory = "../Data/" + str(self.measurementID) + "/raw"
        if not os.path.exists(directory):
            os.makedirs(directory)

        sweep = 0  # Initialise sweep number
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

            fname = directory + "/" + str(datetime.now().timestamp()) + ".h5"
            storeRaw = pd.HDFStore(fname)

            rawLog = {"measurementID": self.measurementID,
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

