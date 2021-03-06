import visa


class ITC4001:
    def __init__(self, *args, **kwargs):
        super(ITC4001, self).__init__()
        rm = visa.ResourceManager()
        # rm.list_resources()
        self.inst = rm.open_resource('USB0::0x1313::0x804A::M00315699::INSTR')
        # self.inst = rm.open_resource('USB0::0x1313::0x804A::M00314891::INSTR')
        # print(self.inst.query("*IDN?"))  # What are you?
        # Turn TEC on
        self.inst.write('OUTP2:STAT ON')

    def setup_980nm_ld(self):
        """ Setup parameters for 980nm laser diode. """
        # Set TEC setpoint
        self.inst.write('SOUR:TEMP 25C')
        # Set LD current setpoint
        self.inst.write('SOUR:CURR LIM 0.5')

    def setup_1618nm_ld(self):
        """ Setup parameters for 1618nm laser diode. """
        # Set TEC setpoint
        self.inst.write('SOUR:TEMP 25C')
        # Set LD current setpoint
        self.inst.write('SOUR:CURR:LIM 0.4')

    def set_ld_shape(self, shape='DC'):
        """Set CW(DC) or QCW(PULSe) mode"""
        self.inst.write('SOUR:FUNC:SHAP {:s}'.format(shape))

    def set_ld_current(self, current):
        # Set LD current setpoint
        self.inst.write('SOUR:CURR {:.2f}'.format(current))

    def turn_ld_on(self):
        # Turn laser diode on
        self.inst.write('OUTP ON')

    def turn_ld_off(self):
        # Turn laser diode off
        self.inst.write('OUTP OFF')

    def get_optical_power(self):
        # Measures laser diode power via PD
        return float(self.inst.query("MEAS:POWer2?"))

    def set_qcw(self, period=0.2, width=0.05):
        # Set QCW pulse
        # Set source pulse period (s)
        self.inst.write('SOUR:PULS:PER {:.3f}'.format(period))
        # Set pulse width (s)
        self.inst.write('SOUR:PULS:WIDT {:.3f}'.format(width))
        # Set trigger source to internal
        self.inst.write('TRIG:SOUR INT')

    def save_config(self, loc=1):
        self.inst.write('*SAV {:s}'.format(loc))

    def load_config(self, loc=1):
        self.inst.write('*RCL {:s}'.format(loc))

    def clear(self):
        """Clears the event registers in all register groups. This command also clears the error queue."""
        self.inst.write('*CLS')

    def print_error(self):
        print(self.inst.query('SYST:ERR?'))

    def user_write(self, string):
        self.inst.write(string)

    def user_query(self, string):
        self.inst.query(string)
