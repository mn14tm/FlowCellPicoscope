import numpy as np
import matplotlib.dates as mdates
import pandas as pd
import matplotlib.pyplot as plt
import glob as gb
from scipy.optimize import curve_fit
from multiprocessing import Pool


# Helper Functions
def mono_exp_decay(t, a, tau, c):
    """ Mono-exponential decay function. t is the time."""
    return a * np.exp(-t / tau) + c


def fit_decay(t, y):
    """ Function to fit the data, y, to the mono-exponential decay."""
    # Guess initial fitting parameters
    a_guess = max(y) - min(y)
    c_guess = min(y)
    tau_guess = 10
    popt, pcov = curve_fit(mono_exp_decay, t, y, p0=(a_guess, tau_guess, c_guess))
    return popt


def analysis(file):
    # Load HDF file
    store = pd.HDFStore(file)
    df_file = store['log']

    # Create time axis in ms
    fs = store['log']['fs'][0]
    samples = store['log']['sample_no'][0]
    x = np.arange(samples) * fs * 1E3

    # Load decay data
    y = store['data']

    # Close hdf5 file
    store.close()

    # Calculate lifetime
    popt = fit_decay(x, y)

    # Append lifetime to individual measurement dataframe
    df_file['A'] = popt[0]
    df_file['tau'] = popt[1]
    df_file['c'] = popt[2]

    return df_file


def folder_analysis(folder):
    """ Use multiprocessing to analysise raw files inside the timestamp folder"""

    pool = Pool()

    # Get raw data files list
    files = gb.glob("../Data/" + str(folder) + "/raw/*.h5")

    # Do fitting
    results = pool.map(analysis, files)

    # close the pool and wait for the work to finish
    pool.close()
    pool.join()

    # merging parts processed by different processes
    df = pd.concat(results, axis=0)

    # Sort rows in measurement dataframe by datetime
    df = df.set_index('datetime').sort_index()
    df = df.reset_index()

    # Save dataframe
    df.to_csv("../Data/" + str(folder) + "/analysis.csv")

    store = pd.HDFStore("../Data/" + str(folder) + "/analysis.h5")
    store['df'] = df  # save it
    store.close()

    return df


def plot_analysis(df):
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
    plt.savefig("../Data/" + str(timestamp) + '/lifetimeVsTime.png', dpi=500)

    # Create histogram plot
    fig2, ax2 = plt.subplots()
    ax2.hist(df['tau'], bins=20)

    plt.ticklabel_format(useOffset=False)
    plt.xlabel('Lifetime (ms)')
    plt.ylabel('Frequency')
    plt.savefig("../Data/" + str(timestamp) + '/histogram.png', dpi=500)
    plt.show()

if __name__ == "__main__":

    # Folder to analyse
    timestamp = 1469206924.941636

    print("Analysing...")
    df = folder_analysis(timestamp)
    print("Done! Now plotting...")
    plot_analysis(df)
