import numpy as np
import matplotlib.dates as mdates
import pandas as pd
import matplotlib.pyplot as plt
import glob as gb
import time

from LabOnChip.HelperFunctions import fit_decay
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from scipy.optimize import curve_fit


# Helper Functions
def analysis(timestamp):
    # Analyse data in the folder named timestamp

    # for folder in timestamped folder folder:
    files = gb.glob("Data/" + str(timestamp) + "/raw/*.h5")
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


if __name__ == "__main__":

    # Empty data frame to append results to
    df = pd.DataFrame()

    # Make the Pool of workers
    pool = ThreadPool(4)
    # Open the urls in their own threads
    # and return the results
    results = pool.map(analysis, files)
    # close the pool and wait for the work to finish
    pool.close()
    pool.join()


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