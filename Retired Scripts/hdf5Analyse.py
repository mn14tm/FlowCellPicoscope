"""
Analyse all hdf5 files in Data folder and dump into a CSV/pickle.
"""

import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import glob as gb
import os
from tqdm import tqdm
from scipy.optimize import curve_fit


def mono_exp_decay(t, a, tau, c):
    """ Mono-exponential fitting function. t is the time."""
    return a * np.exp(-t / tau) + c


def fit_decay(t, y):
    """ Function to fit the data, y, to the mono-exponential fitting."""
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


files = gb.glob('Data/Collimated Beam/**/*.h5', recursive=True)

df = pd.DataFrame()
for file in tqdm(files):
    try:
        # Load HDF file
        store = pd.HDFStore(file)

        df_file = store['log']
        df_file['folder'] = file.split(os.sep)[1]

        # Convert datatypes
        df_file['tempC'] = df_file['tempC'].apply(float)
        df_file['humidity'] = df_file['humidity'].apply(float)
        df_file['chip'] = df_file['chip'].apply(str)
        df_file['medium'] = df_file['medium'].apply(str)

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

    except:
        print(file)
        popt = [np.nan,  np.nan, np.nan]

    # Append lifetime to dataframe
    df_file['a'] = popt[0]
    df_file['tau'] = popt[1]
    df_file['c'] = popt[2]

    # Add sweep data to measurement dataframe
    df = df.append(df_file)

# Sort rows by datetime
df = df.set_index('datetime').sort_index()
df = df.reset_index()

# Save df
store = pd.HDFStore('store_collimated.h5')
store['df'] = df  # save it
# store['df']  # load it

store.close()

df.to_csv('store_collimated.csv')
