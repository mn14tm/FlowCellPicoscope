import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import glob as gb
import os

sample = "T16"

df = pd.DataFrame()

# Get list of folders
folders = gb.glob("Data/" + sample + "/*/")
for folder in folders:
    # print(file)

    # Load HDF file
    df_file = pd.read_csv(folder + '/analysis.csv')

    # Add sweep data to measurement dataframe
    df = df.append(df_file)

# Sort rows by datetime
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.set_index('datetime').sort_index()
df = df.reset_index()

# Plot concentration vs lifetime
fig, ax = plt.subplots()
ax.plot(df['concentration'], df['tau'], 'o', alpha=0.3, label=sample)

sample = "T16_2"

df = pd.DataFrame()

# Get list of folders
folders = gb.glob("Data/" + sample + "/*/")
for folder in folders:
    # print(file)

    # Load HDF file
    df_file = pd.read_csv(folder + '/analysis.csv')

    # Add sweep data to measurement dataframe
    df = df.append(df_file)

# Sort rows by datetime
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.set_index('datetime').sort_index()
df = df.reset_index()

# Plot concentration vs lifetime
# fig, ax = plt.subplots()
ax.plot(df['concentration'], df['tau'], 'o', alpha=0.3, label=sample)

plt.ticklabel_format(useOffset=False, axis='y')

ax.set_xlabel('Glucose concentration (mmol)')
ax.set_ylabel('Lifetime (ms)')
ax.grid(True)
plt.legend()

# plt.ylim([8.45, 8.92])
plt.tight_layout()
plt.savefig("Data/" + sample + '/' + sample + '_concVslifetime.png', dpi=1000)

# Bring window to the front (above pycharm)
fig.canvas.manager.window.activateWindow()
fig.canvas.manager.window.raise_()

plt.show()