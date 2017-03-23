import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from labonchip.Methods.HelperFunctions import folder_analysis, sweeps_number, text_when_done


def plot(folder, data_folder='../Data/', save=True):
    import pandas as pd

    # Load HDF file
    df = pd.read_hdf(data_folder + str(folder) + '/analysis.h5')
    chip = df.chip.unique()[0]
    # Create column for time since start of measurement
    df['delta'] = (df['datetime'] - df['datetime'][0]).fillna(0).astype('timedelta64[us]') / (1E6 * 60)

    # Plot in time since beginning of experiment
    from collections import OrderedDict
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    for key, group in df.groupby(['current']):
        ax1.plot(group['delta'], group['tau'], 'o', alpha=0.05, label=key)
        rolling = group['tau'].rolling(window=20).mean()
        ax1.plot(group['delta'], rolling, '-', label='rolling average', color='black')
        ax2.plot(group['delta'], group['A'], 'o', alpha=0.05, label=key)
        rolling = group['A'].rolling(window=20).mean()
        ax2.plot(group['delta'], rolling, '-', label='rolling average', color='black')
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), ncol=2)
    ax2.set_xlabel('Time since start of experiment (Mins)')
    ax1.set_ylabel('Lifetime (ms)')
    ax2.set_ylabel('Amplitude (A.U.)')
    ax1.set_title('Chip: {}'.format(chip))
    if save:
        plt.savefig(data_folder + str(folder) + '/experimental_run')

    # Tau and amp. plots
    df = df[['current', 'pulse_width', 'tau', 'A']]
    g = df.groupby(['current', 'pulse_width']).agg([np.mean, np.std])
    g = g.reset_index()
    # Two subplots, unpack the axes array immediately
    f, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    for key, group in g.groupby('current'):
        ax1.errorbar(group['pulse_width'], group['tau']['mean'], yerr=group['tau']['std'], label=key)
        ax2.errorbar(group['pulse_width'], group['A']['mean'], yerr=group['A']['std'], label=key)
    ax2.set_xlabel('Pulse Width (ms)')
    ax1.set_ylabel('Lifetime (ms)')
    ax2.set_ylabel('Amplitude (A.U.)')
    ax1.set_title('Chip: {}'.format(chip))
    ax2.legend(title='Laser current (A)', loc='best', fontsize='medium')
    if save:
        plt.savefig(data_folder + str(folder) + '/result')

    # Contour plot
    import matplotlib.mlab as ml
    x = g['pulse_width']
    y = g['current']
    z = g['tau']['mean']

    xi = np.linspace(0, 100, 500)
    yi = np.linspace(min(y), max(y), 500)
    zi = ml.griddata(x, y, z, xi, yi, interp='linear')

    fig, ax = plt.subplots()
    # plt.contour(xi, yi, zi, 15, colors='k')
    plt.pcolormesh(xi, yi, zi)
    cbar = plt.colorbar()
    plt.scatter(x, y, marker='o', color='k', s=5, zorder=10)

    plt.xlim(0, max(x))
    plt.ylim(min(y), max(y))
    cbar.ax.set_ylabel('Lifetime (ms)')
    ax.set_xlabel('Pulse width (ms)')
    ax.set_ylabel('Current (mA)')
    if save:
        plt.savefig(data_folder + str(folder) + '/contour_tau')

    z = g['A']['mean']
    zi = ml.griddata(x, y, z, xi, yi, interp='linear')

    fig, ax = plt.subplots()
    # plt.contour(xi, yi, zi, 15, colors='k')  # , linewidths=1
    plt.pcolormesh(xi, yi, zi)
    cbar = plt.colorbar()
    plt.scatter(x, y, marker='o', color='k', s=5, zorder=10)

    plt.xlim(0, max(x))
    plt.ylim(min(y), max(y))
    cbar.ax.set_ylabel('Amplitude (A.U.)')
    ax.set_xlabel('Pulse width (ms)')
    ax.set_ylabel('Current (mA)')
    if save:
        plt.savefig(data_folder + str(folder) + '/contour_A')


def measure():
    from labonchip.Methods.Devices.Arduino import Arduino
    from labonchip.Methods.Devices.ITC4001 import ITC4001
    from labonchip.Methods.Devices.Picoscope import Picoscope

    # Measurement Info Dictionary
    log = dict(measurementID=str(datetime.now().timestamp()),
               chip='T20',
               medium='Air'
               )

    # Make directory to store files
    import os
    directory = '../Data/' + str(log['measurementID']) + "/raw"
    if not os.path.exists(directory):
        os.makedirs(directory)
        os.makedirs('../Data/' + str(log['measurementID']) + "/Plots")

    # How long to capture the decay for (ms) [same as picoscope]
    decay_time = 120

    # Setup devices
    laserDriver = ITC4001()
    laserDriver.setup_980nm_ld()
    laserDriver.set_ld_shape('PULS')
    arduino = Arduino()
    scope = Picoscope()
    scope.openScope()

    # Update Experimental Log
    log['tempC'] = arduino.tempC
    log['humidity'] = arduino.humidity
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Sweep over pump powers (A)
    for current in np.arange(0.1, 0.6, step=0.1)[::-1]:
        print("Measuring at {0:3f}A power:".format(current))
        log["current"] = current  # Laser drive current(A)
        laserDriver.set_ld_current(current)

        # Sweep over pulse times (ms)
        for pulse_duration in [1, 5, 10, 20, 30, 40, 50, 70, 100][::-1]:
            print("Pulse width: {0:.2f}".format(pulse_duration))
            log['pulse_width'] = pulse_duration
            laserDriver.set_qcw(period=(pulse_duration+decay_time)*1e-3, width=pulse_duration*1e-3)

            laserDriver.turn_ld_on()
            time.sleep(3)
            log['optical power'] = laserDriver.get_optical_power()

            # Save plot of the decay
            fig = scope.plot(show=False)
            fig.savefig('../Data/' + str(log['measurementID']) + '/Plots/pulse_duration_{0}_current_{1}.png'.format(
                pulse_duration, current))
            plt.close(fig)  # close the figure

            sweeps_number(sweeps=100, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver,
                          thermocouple=False)
            laserDriver.turn_ld_off()
            time.sleep(1)

    # Stop and close all instruments
    scope.closeScope()
    arduino.close()
    print('Finished measurement.')

    return log['measurementID']


if __name__ == "__main__":
    # Do measurement
    measurementID = measure()
    # Analyse Data
    print("Analysing data files...")
    folder_analysis(measurementID)
    text_when_done()
    print("Done! Now plotting...")
    plot(folder=measurementID)
    # print("Copying files to network...")
    # copy_data(str(log['measurementID']))
    print("Finito!")
