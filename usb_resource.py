import falcon
import json


class UsbResource:
    def on_get(self, req, resp):
        resp.text = json.dumps({"ports": ["COM1"]})
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
