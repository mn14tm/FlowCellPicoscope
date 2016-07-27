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
    log["current"] = 0.07  # Laser drive current(A)
    laserDriver = ITC4001()
    laserDriver.set_ld_current(log["current"])
    laserDriver.turn_ld_on()

    # Setup picoscope for logging
    scope = Picoscope()
    scope.openScope()
    scope.show_signal()  # Show a single sweep with the fit
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Setup Arduino
    arduino = Arduino()
    log['t_in'] = arduino.t_in
    log['t_out'] = arduino.t_out
    log['tempC'] = arduino.tempC
    log['humidity'] = arduino.humidity

    # Setup syringe pumps
    conc_stock = 20     # % IL of stock solution
    flow_rate = 1       # Flow rate over photonic chip (ml/min)
    log['flow_rate'] = flow_rate
    pump = SyringePump()
    pump.send_command(1, 'DIA 26.59')  # Set Syringe Diameter for 60ml syringe

    # Flush 2 ml/min for 1 min
    print("Flushing...")
    pump.send_command(1, 'RAT 2 MM')
    pump.send_command(1, 'RUN')
    time.sleep(6)
    pump.send_command(1, 'STP')
    print("Flush finished!")

    # Clear dispensed volume
    pump.send_command(1, 'CLD INF')

    # Set Flow Rate to desired dilution (ml/min)
    conc_out = 0
    # Update concentration to save to data files
    log['concentration'] = conc_out

    # Calculate ratio of stock and dilute flow rates
    [vol_dilute, vol_stock] = dilution(conc_out, conc_stock, vol_out=flow_rate)
    print('Concentration is {conc:.2f}, flow rate of water {dilute:.2f} and IL {intra:.2f} ml/min'
          .format(conc=conc_out, dilute=vol_dilute, intra=vol_stock))

    # Send rates to pumps
    pump.send_command(1, 'RAT {:.2f} MM'.format(vol_dilute))
    pump.send_command(1, 'RUN')

    # Capture and fit single sweeps
    # scope.sweeps_number(sweeps=50, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
    sweeps_time(mins=1/10, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)

    # Stop pump
    pump.send_command(1, 'STP')

    # Stop and close all instruments
    scope.closeScope()
    laserDriver.turn_ld_off()
    print('Finished measurements.')

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])
    print("Done! Now plotting...")
    # plot_analysis(df, folder=log['measurementID'])
    print("Finito!")
