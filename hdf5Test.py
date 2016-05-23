import numpy as np
import pandas as pd
import h5py

from datetime import datetime

m1 = np.random.rand(1000)
m2 = np.random.rand(300, 30)

store = pd.HDFStore('Data/store.h5')

time = np.linspace(0, 100, 1000)
data = "Hi tyhert"

raw = pd.DataFrame({"time":time, 'data':data})

m1 = pd.Series(m1)

store.put('m1', m1)
store.put('raw', raw)
# store['m2'] = m2

store.close()