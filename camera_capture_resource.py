import falcon.status_codes

from .camera_server_utils import check_camera_id
import json


class CameraCaptureResource:
    def __init__(self, cameras: dict):
        self._cameras = cameras

    def on_post(self, req, resp, camera_id):

        if not check_camera_id(camera_id, self._cameras, resp):
            print(f"POST on capture failed!")
            return
        try:
            generator = self._cameras[int(camera_id)]["generator"]
            raw_data = json.load(req.bounded_stream)
            print(f"Acquired some data from POST on capture endpoint: {raw_data}")
        except json.JSONDecodeError:
            print(f"No data passed, using previous settings for capture")

        image_id = generator.generate()
        camera = self._cameras[int(camera_id)]["instance"]
        camera.set_exposure_us(200000)
        camera.capture_file(image_id)
        resp.text = json.dumps({"image_id": image_id})
        resp.status = falcon.HTTP_202

