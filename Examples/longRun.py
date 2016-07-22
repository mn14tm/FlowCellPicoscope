from LabOnChip.Devices.System import System
from LabOnChip.Devices.ITC4001 import ITC4001
from LabOnChip.HelperFunctions import analysis

from datetime import datetime


if __name__ == "__main__":
    # Measurement Info
    chip = 'T6'
    medium = 'Water'
    timestamp = datetime.now().timestamp()  # Unique measurement ID

    # Excitation signal
    current = 0.5  # Laser drive current(A)

    # Setup laser diode driver
    laserDriver = ITC4001()
    laserDriver.set_ld_current(current)
    laserDriver.turn_ld_on()
    power = laserDriver.get_optical_power()  # power at the photodiode (W)

    # Setup picoscope for logging
    scope = System(chip=chip,
                   current=current,
                   medium=medium,
                   timestamp=timestamp)
    scope.openScope()

    # Capture and fit single sweeps
    try:
        while True:
            scope.set_power(laserDriver.get_optical_power())
            scope.single_sweep()
    except KeyboardInterrupt:
        pass

    # Stop and close all instruments
    scope.closeScope()
    laserDriver.turn_ld_off()
    print('Done')

    # Analyse Data
    print("Analysing data files...")
    analysis(timestamp=timestamp)
    print("Done!")
