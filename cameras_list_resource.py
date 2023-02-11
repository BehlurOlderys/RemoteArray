import falcon
import json
from .zwo_asi_camera_grabber import ASICamera


class CamerasListResource:
    def __init__(self, cameras: dict):
        self._cameras = cameras

    def on_get(self, req, resp):
        try:
            resp.text = json.dumps({"cameras": [self._cameras]})
            resp.status = falcon.HTTP_200
        except RuntimeError as re:
            resp.text = json.dumps({"error": repr(re)})
            resp.status = falcon.HTTP_503
        finally:
            resp.content_type = falcon.MEDIA_JSON
