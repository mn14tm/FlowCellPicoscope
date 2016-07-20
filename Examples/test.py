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
    medium = 'Intralipid (%)'
    timestamp = datetime.now().timestamp()  # Unique measurement ID

    # Excitation signal
    current = 0.2  # Laser drive current(A)
    power = 0.10  # power at the photodiode (W)

    # Liquid Sample
    conc_stock = 20  # % IL of stock solution
    flow_rate = 1  # Flow rate over photonic chip (ml/min)

    # Syringe Pump Setup
    pump = SyringePump()
    # Syringe Pump addresses
    water = 1
    intralipid = 2
    # Set Syringe Diameter for 60ml syringe
    pump.send_command(water, 'DIA 26.59')
    pump.send_command(intralipid, 'DIA 26.59')

    # Picoscope setup for logging
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
    pump.send_command(intralipid, 'CLD INF')

    # Set Flow Rate to desired dilution (ml/min)
    for conc_out in np.linspace(start=0, stop=conc_stock, endpoint=True, num=21):
        # Update concentration to save to data files
        scope.set_concentration(conc_out)

        # Calculate ratio of stock and dilute flow rates
        [vol_dilute, vol_stock] = dilution(conc_out, conc_stock, vol_out=flow_rate)

        # Print
        print('Concentration is {conc:.2f}, flow rate of water {dilute:.2f} and IL {intra:.2f} ml/min'
              .format(conc=conc_out, dilute=vol_dilute, intra=vol_stock))

        # Send to pumps
        pump.send_command(water, 'RAT {:.2f} MM'.format(vol_dilute))
        pump.send_command(intralipid, 'RAT {:.2f} MM'.format(vol_stock))
        pump.send_command(water, 'RUN')
        pump.send_command(intralipid, 'RUN')

        # Capture and fit single sweeps
        # scope.sweeps_number(sweeps=50)
        scope.sweeps_time(mins=4)

        pump.send_command(water, 'STP')
        pump.send_command(intralipid, 'STP')

    # Stop and close all instruments
    scope.closeScope()
    print('Done')

    # Analyse Data
    print("Analysing data files...")
    analysis(timestamp=timestamp)
    print("Done!")
