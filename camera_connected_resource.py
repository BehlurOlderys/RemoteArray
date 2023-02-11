import falcon
import json
from .camera_server_utils import check_camera_id
from .zwo_asi_camera_grabber import ASICamera


class CameraConnectedResource:
    def __init__(self, cameras: dict):
        self._cameras = cameras

    def on_get(self, req, resp, camera_id):
        check_camera_id(camera_id, self._cameras, resp)

    def on_put(self, req, resp, camera_id):
        resp.status = falcon.HTTP_501
