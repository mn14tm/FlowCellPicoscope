import time
import numpy as np

from LabOnChip.Devices.ITC4001 import ITC4001
from LabOnChip.Devices.SyringePump import SyringePump
from LabOnChip.Devices.Picoscope import Picoscope
from LabOnChip.Devices.Arduino import Arduino
from LabOnChip.HelperFunctions import folder_analysis, plot_analysis, dilution, sweeps_time
from datetime import datetime


if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID=datetime.now().timestamp(),
               chip='T6',
               medium='Intralipid (%)'
               )

    # Setup laser diode driver
    log["current"] = 0.1  # Laser drive current(A)
    laserDriver = ITC4001()
    laserDriver.set_ld_current(log["current"])
    laserDriver.turn_ld_on()

    # Setup picoscope for logging
    scope = Picoscope()
    scope.openScope()
    scope.show_signal()  # Show a single sweep with the fit

    # Setup Arduino
    arduino = Arduino()

    # Setup syringe pumps
    conc_stock = 20     # % IL of stock solution
    flow_rate = 1       # Flow rate over photonic chip (ml/min)
    water = 1           # Syringe Pump address
    intralipid = 2      # Syringe Pump address
    pump = SyringePump()
    pump.send_command(water, 'DIA 26.59')  # Set Syringe Diameter for 60ml syringe
    pump.send_command(intralipid, 'DIA 26.59')

    # Flush 2 ml/min for 1 min
    print("Flushing...")
    pump.send_command(water, 'RAT 2 MM')
    pump.send_command(water, 'RUN')
    time.sleep(60)
    pump.send_command(water, 'STP')
    print("Flush finished!")

    # Clear dispensed volume
    pump.send_command(water, 'CLD INF')
    pump.send_command(intralipid, 'CLD INF')

    # Set Flow Rate to desired dilution (ml/min)
    for conc_out in np.linspace(start=0, stop=conc_stock, endpoint=True, num=21):
        # Update concentration to save to data files
        log['concentration'] = conc_out

        # Calculate ratio of stock and dilute flow rates
        [vol_dilute, vol_stock] = dilution(conc_out, conc_stock, vol_out=flow_rate)
        print('Concentration is {conc:.2f}, flow rate of water {dilute:.2f} and IL {intra:.2f} ml/min'
              .format(conc=conc_out, dilute=vol_dilute, intra=vol_stock))

        # Send rates to pumps
        pump.send_command(water, 'RAT {:.2f} MM'.format(vol_dilute))
        pump.send_command(intralipid, 'RAT {:.2f} MM'.format(vol_stock))
        pump.send_command(water, 'RUN')
        pump.send_command(intralipid, 'RUN')

        # Capture and fit single sweeps
        # scope.sweeps_number(sweeps=50)
        sweeps_time(mins=5, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)

        pump.send_command(water, 'STP')
        pump.send_command(intralipid, 'STP')

    # Stop and close all instruments
    scope.closeScope()
    laserDriver.turn_ld_off()
    print('Finished measurements.')

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])
    print("Done! Now plotting...")
    plot_analysis(df, folder=log['measurementID'])
    print("Finito!")
