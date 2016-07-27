import time
import os
import numpy as np
import matplotlib.dates as mdates
from tqdm import tqdm
import pandas as pd
import matplotlib.pyplot as plt
import glob as gb
from scipy.optimize import curve_fit
from multiprocessing import Pool
from datetime import datetime


# Helper Functions
def mono_exp_decay(t, a, tau, c):
    """ Mono-exponential decay function. t is the time."""
    return a * np.exp(-t / tau) + c


def fit_decay(t, y):
    """ Function to fit the data, y, to the mono-exponential decay."""
    # Guess initial fitting parameters
    a_guess = max(y) - min(y)
    c_guess = min(y)

    y_norm = y - min(y)
    y_norm = y_norm / max(y_norm)
    t_loc = np.where(y_norm <= 1/np.e)
    tau_guess = t[t_loc[0][0]]

    # Fit decay
    popt, pcov = curve_fit(mono_exp_decay, t, y, p0=(a_guess, tau_guess, c_guess))
    return popt


def dilution(conc_out, conc_stock, vol_out=1):
    # Volume of stock required
    vol_stock = vol_out * conc_out / conc_stock
    # Volume of dilute required
    vol_dilute = vol_out - vol_stock
    return vol_dilute, vol_stock


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

    # # Calculate lifetime
    # popt = fit_decay(x, y)
    #
    # # Append lifetime to individual measurement dataframe
    # df_file['A'] = popt[0]
    # df_file['tau'] = popt[1]
    # df_file['c'] = popt[2]

    # Reflection mean and std calculation
    df_file['mean'] = np.mean(y)
    df_file['std'] = np.std(y)
    return df_file


def folder_analysis(folder):
    """ Use multiprocessing to analysise raw files inside the timestamp folder"""
    pool = Pool()

    # Get raw data files list
    directory = "../Data/" + str(folder)
    files = gb.glob( directory + "/raw/*.h5")

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
    df.to_csv(directory + "/analysis.csv")

    store = pd.HDFStore(directory + "/analysis.h5")
    store['df'] = df  # save it
    store.close()

    return df


def plot_analysis(df, folder):
    # Directory to save plots to
    directory = "../Data/" + str(folder)

    # Create plot of lifetime vs time
    fig, ax = plt.subplots()
    ax.plot(df['datetime'], df['tau'], 'o', alpha=0.3)
    # ax.plot(df['datetime'], df['tempC'], '-')

    # format the ticks
    # ax.xaxis.set_major_locator(mdates.MinuteLocator())
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    # ax.xaxis.set_minor_locator(mdates.SecondLocator(bysecond=np.arange(0, 60, 10)))

    ax.grid(True)
    fig.autofmt_xdate()

    plt.xlabel('Time (H:M)')
    plt.ylabel('Lifetime (ms)')
    # plt.tight_layout()
    plt.ticklabel_format(useOffset=False, axis='y')
    # plt.savefig(directory + '/lifetimeVsTime.png', dpi=500)

    # Create histogram plot
    fig2, ax2 = plt.subplots()
    ax2.hist(df['tau'], bins=20)

    plt.ticklabel_format(useOffset=False)
    plt.xlabel('Lifetime (ms)')
    plt.ylabel('Frequency')
    # plt.savefig(directory + '/histogram.png', dpi=500)
    plt.show()


def sweeps_number(sweeps, log, arduino, scope, laserDriver):
    """ Measure and save single sweeps for a given number of sweeps. """
    log['sweeps'] = sweeps

    # Make directory to store files
    directory = "../Data/" + str(log['measurementID']) + "/raw"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Collect and save data for each sweep
    start = time.time()
    for i in tqdm(range(sweeps)):
        log['sweep_no'] = i + 1

        if time.time() - start > 3:
            arduino.get_data()
            log['t_in'] = arduino.t_in
            log['t_out'] = arduino.t_out
            log['tempC'] = arduino.tempC
            log['humidity'] = arduino.humidity
            arduino.request_data()
            start = time.time()
            # Update laser measured optical power (by photodiode internal)
            log['optical power'] = laserDriver.get_optical_power()

        # Collect data from picoscope (detector)
        scope.armMeasure()
        log['datetime'] = datetime.now()
        data = scope.measure()

        fname = directory + "/" + str(log['datetime'].timestamp()) + ".h5"
        storeRaw = pd.HDFStore(fname)
        storeRaw.put('log/', pd.DataFrame(log, index=[0]))

        rawData = pd.Series(data)
        storeRaw.put('data/', rawData)
        storeRaw.close()


def sweeps_time(mins, log, arduino, scope, laserDriver):
    """ Measure and save single sweeps over a given run_time. """
    log['run_time'] = mins
    # Make directory to store files
    directory = "../Data/" + str(log['measurementID']) + "/raw"
    if not os.path.exists(directory):
        os.makedirs(directory)

    sweep = 0  # Initialise sweep number
    timeout = time.time() + 60 * mins  # mins minutes from now
    print("Finished at: {end}".format(end=time.asctime(time.localtime(timeout))))
    start = time.time()
    while time.time() < timeout:
        sweep += 1
        log['sweep_no'] = sweep

        # Arduino and laser power Update every 3 seconds
        if time.time() - start > 3:
            arduino.get_data()
            log['t_in'] = arduino.t_in
            log['t_out'] = arduino.t_out
            log['tempC'] = arduino.tempC
            log['humidity'] = arduino.humidity
            arduino.request_data()
            start = time.time()
            # Update laser measured optical power (by photodiode internal)
            log['optical power'] = laserDriver.get_optical_power()

        # Collect data from picoscope (detector)
        scope.armMeasure()
        log['datetime'] = datetime.now()
        data = scope.measure()

        fname = directory + "/" + str(log['datetime'].timestamp()) + ".h5"
        storeRaw = pd.HDFStore(fname)
        storeRaw.put('log/', pd.DataFrame(log, index=[0]))

        rawData = pd.Series(data)
        storeRaw.put('data/', rawData)
        storeRaw.close()
