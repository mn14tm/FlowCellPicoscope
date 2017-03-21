import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from labonchip.Methods.Devices.Arduino import Arduino
from labonchip.Methods.Devices.ITC4001 import ITC4001
from labonchip.Methods.Devices.Picoscope import Picoscope


def measure(log):
    import os

    # Make directory to store files
    directory = '../Data/' + str(log['measurementID']) + "/raw"
    if not os.path.exists(directory):
        os.makedirs(directory)
        os.makedirs('../Data/' + str(log['measurementID']) + "/Plots")

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
    fig.savefig('../Data/' + str(log['measurementID']) + '/Plots/current_{0:.3f}.png'.format(current))
    plt.close(fig)  # close the figure

    # Save data as h5 file
    storeRaw = pd.HDFStore(directory + "/" + str(log['datetime'].timestamp()) + ".h5")
    storeRaw.put('log/', pd.DataFrame(log, index=[0]))
    storeRaw.put('data/', data)
    storeRaw.close()


def analysis(file):
    # Load HDF file
    store = pd.HDFStore(file)
    df_file = store['log']
    # Create time axis in ms
    fs = store['log']['fs'][0]
    samples = store['log']['sample_no'][0]
    # Load fitting data
    y = np.array(store['data'])
    # Close hdf5 file
    store.close()
    # Do analysis
    df_file['mean'] = np.mean(y)
    df_file['std'] = np.std(y)
    return df_file


def folder_analysis(folder, savename='analysis'):
    """Use single thread to analyse data (h5) files inside: folder/raw"""
    # Get raw data files list
    import pandas as pd
    import glob as gb

    directory = "../Data/" + str(folder)
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


def plot_analysis(df, folder, dir='../Data/', save=True):
    # Directory to save plots to
    directory = dir + str(folder)

    fig, ax = plt.subplots(1)
    ax.errorbar(df['current'], df['mean'], yerr=df['std'], fmt='-.')
    ax.set_xlabel('Current (A)')
    ax.set_ylabel('Mean (A.U.)')
    plt.tight_layout()
    if save:
        plt.savefig(directory + '/currentVsMean.png', dpi=300)
    plt.show()


if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID=str(datetime.now().timestamp()),
               chip='T27',
               medium='Air'
               )

    # Setup devices
    laserDriver = ITC4001()
    arduino = Arduino()
    scope = Picoscope()
    scope.openScope(obsDuration=10)
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Sweep over pump powers (A)
    for current in tqdm(np.linspace(0.1, 0.5, num=21, endpoint=True)):
        # for current in [0.5]:
        log["current"] = current  # Laser drive current(A)
        laserDriver.set_ld_current(current)
        laserDriver.turn_ld_on()
        arduino.update()
        log['tempC'] = arduino.tempC
        log['humidity'] = arduino.humidity
        log['optical power'] = laserDriver.get_optical_power()
        measure(log)
        laserDriver.turn_ld_off()
        time.sleep(1)

    # Stop and close all instruments
    scope.closeScope()
    arduino.close()
    print('Finished measurement.')

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])
    print("Done! Now plotting...")
    plot_analysis(df, folder=log['measurementID'])
    print("Finito!")
