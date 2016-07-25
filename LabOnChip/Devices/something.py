# SyringePump.py

import serial
import time


def format_command(address, command):
    """
    Format a command for transmission to Aladdin pump in Safe Mode.
    Result includes the length and checksum but not the
    start / termination characters (\x02 and \x03).
    @param address: Numeric address of the pump, 0-99, or None.
    @param command: Textual command to send.
    """

    # Confirm address parameter
    if address > 99:
        raise SyntaxError("Invalid Address: %s" % address)
    if address is not None:
        command = "{:02d}{:s}\r\n".format(address, command)
        # print(command)
    return command


def interpret_response(response):
    """
    Parse response from Aladdin pump.
    Returns a tuple (address, status, message)
    @param response: Message received. Should not include the
                     start / termination characters.
    @param basic: Parse in basic mode (no checksum).
    """

    # Reject empty response
    if len(response) == 0:
        raise SyntaxError

    # Basic mode response in format:
    # <address, 2 chars><status, one char><message>
    address = int(response[0:2])
    status = response[2]
    msg = response[3:]

    # Catch errors
    if len(msg) > 0 and msg[0] == '?':
        raise CommandError(msg)

    return address, status, msg


class Error(Exception):
    pass


class CommandError(Error):
    def __init__(self, msg):
        self.msg = msg

        if msg == "?":
            self.type = "Command not recognised"
        elif msg == "?NA":
            self.type = "Command not currently applicable"
        elif msg == "?OOR":
            self.type = "Command data out of range"
        elif msg == "?COM":
            self.type = "Invalid command packet"
        elif msg == "?O":
            self.type = "Command ignored (simultaneous phase start)"

        Error.__init__(self, self.type)


class SyringePump:
    def __init__(self):
        super(SyringePump, self).__init__()
        # Setup serial port to communicate with Aladdin Syringe Pump
        self.syringe_pump = serial.Serial(
            port='COM5',
            baudrate=19200,
            timeout=3
        )
        # Allow serial connection time to setup
        time.sleep(2)  # Could make shorter?

    def send_command(self, address, command):
        command = format_command(address, command)
        self.syringe_pump.write(str.encode(command))
        # Delay between sending commands to allow pump to receive and process
        time.sleep(0.1)

    def get_response(self):
        buffer_string = ''
        buffer_string += self.syringe_pump.read(self.syringe_pump.inWaiting()).decode('utf-8')
        last_received = buffer_string  # [:-2]  # Remove \n and \r
        print(last_received)
