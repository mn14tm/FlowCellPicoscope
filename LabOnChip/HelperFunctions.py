import numpy as np
import matplotlib.dates as mdates
import pandas as pd
import matplotlib.pyplot as plt
import glob as gb

from scipy.optimize import curve_fit


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

def analysis(timestamp):
    # Analyse data in the folder named timestamp kwarg

    # Empty data frame to append results to
    df = pd.DataFrame()

    # for folder in timestamped folder folder:
    for file in gb.glob("Data/" + str(timestamp) + "/raw/*.h5"):
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