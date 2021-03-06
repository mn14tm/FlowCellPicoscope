import time
from datetime import datetime

import numpy as np
from labonchip.Methods.Devices.Arduino import Arduino
from labonchip.Methods.Devices.Picoscope import Picoscope
from labonchip.Methods.Devices.ITC4001 import ITC4001
from labonchip.Methods.HelperFunctions import folder_analysis, plot_analysis, dilution, \
    sweeps_number

if __name__ == "__main__":
    # Measurement Info Dictionary
    log = dict(measurementID=datetime.now().timestamp(),
               chip='T2',
               medium='D2o (%)'
               )

    # Setup laser diode driver
    log["current"] = 0.5  # Laser drive current(A)
    laserDriver = ITC4001()
    laserDriver.set_ld_current(log["current"])
    laserDriver.turn_ld_on()
    log['optical power'] = laserDriver.get_optical_power()

    # Setup picoscope for logging
    scope = Picoscope()
    scope.openScope()
    scope.show_signal()  # Show a single sweep with the fit
    log['fs'] = scope.res[0]
    log['sample_no'] = scope.res[1]
    laserDriver.turn_ld_off()

    # Setup Arduino
    arduino = Arduino()
    log['t_in'] = arduino.t_in
    log['t_out'] = arduino.t_out
    log['tempC'] = arduino.tempC
    log['humidity'] = arduino.humidity

    # Setup syringe pumps
    conc_stock = 100     # % IL of stock solution
    flow_rate = 1        # Flow rate over photonic chip (ml/min)
    log['flow_rate'] = flow_rate
    water = 1           # Syringe Pump address
    intralipid = 2      # Syringe Pump address
    pump = SyringePump()
    pump.send_command(water, 'DIA 26.59')  # Set Syringe Diameter for 60ml syringe
    pump.send_command(intralipid, 'DIA 26.59')

    # Clear dispensed volume
    pump.send_command(water, 'CLD INF')
    pump.send_command(intralipid, 'CLD INF')

    # Flush 2 ml/min for 1 min
    print("Flushing water...")
    pump.send_command(water, 'RAT 1 MM')
    pump.send_command(water, 'RUN')
    # time.sleep(60)
    pump.send_command(water, 'STP')
    print("Flush finished!")

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

        # 1 Min flush
        time.sleep(55)
        # Sweep over various pump powers
        for current in [0.5, 0.4, 0.3, 0.2, 0.1]:
            log["current"] = current  # Laser drive current(A)
            laserDriver.set_ld_current(log["current"])
            laserDriver.turn_ld_on()
            time.sleep(5)  # Wait for laser driver to fire up
            log['optical power'] = laserDriver.get_optical_power()

            # Capture and fit single sweeps
            sweeps_number(sweeps=250, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
            # sweeps_time(mins=1, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
            laserDriver.turn_ld_off()

        # Capture and fit single sweeps
        # sweeps_number(sweeps=250, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)
        # sweeps_time(mins=5, log=log, arduino=arduino, scope=scope, laserDriver=laserDriver)

        pump.send_command(water, 'STP')
        pump.send_command(intralipid, 'STP')

    # Stop and close all instruments
    scope.closeScope()
    laserDriver.turn_ld_off()
    print('Finished measurements.')

    # Flush 1 ml/min for 1 min
    print("Flushing with water...")
    pump.send_command(intralipid, 'RAT 1 MM')
    pump.send_command(intralipid, 'RUN')
    time.sleep(60)
    pump.send_command(intralipid, 'STP')
    print("End flush finished!")

    # Analyse Data
    print("Analysing data files...")
    df = folder_analysis(log['measurementID'])
    print("Done! Now plotting...")
    plot_analysis(df, folder=log['measurementID'])
    print("Finito!")

    # Alert me via text
    text_when_done()
