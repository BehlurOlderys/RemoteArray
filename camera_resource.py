import falcon
import json
import time


class CameraResource:
    def on_get(self, req, resp):
        time.sleep(10)
        resp.text = json.dumps({"camera": "OK"})
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
