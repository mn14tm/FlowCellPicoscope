import pandas as pd
import numpy as np
import glob as gb
import os
import matplotlib.pyplot as plt

from tqdm import tqdm

# Helper Functions
def mono_exp_decay(t, a, tau, c):
    """
    Mono-exponential fitting function. t is the time.
    """
    return a * np.exp(-t / tau) + c


def fit_decay(t, y):
    """
    Function to fit the data, y, to the mono-exponential fitting.
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
    """
    Use single thread to analyse data (h5) files inside: folder/raw
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
    store = pd.HDFStore(directory + "/analysis_new.h5")
    store['df'] = df  # save it
    store.close()

    return df

if __name__ == "__main__":

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])