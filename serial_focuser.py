from .ascom_focuser import AscomFocuser
import sys
from serial import Serial, SerialException
import glob


def get_available_com_ports():
    if sys.platform.startswith('win'):  # TODO: other platforms?
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for p in ports:
        try:
            s = Serial(p)
            s.close()
            result.append(p)
        except (OSError, SerialException):
            pass
    if not result:
        return ["<NONE>"]
    return result


commands_set = [
    "GET_NAME",
    "IS_MOVING",
    "GET_POSITION",
    "GET_TEMP",
    "HALT",
    "MOVE",
    "IS_ALIVE"
]


def send_command_and_get_response(ser, command):
    """
    Returned message can be:
    GET_NAME: "<some name>"
    IS_MOVING: "True/False" (strings)
    MOVE: "OK"
    GET_POSITION: "123"
    """
    if command not in commands_set:
        raise SerialException(f"Command unknown: {command}!")
    if ser is None:
        raise SerialException("Serial device not available!")

    ser.write(command)
    message = ser.readline().decode('UTF-8').rstrip()
    return message


class SerialFocuser(AscomFocuser):
    def __init__(self, focuser_index, serial_device: Serial):
        self._index = focuser_index
        self._ser = serial_device
        self._maxincrement = 100
        self._maxstep = 10000
        self._stepsize_um = 1  # TODO no idea
        self._name = send_command_and_get_response(self._ser, self._create_command("GET_NAME"))
        self._connected = False

    def _create_command(self, command, argument=None):
        """
        example:
        MOVE@1=23\n
        GET_NAME@3=0\n
        """
        argument_str = f"{str(argument)}" if command == "MOVE" else "0"
        return f"{command}@{self._index}={argument_str}\n".encode()

    def get_absolute(self):
        return False

    def get_ismoving(self):
        return bool(send_command_and_get_response(self._ser, "IS_MOVING") == "True")

    def get_maxincrement(self):
        return self._maxincrement

    def get_maxstep(self):
        return self._maxstep

    def get_position(self):
        return int(send_command_and_get_response(self._ser, "GET_POSITION"))

    def get_stepsize(self):
        return self._stepsize_um

    def get_tempcomp(self):
        return False

    def get_tempcompavailable(self):
        return False

    def get_temperature(self):
        return float(send_command_and_get_response(self._ser, "GET_TEMP"))

    def put_tempcomp(self, value):
        pass  # Does nothing

    def put_halt(self):
        return send_command_and_get_response(self._ser, "HALT")

    def put_move(self, value):
        return send_command_and_get_response(self._ser, "MOVE", value)

    def get_connected(self):
        is_alive = send_command_and_get_response(self._ser, self._create_command("IS_ALIVE"))
        self._connected = bool(is_alive == "True")
        return self._connected

    def get_name(self):
        return self._name

    def get_interfaceversion(self):
        return 1

    def get_description(self):
        return "Serial focuser"

    def get_driverinfo(self):
        return "This is ALPACA driver by Bartlomiej Hnatio"

    def set_connected(self, value):
        self._connected = value
