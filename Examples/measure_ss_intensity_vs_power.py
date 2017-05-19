import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from picoscope import ps5000a
from tqdm import tqdm

from labonchip.Methods.Devices.Arduino import Arduino
from labonchip.Methods.Devices.ITC4001 import ITC4001


class Picoscope:
    def __init__(self, *args, **kwargs):
        super(Picoscope, self).__init__()
        self.ps = ps5000a.PS5000a(connect=False)

    def openScope(self, bitRes=16, obsDuration=120e-3, sampleFreq=1E4):
        self.ps.open()

        # Set bit resolution
        self.ps.setResolution(str(bitRes))

        # Set trigger and channels
        scope.ps.setChannel("A", coupling="DC", VRange=5.0, VOffset=-1.0, enabled=True, BWLimited=True)
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

    def plot(self, show=True, decay=False):
        self.armMeasure()
        y = self.measure()
        x = self.get_time()

        # Just plot data
        fig, ax = plt.subplots()
        ax.plot(x, y, '.')
        ax.grid(True, which="major")
        ax.set_ylabel('Intensity (A.U.)')
        ax.set_xlabel("Time (ms)")
        if show:
            plt.show()
        return fig


def measure(log, dataf='../Data/'):
    import os

    # Make directory to store files
    directory = dataf + str(log['measurementID'])
    if not os.path.exists(directory):
        os.makedirs(directory + "/raw")
        os.makedirs(directory + "/Plots")

    # Collect data from picoscope (detector)
    log['datetime'] = datetime.now()
    scope.armMeasure()
    data = scope.measure()
    data = pd.Series(data)

    # Save a plot
    y = data
    x = scope.get_time()
    fig, ax = plt.subplots()
    ax.plot(x, y, '.', alpha=0.3)
    ax.grid(True, which="major")
    ax.set_ylabel('Intensity (A.U.)')
    ax.set_xlabel("Time (ms)")
    fig.savefig(directory + '/Plots/current_{0:.3f}.png'.format(current))
    plt.close(fig)  # close the figure

    # Save data as h5 file
    storeRaw = pd.HDFStore(directory + "/raw/" + str(log['datetime'].timestamp()) + ".h5")
    storeRaw.put('log/', pd.DataFrame(log, index=[0]))
    storeRaw.put('data/', data)
    storeRaw.close()


def analysis(file):
    # Load HDF file
    store = pd.HDFStore(file)
    df_file = store['log']
    # Load fitting data
    y = np.array(store['data'])
    # Close hdf5 file
    store.close()
    # Do analysis
    df_file['mean'] = np.mean(y)
    df_file['std'] = np.std(y)
    return df_file


def folder_analysis(folder, savename='analysis', dir='../Data'):
    """Use single thread to analyse data (h5) files inside: folder/raw"""
    # Get raw data files list
    import pandas as pd
    import glob as gb

    directory = dir + str(folder)
    files = gb.glob(directory + "/raw/*.h5")

    df = pd.DataFrame([])

    # Do fitting
    for file in tqdm(files):
        data = analysis(file)
        df = df.append(data)

    # Sort rows in measurement dataframe by datetime
    df = df.set_index('datetime').sort_index()
    df = df.reset_index()

    # Save dataframe
    df.to_csv(directory + "/" + savename + ".csv")

    store = pd.HDFStore(directory + "/" + savename + ".h5")
    store['df'] = df  # save it
    store.close()

    return df


def plot_analysis(df, folder, dir='E:/Data/', save=True):
    # Directory to save plots to
    directory = dir + str(folder)

    fig, ax = plt.subplots(1)
    ax.errorbar(df['current'], df['mean'], yerr=df['std'], fmt='-.')
    ax.set_xlabel('Current (A)')
    ax.set_ylabel('Mean (A.U.)')
    plt.tight_layout()
    if save:
        plt.savefig(directory + '/Plots/currentVsMean.png', dpi=300)
    plt.show()

if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID=str(datetime.now().timestamp()),
               chip='T26',
               medium='Air'
               )
    # time.sleep(10*60)
    # Setup devices
    laserDriver = ITC4001()
    laserDriver.set_ld_shape('DC')
    arduino = Arduino()
    scope = Picoscope()
    scope.openScope(obsDuration=20)

    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Sweep over pump powers (A)
    for current in tqdm(np.linspace(0.1, 0.5, num=21, endpoint=True)):
        log["current"] = current  # Laser drive current(A)
        laserDriver.set_ld_current(current)
        laserDriver.turn_ld_on()
        arduino.update()
        log['tempC'] = arduino.tempC
        log['humidity'] = arduino.humidity
        log['optical power'] = laserDriver.get_optical_power()
        measure(log, dataf='E:/Data/')
        laserDriver.turn_ld_off()
        time.sleep(1)

    # Stop and close all instruments
    scope.closeScope()
    arduino.close()
    print('Finished measurement.')

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'], dir='E:/Data/')
    print("Done! Now plotting...")
    plot_analysis(df, folder=log['measurementID'], dir='E:/Data/')
    print("Finito!")
