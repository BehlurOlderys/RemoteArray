import falcon
import json


class CamerasListResource:
    def __init__(self, cameras: dict):
        self._cameras = cameras

    def on_get(self, _req, resp):
        try:
            resp.text = json.dumps({"cameras": [v["name"] for k, v in self._cameras.items()]})
            resp.status = falcon.HTTP_200
        except RuntimeError as re:
            resp.text = json.dumps({"error": repr(re)})
            resp.status = falcon.HTTP_503
        finally:
            resp.content_type = falcon.MEDIA_JSON
