from datetime import datetime

from labonchip.Methods.Devices.ITC4001 import ITC4001
from labonchip.Methods.Devices.System import System
from labonchip.Methods.HelperFunctions import folder_analysis, plot_analysis

if __name__ == "__main__":
    # Measurement Info
    chip = 'T6'
    medium = 'Water'
    measurementID = datetime.now().timestamp()  # Unique measurement ID

    # Excitation signal
    current = 0.5  # Laser drive current(A)

    # Setup laser diode driver
    laserDriver = ITC4001()
    laserDriver.set_ld_current(current)
    laserDriver.turn_ld_on()

    # Setup picoscope for logging
    scope = System(chip=chip,
                   current=current,
                   medium=medium,
                   timestamp=measurementID)
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
    df = folder_analysis(measurementID)
    print("Done! Now plotting...")
    plot_analysis(df, folder=measurementID)
    print("Finito!")
