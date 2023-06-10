import sys
from serial import Serial, SerialException
import logging
import glob
log = logging.getLogger(__name__)


class SerialWriter:
    def __init__(self, port, baud=115200, timeout=0.25):
        self._serial = Serial(port=port, baudrate=baud, timeout=timeout)

    def receive_line(self):
        try:
            return self._serial.readline().decode('UTF-8').rstrip()
        except SerialException:
            log.error(f"Serial exception occured, I guess we should leave now...")
            return None
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            log.error("Serial error while reading: " + message)
            return None

    def send_line(self, strline):
        try:
            self._serial.write((strline + "\n").encode())
            return True
        except SerialException:
            log.error(f"Serial exception occured, I guess we should leave now...")
            return False
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            log.error("Serial error while writing: " + message)
            return False


def get_available_com_ports():
    if sys.platform.startswith('win'):  # TODO: other platforms?
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    else:
        return ["<NONE>"]

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
