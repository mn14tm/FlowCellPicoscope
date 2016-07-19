import time
import numpy as np

from LabOnChip.Devices.System import System
from LabOnChip.Devices.SyringePump import SyringePump
from LabOnChip.HelperFunctions import analysis
from LabOnChip.HelperFunctions import dilution
from datetime import datetime


if __name__ == "__main__":
    # Measurement Info
    chip = 'T6'
    medium = 'Water 30 deg'
    timestamp = datetime.now().timestamp()  # Unique measurement ID

    # Excitation signal
    current = 0.5  # Laser drive current(A)
    power = 0.27  # power at the photodiode (W)

    # Sample
    flow_rate = 1  # Flow rate over photonic chip (ml/min)

    pump = SyringePump()
    # Syringe Pump addresses
    water = 1

    # Set Syringe Diameter for 60ml syringe
    pump.send_command(water, 'DIA 26.59')

    # Setup picoscope for logging
    scope = System(chip=chip,
                current=current,
                power=power,
                medium=medium,
                timestamp=timestamp)
    scope.openScope()

    # Show a single sweep with the fit
    scope.show_signal()

    # Flush 2 ml/min for 1 min
    pump.send_command(water, 'RAT 2 MM')
    pump.send_command(water, 'RUN')
    time.sleep(60)
    pump.send_command(water, 'STP')

    # Clear dispensed volume
    pump.send_command(water, 'CLD INF')


    # Send to pumps
    pump.send_command(water, 'RAT 1 MM')
    pump.send_command(water, 'RUN')

    # Capture and fit single sweeps
    # scope.sweeps_number(sweeps=50)
    scope.sweeps_time(mins=50)

    pump.send_command(water, 'STP')

    # Stop and close all instruments
    scope.closeScope()
    print('Done')

    # Analyse Data
    print("Analysing data files...")
    analysis(timestamp=timestamp)
    print("Done!")
