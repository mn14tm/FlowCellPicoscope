import numpy as np
import h5py

with h5py.File('data.h5', 'r') as hf:
    print(hf.keys())