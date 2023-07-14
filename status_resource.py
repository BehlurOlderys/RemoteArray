import falcon
import json


class MountStatusResource:
    def __init__(self, available_com_ports):
        self._available = available_com_ports

    # noinspection PyMethodMayBeStatic
    def on_get(self, _req, resp):
        resp.text = json.dumps({"server": "OK", "usb ports": self._available})
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON


class StatusResource:
    # noinspection PyMethodMayBeStatic
    def on_get(self, _req, resp):
        resp.text = json.dumps({"server": "OK"})
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
