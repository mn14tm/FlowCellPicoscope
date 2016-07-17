import numpy as np

from LabOnChip.Devices.System import System
from LabOnChip.HelperFunctions import analysis
from LabOnChip.HelperFunctions import dilution
from datetime import datetime


if __name__ == "__main__":
    chip = 'T6'
    current = 0.5  # Laser drive current(A)
    power = 0.3  # power at the photodiode (W)

    # Unique measurement ID
    timestamp = datetime.now().timestamp()
    # self.timestamp = timestamp  # Allow Analysis to access this variable

    medium = 'Water - 20% Intralipid switch every min'
    # medium = 'Water'
    # medium = 'Aqueous Glucose (%% Weight)'
    concentration = np.nan
    # concentration = 48
    print("Measuring concentration: {conc}".format(conc=concentration))

    dm = System(chip=chip,
                current=current,
                power=power,
                medium=medium,
                concentration=concentration,
                timestamp=timestamp)

    # # Show a single sweep with the fit
    # dm.show_signal()

    # Capture and fit single sweeps while logging temperature
    dm.sweeps_number(sweeps=20)
    # dm.sweeps_time(mins=1)

    print("Analysing data files...")
    analysis(timestamp=timestamp)
    print("Done!")
