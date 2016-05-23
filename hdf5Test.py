import numpy as np
import h5py

from datetime import datetime

m1 = np.random.rand(1000, 20)
m2 = np.random.rand(300, 30)

with h5py.File('data.h5', 'w') as hf:
    hf.create_dataset('dataset_1', data=m1)
    hf.create_dataset('dataset_2', data=m2)