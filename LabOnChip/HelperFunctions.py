import os
import errno
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob as gb
from tqdm import tqdm
from scipy.optimize import curve_fit


# Helper Functions
def mono_exp_decay(t, a, tau, c):
    """ Mono-exponential decay function. t is the time.
    """
    return a * np.exp(-t / tau) + c


def fit_decay(t, y):
    """ Function to fit the data, y, to the mono-exponential decay.
    Return fitting parameters [a, tau, c].
    """
    # Normalise data
    y_norm = y - min(y)
    y_norm = y_norm / max(y_norm)
    # Locate time where 1/e of normalised intensity
    t_loc = np.where(y_norm <= 1/np.e)

    # Guess initial fitting parameters
    a_guess = max(y) - min(y)
    tau_guess = t[t_loc[0][0]]
    c_guess = min(y)

    # Fit decay
    try:
        popt, pcov = curve_fit(mono_exp_decay, t, y, p0=(a_guess, tau_guess, c_guess))
    except RuntimeError:
        popt = [np.nan, np.nan, np.nan]
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

    # Optional drop x > cutoff ms
    # iloc = np.where(x > 1)
    # x = x[iloc]
    # y = np.asarray(y)[iloc]

    # Calculate lifetime
    popt = fit_decay(x, y)

    # Append lifetime to individual measurement dataframe
    df_file['A'] = popt[0]
    df_file['tau'] = popt[1]
    df_file['c'] = popt[2]

    # # Reflection mean and std calculation
    # df_file['mean'] = np.mean(y)
    # df_file['std'] = np.std(y)
    return df_file


def folder_analysis(folder):
    """ Use single thread to analyse data (h5) files inside: folder/raw
    """
    # Get raw data files list
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
    df.to_csv(directory + "/analysis.csv")

    store = pd.HDFStore(directory + "/analysis.h5")
    store['df'] = df  # save it
    store.close()

    return df


def folder_analysis_pool(folder):
    """ Use multiprocessing to analysise raw files inside the timestamp folder"""
    from multiprocessing import Pool

    # Get raw data files list
    directory = "../Data/" + str(folder)
    files = gb.glob( directory + "/raw/*.h5")

    # Do fitting
    pool = Pool()
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


def plot_analysis(df, folder, dir='../Data/', save=True, hist=False):
    import matplotlib.dates as mdates

    # Directory to save plots to
    directory = dir + str(folder)

    # Create plot of lifetime vs time
    fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True)
    ax1.plot(df['datetime'], df['tau'], 'o', alpha=0.3)
    ax2.plot(df['datetime'], df['A'], 'o', alpha=0.3)

    fig.autofmt_xdate()
    ax1.grid(True)
    ax2.grid(True)
    ax2.set_xlabel('Time (H:M)')
    ax1.set_ylabel('Lifetime (ms)')
    ax2.set_ylabel('Amplitude (A.U.)')
    plt.tight_layout()
    plt.ticklabel_format(useOffset=False, axis='y')
    if save:
        plt.savefig(directory + '/lifetimeVsTime.png', dpi=300)

    # Create histogram plot
    if hist:
        fig2, ax2 = plt.subplots()
        ax2.hist(df['tau'], bins=20)
        plt.ticklabel_format(useOffset=False)
        plt.xlabel('Lifetime (ms)')
        plt.ylabel('Frequency')
        if save:
            plt.savefig(directory + '/histogram.png', dpi=300)
    plt.show()


def sweeps_number(sweeps, log, arduino, scope, laserDriver, dir='../Data/'):
    """ Measure and save single sweeps for a given number of sweeps.
    """
    from datetime import datetime
    import time

    # Make directory to store files
    directory = dir + str(log['measurementID']) + "/raw"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Collect and save data for each sweep
    log['sweeps'] = sweeps
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
            # Update laser measured optical power (by internal photodiode)
            log['optical power'] = laserDriver.get_optical_power()

        # Collect data from picoscope (detector)
        scope.armMeasure()
        data = scope.measure()
        data = pd.Series(data)

        # Save data as h5 file
        storeRaw = pd.HDFStore(directory + "/" + str(log['datetime'].timestamp()) + ".h5")
        storeRaw.put('log/', pd.DataFrame(log, index=[0]))
        storeRaw.put('data/', data)
        storeRaw.close()


def sweeps_time(mins, log, arduino, scope, laserDriver, dir='../Data/'):
    """ Measure and save single sweeps over a given time.
    """
    from datetime import datetime
    import time
    log['run_time'] = mins
    # Make directory to store files
    directory = dir + str(log['measurementID']) + "/raw"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # minutes from now to run for
    timeout = time.time() + 60 * mins
    print("Finished at: {end}".format(end=time.asctime(time.localtime(timeout))))

    # Begin
    start = time.time()
    sweep = 0
    while time.time() < timeout:
        sweep += 1
        log['sweep_no'] = sweep
        log['datetime'] = datetime.now()

        # Arduino and laser power update every 3 seconds (delay is 3 seconds due to calling method)
        if time.time() - start > 3:
            arduino.get_data()
            log['t_in'] = arduino.t_in
            log['t_out'] = arduino.t_out
            log['tempC'] = arduino.tempC
            log['humidity'] = arduino.humidity
            arduino.request_data()
            start = time.time()
            # Update laser measured optical power (by internal photodiode)
            log['optical power'] = laserDriver.get_optical_power()

        # Collect data from picoscope (detector)
        scope.armMeasure()
        data = scope.measure()
        data = pd.Series(data)

        # Save data as h5 file
        storeRaw = pd.HDFStore(directory + "/" + str(log['datetime'].timestamp()) + ".h5")
        storeRaw.put('log/', pd.DataFrame(log, index=[0]))
        storeRaw.put('data/', data)
        storeRaw.close()


def text_when_done():
    """ Send me a text saying 'Experiment Finished'.
    """
    from twilio.rest import TwilioRestClient

    # Setup texting for notification when complete
    accountSID = 'AC8e87f7e3dfec4552532dcae2480fa021'
    authToken = 'a576d5aac28efc503b50b5958e9276f0'
    twilioCli = TwilioRestClient(accountSID, authToken)
    myTwilioNumber = '+441725762055'
    myCellPhone = '+447932553111'

    message = twilioCli.messages.create(
        body='Experiment Finished',
        from_=myTwilioNumber,
        to=myCellPhone)
    print(message.sid)


def copy_data(src='../Data/', dst='Z:/LabOnChip/Data', symlinks=False, ignore=None):
    """ Copies all data in src folder to the dst folder. See http://tinyurl.com/q9xc492
    """
    import shutil
    if not os.path.exists(dst):
        print("Destination does not exist!")
        # os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)
