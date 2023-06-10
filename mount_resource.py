from .utils import add_timestamp_before, add_timestamp_after
import falcon
import logging
import json
from traceback import format_exc
from .serial_utils import get_available_com_ports, SerialWriter


log = logging.getLogger("mount")


class MountResource:
    def __init__(self, serial):
        self._serial = serial
        self._last_timestamp = None

    def set_timestamp(self, t):
        self._last_timestamp = t

    def get_timestamp(self):
        return self._last_timestamp

    def _set_serial(self, serial):
        self._serial = serial

    @falcon.before(add_timestamp_before)
    @falcon.after(add_timestamp_after)
    def on_get(self, req: falcon.Request, resp: falcon.Response, command_name):
        if command_name == "list_ports":
            ports = get_available_com_ports
            resp.text = json.dumps({"ports": ports})
            resp.status = falcon.HTTP_200
            return
        resp.status = falcon.HTTP_501

    @falcon.before(add_timestamp_before)
    @falcon.after(add_timestamp_after)
    def on_put(self, req: falcon.Request, resp: falcon.Response, command_name):
        log.debug(f"PUT {command_name}")
        form = req.media
        log.info(f"Send form = {form}")
        try:
            value = form["Value"]
        except Exception as e:
            log.warning(f"Could not read params: {repr(e)}")
            resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
            resp.status = falcon.HTTP_400
            return
        if command_name == "set_serial":
            self._set_serial(SerialWriter(port=value))
            resp.status = falcon.HTTP_200
            return
        if command_name == "move_ra":
            arcseconds = int(value)
            self._serial.send_line(f"MOVE_RA_AS {arcseconds}")
            resp.status = falcon.HTTP_200
            return
        if command_name == "move_dec":
            arcseconds = int(value)
            self._serial.send_line(f"MOVE_DEC_AS {arcseconds}")
            resp.status = falcon.HTTP_200
            return
        resp.status = falcon.HTTP_501
