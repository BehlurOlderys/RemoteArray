import falcon
import logging
from .status_resource import StatusResource
from .camera_settings_resource import CameraSettingsResource
from .cameras_list_resource import CamerasListResource
from .camera_connected_resource import CameraConnectedResource
from .zwo_asi_camera_grabber import ASICamera
from .camera_capture_resource import CameraCaptureResource
from .image_download_resource import ImageDownloadResource

from datetime import datetime


class DefaultServerTransactionIDGenerator:
    def __init__(self):
        self._counter = 0

    def generate(self):
        r = self._counter
        self._counter += 1
        return r


class DefaultCaptureFilenameGenerator:
    def __init__(self, prefix):
        self._number = 0
        self._prefix = prefix

    def generate(self):
        dt_string = datetime.now().strftime("_%Y%m%d_%H%M%S")
        fn = self._prefix + dt_string + "_Capture_{0:05d}.png".format(self._number)
        self._number += 1
        return fn


class DummyResource:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_501


log = logging.getLogger('main')
log.setLevel(logging.DEBUG)
mainHandler = logging.FileHandler('main.log')
formatter = logging.Formatter('%(levelname)s: %(asctime)s %(filename)s %(funcName)s(%(lineno)d) -- %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
mainHandler.setFormatter(formatter)
log.addHandler(mainHandler)


ASICamera.initialize_library()
cameras = ASICamera.get_cameras_list()
cameras_dict = dict(zip(range(0, len(cameras)), cameras))
cameras_dict = {i: {"name": n,
                    "id": i,
                    "instance": ASICamera(i),
                    "image_path": "",
                    "generator": DefaultCaptureFilenameGenerator(f"camera_{i}")} for i, n in cameras_dict.items()}

app = application = falcon.App()


server_transaction_id_generator = DefaultServerTransactionIDGenerator()

app.add_route("/api/v1/status", StatusResource())
app.add_route("/api/v1/cameras/list", CamerasListResource(cameras_dict))
# app.add_route("/api/v1/camera/{camera_id}/connected", CameraConnectedResource(cameras_dict))
app.add_route("/api/v1/camera/{camera_id}/capture", CameraCaptureResource(cameras_dict))
app.add_route("/api/v1/camera/{camera_id}/images/status/{image_name}", DummyResource()) #ImageStatusResource(cameras_dict))
app.add_route("/api/v1/camera/{camera_id}/images/download/{image_name}", ImageDownloadResource(cameras_dict))
app.add_route("/api/v1/camera/{camera_id}/{setting_name}", CameraSettingsResource(cameras_dict, server_transaction_id_generator))


