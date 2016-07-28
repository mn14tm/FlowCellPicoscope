from LabOnChip.Devices.ITC4001 import ITC4001
from LabOnChip.Devices.SyringePump import SyringePump
from LabOnChip.Devices.Picoscope import Picoscope
from LabOnChip.Devices.Arduino import Arduino
from LabOnChip.HelperFunctions import folder_analysis, plot_analysis, dilution, sweeps_time, sweeps_number
from datetime import datetime
from twilio.rest import TwilioRestClient


if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID=datetime.now().timestamp(),
               chip='Blank',
               medium='Water (waterbath at 40deg)'
               )

    # Setup laser diode driver
    log["current"] = 0.07  # Laser drive current(A)
    laserDriver = ITC4001()
    laserDriver.set_ld_current(log["current"])
    laserDriver.turn_ld_on()
    log['optical power'] = 0

    # Setup picoscope for logging
    scope = Picoscope()
    scope.openScope()
    scope.show_signal()  # Show a single sweep with the fit
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]

    # Setup syringe pumps
    flow_rate = 1       # Flow rate over photonic chip (ml/min)
    log['flow_rate'] = flow_rate
    water = 1           # Syringe Pump address
    pump = SyringePump()
    pump.send_command(water, 'DIA 26.59')  # Set Syringe Diameter for 60ml syringe

    # Setup Arduino
    arduino = Arduino()
    log['t_in'] = arduino.t_in
    log['t_out'] = arduino.t_out
    log['tempC'] = arduino.tempC
    log['humidity'] = arduino.humidity

    # Clear dispensed volume
    pump.send_command(water, 'CLD INF')

    # Update concentration to save to data files
    log['concentration'] = 0

    # Send rates to pumps
    pump.send_command(water, 'RAT {:.2f} MM'.format(flow_rate))
    pump.send_command(water, 'RUN')

    # Capture and fit single sweeps
    # sweeps_number(sweeps=10, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
    sweeps_time(mins=10, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)

    pump.send_command(water, 'STP')

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