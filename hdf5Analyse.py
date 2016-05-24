import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# Calculate lifetime for each sweep
popt = fit_decay(self.x, data)
tau = popt[1]

# Plot histogram
plt.figure(figsize=(10.0, 5.0))
plt.hist(tau, bins=100)
plt.ticklabel_format(useOffset=False)
plt.xlabel('Lifetime (ms)')
plt.ylabel('Frequency')
plt.show()  # Breaks on multithreading for some reason