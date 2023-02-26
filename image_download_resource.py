from .camera_server_utils import check_camera_id
import os


class ImageDownloadResource:
    def __init__(self, cameras):
        self._cameras = cameras

    def on_get(self, _req, resp, camera_id, image_name):
        if not check_camera_id(camera_id, self._cameras, resp):
            return

        resp.content_type = "image/png"

        image_path = os.path.join(self._cameras[int(camera_id)]["image_path"], image_name)
        resp.stream = open(image_path, 'rb')
        resp.content_length = os.path.getsize(image_path)
