from .utils import add_timestamp_before, add_timestamp_after
import falcon
import logging
import json
from traceback import format_exc


log = logging.getLogger("focuser")


class FocuserResource:
    def __init__(self, serial):
        self._serial = serial
        self._last_timestamp = None

    def set_timestamp(self, t):
        self._last_timestamp = t

    def get_timestamp(self):
        return self._last_timestamp

    def _check_for_serial_error(self, resp):
        if self._serial.get_error():
            resp.text = json.dumps(
                {"Status": "Error", "Message": self._serial.get_error_msg()})
            resp.status = falcon.HTTP_500
            return False
        return True

    def _check_right_focuser_number(self, focuser_no, resp):
        max_focusers = 3            #TODO: more than 3!!!

        if focuser_no < 0 or focuser_no > (max_focusers-1):

            resp.text = json.dumps(
                {"Status": "Error",
                 "Message": f"Focuser number {focuser_no} out of range!"})
            resp.status = falcon.HTTP_412
            return False
        return True

    @falcon.before(add_timestamp_before)
    @falcon.after(add_timestamp_after)
    def on_get(self, req: falcon.Request, resp: falcon.Response, device_number, command_name):
        focuser_number = int(device_number)
        if not self._check_right_focuser_number(focuser_number, resp):
            return

        if command_name == "status":
            if not self._check_for_serial_error(resp):
                return
            resp.text = json.dumps({"Status": "OK"})
            resp.status = falcon.HTTP_200
            return

        resp.status = falcon.HTTP_501

    @falcon.before(add_timestamp_before)
    @falcon.after(add_timestamp_after)
    def on_put(self, req: falcon.Request, resp: falcon.Response, device_number, command_name):
        log.debug(f"PUT {command_name}")
        form = req.media
        log.info(f"Send form = {form}")

        focuser_number = int(device_number)
        if not self._check_right_focuser_number(focuser_number, resp):
            return
        try:
            value = form["Value"]
        except Exception as e:
            log.warning(f"Could not read params: {repr(e)}")
            resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
            resp.status = falcon.HTTP_400
            return
        if command_name == "move_relative":
            if not self._check_for_serial_error(resp):
                return
            steps = int(value)
            command_line = f"F{focuser_number+1}REL {steps}"
            self._serial.send_line(command_line)
            resp.text = json.dumps({"Status": "OK", "Command send": command_line})
            resp.status = falcon.HTTP_200
            return
        resp.status = falcon.HTTP_501
