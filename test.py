import serial
import time
import numpy as np

from enum import Enum     # for enum34, or the stdlib version
from LabOnChip.HelperFunctions import dilution
from LabOnChip.Devices.System import System
from LabOnChip.Devices.SyringePump import SyringePump
from LabOnChip.HelperFunctions import analysis
from LabOnChip.HelperFunctions import dilution
from datetime import datetime


class Liquid(Enum):
    # Pump IDs to make easier to read code
    Water = 1
    Intralipid = 2


if __name__ == "__main__":
    # Measurement Info
    chip = 'T6'
    medium = 'Intralipid (%)'
    timestamp = datetime.now().timestamp()  # Unique measurement ID

    # Excitation signal
    current = 0.5  # Laser drive current(A)
    power = 0.3  # power at the photodiode (W)

    # Sample
    conc_stock = 20  # % IL of stock solution
    flow_rate = 1  # Flow rate over photonic chip (ml/min)

    pump = SyringePump()

    # Syringe Pump addresses
    water = Liquid.Water.value
    intralipid = Liquid.Intralipid.value

    # Set Syringe Diameter for 60ml syringe
    pump.send_command(water, 'DIA 26.59')
    pump.send_command(intralipid, 'DIA 26.59')

    # Setup picoscope for logging
    scope = System(chip=chip,
                current=current,
                power=power,
                medium=medium,
                timestamp=timestamp)
    scope.openScope()

    # Show a single sweep with the fit
    scope.show_signal()

    # Set Flow Rate to desired dilution (ml/min)
    for conc_out in range(20):
        # Update concentration to save to data files
        scope.set_concentration(conc_out)

        # Calculate ratio of stock and dilute flow rates
        [vol_dilute, vol_stock] = dilution(conc_out, conc_stock, vol_out=flow_rate)

        # Send to pumps
        pump.send_command(water, 'RAT {:.2f} MM'.format(vol_dilute))
        pump.send_command(intralipid, 'RAT {:.2f} MM'.format(vol_stock))
        pump.send_command(water, 'RUN')
        pump.send_command(intralipid, 'RUN')

        # Capture and fit single sweeps
        scope.sweeps_number(sweeps=20)
        # scope.sweeps_time(mins=1)

    # Stop and close all instruments
    scope.closeScope()
    pump.send_command(water, 'STP')
    pump.send_command(intralipid, 'STP')
    print('Done')

    # Analyse Data
    print("Analysing data files...")
    analysis(timestamp=timestamp)
    print("Done!")
