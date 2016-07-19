import visa

class ITC4001:
    def __init__(self, *args, **kwargs):
        super(ITC4001, self).__init__()
        rm = visa.ResourceManager()
        rm.list_resources()
        # ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::12::INSTR')
        self.inst = rm.open_resource('GPIB0::12::INSTR')
        print(self.inst.query("*IDN?"))  # What are you?

    # def setup(self):

    def get_optical_power(self):
        self.inst.query("")


if __name__ == "__main__":
    laserDriver = ITC4001()
    laserDriver.get_optical_power()
