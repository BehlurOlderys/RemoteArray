import falcon
import logging
from .status_resource import StatusResource
from .camera_resource import CameraResource
from .cameras_list_resource import CamerasListResource
from .zwo_camera import ZwoCamera
from .camera_capture_resource import CameraCaptureResource
from .image_download_resource import ImageDownloadResource
from .app_utils import add_log, DefaultCaptureFilenameGenerator, DefaultServerTransactionIDGenerator


log = add_log("main")


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
