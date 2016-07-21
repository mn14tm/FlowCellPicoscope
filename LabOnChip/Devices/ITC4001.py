import visa

class ITC4001:
    def __init__(self, *args, **kwargs):
        super(ITC4001, self).__init__()
        rm = visa.ResourceManager()
        rm.list_resources()
        # ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::12::INSTR')
        self.inst = rm.open_resource('GPIB0::12::INSTR')
        print(self.inst.query("*IDN?"))  # What are you?

    def setup(self):
        # Set TEC setpoint
        self.inst.write('SOUR:TEMP 25C')

    def save_config(self):
        self.inst.write('*SAV 1')

    def load_config(self):
        self.inst.write('*RCL 1')

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



if __name__ == "__main__":
    laserDriver = ITC4001()
    laserDriver.get_optical_power()
