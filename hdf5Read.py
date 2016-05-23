import numpy as np
import pandas as pd

store = pd.HDFStore('Data/store.h5')
# List keys
store.keys()

# read back in
df = pd.read_hdf('Data/store.h5', 'raw')