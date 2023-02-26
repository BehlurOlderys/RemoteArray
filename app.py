import falcon
import logging
from .status_resource import StatusResource
from .camera_resource import CameraResource
from .cameras_list_resource import CamerasListResource
from .zwo_camera import ZwoCamera
from .camera_capture_resource import CameraCaptureResource
from .image_download_resource import ImageDownloadResource
from datetime import datetime
import os


class DefaultServerTransactionIDGenerator:
    def __init__(self):
        self._counter = 0

    def generate(self):
        r = self._counter
        self._counter += 1
        return r


class DefaultCaptureFilenameGenerator:
    def __init__(self, prefix):
        self._last_dir = None
        self._number = 0
        self._prefix = prefix

    def generate(self):
        current_day = datetime.now().strftime("%Y-%m-%d")
        new_dir = os.path.join(os.getcwd(), "capture", current_day)

        if self._last_dir is None:
            self._last_dir = new_dir
            os.makedirs(self._last_dir)

        elif self._last_dir != new_dir:
            os.makedirs(os.path.join(os.getcwd(), self._last_dir))
            self._last_dir = new_dir

        dt_string = datetime.now().strftime("_%Y%m%d_%H%M%S")
        fn = self._prefix + dt_string + "_Capture_{0:05d}.tif".format(self._number)
        fp = os.path.join(self._last_dir, fn)
        self._number += 1
        return fp


log = logging.getLogger('main')
log.setLevel(logging.DEBUG)
mainHandler = logging.FileHandler('main.log')
formatter = logging.Formatter('%(levelname)s: %(asctime)s %(filename)s %(funcName)s(%(lineno)d) -- %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
mainHandler.setFormatter(formatter)
log.addHandler(mainHandler)


ZwoCamera.initialize_library()
cameras = ZwoCamera.get_cameras_list()
cameras_dict = dict(zip(range(0, len(cameras)), cameras))
cameras_dict = {i: {"name": n,
                    "id": i,
                    "instance": ZwoCamera(i),
                    "image_path": "",
                    "generator": DefaultCaptureFilenameGenerator(f"camera_{i}")} for i, n in cameras_dict.items()}

app = application = falcon.App()


for k, v in cameras_dict.items():
    inst = v["instance"]
    log.debug(inst.get_property())
    for kk, vv in inst.get_controls().items():
        log.debug(vv)

server_transaction_id_generator = DefaultServerTransactionIDGenerator()
camera_resource = CameraResource(cameras_dict, server_transaction_id_generator)

app.add_route("/api/v1/status", StatusResource())
app.add_route("/api/v1/cameras/list", CamerasListResource(cameras_dict))
app.add_route("/api/v1/camera/{camera_id}/capture", CameraCaptureResource(cameras_dict))
app.add_route("/api/v1/camera/{camera_id}/images/download/{image_name}", ImageDownloadResource(cameras_dict))
app.add_route("/api/v1/camera/{camera_id}/{setting_name}", camera_resource)
