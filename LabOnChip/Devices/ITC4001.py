import visa


class ITC4001:
    def __init__(self, *args, **kwargs):
        super(ITC4001, self).__init__()
        rm = visa.ResourceManager()
        # rm.list_resources()
        self.inst = rm.open_resource('USB0::0x1313::0x804A::M00315699::INSTR')
        # print(self.inst.query("*IDN?"))  # What are you?

    def setup(self):
        # Set TEC setpoint
        self.inst.write('SOUR:TEMP 25C')
        # Set LD current setpoint
        self.inst.write('SOUR:CURR 0.5')
        # # Set TEC setpoint
        # self.inst.write('')

    def setup_1618nm(self):
        # Set TEC setpoint
        self.inst.write('SOUR:TEMP 25C')
        # Set LD current setpoint
        self.inst.write('SOUR:CURR:LIM 0.4')
        # # Set TEC setpoint
        # self.inst.write('')

    def set_ld_current(self, current):
        # Set LD current limit
        self.inst.write('SOUR:CURR {:.2f}'.format(current))

    def turn_ld_on(self):
        self.inst.write('OUTP ON')

    def turn_ld_off(self):
        self.inst.write('OUTP OFF')

    def get_optical_power(self):
        # Measures LD power via PD
        return self.inst.query("MEAS:POWer2?")

    def set_qcw(self):
        # Set source period to 200 ms
        self.inst.write('SOUR:PULS:PER 0.2')
        # Set source period to 50 ms
        self.inst.write('SOUR:PULS:PER 0.05')
        # Set trigger source to internal
        self.inst.write('TRIG:SOUR INT')

    def save_config(self, loc=1):
        self.inst.write('*SAV {:s}'.format(loc))

    def load_config(self, loc=1):
        self.inst.write('*RCL {:s}'.format(loc))
