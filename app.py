import falcon
from .status_resource import StatusResource
from .camera_resource import CameraResource
from .cameras_list_resource import CamerasListResource
from .camera_connected_resource import CameraConnectedResource
from .zwo_asi_camera_grabber import ASICamera
from .camera_capture_resource import CameraCaptureResource
from .image_download_resource import ImageDownloadResource


class DefaultCaptureFilenameGenerator:
    def __init__(self, prefix):
        self._number = 0
        self._prefix = prefix

    def generate(self):
        fn = self._prefix + "_Capture_{0:05d}.png".format(self._number)
        self._number += 1
        return fn


class DummyResource:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_501


ASICamera.initialize_library()
cameras = ASICamera.get_cameras_list()
cameras_dict = dict(zip(range(0, len(cameras)), cameras))
cameras_dict = {i: {"name": n,
                    "id": i,
                    "instance": ASICamera(i),
                    "image_path": "",
                    "generator": DefaultCaptureFilenameGenerator(f"camera_{i}")} for i, n in cameras_dict.items()}

app = application = falcon.App()


app.add_route("/status", StatusResource())
app.add_route("/cameras/list", CamerasListResource(cameras_dict))
app.add_route("/camera/{camera_id}/connected", CameraConnectedResource(cameras_dict))
app.add_route("/camera/{camera_id}/capture", CameraCaptureResource(cameras_dict))
app.add_route("/camera/{camera_id}/images/status/{image_name}", DummyResource()) #ImageStatusResource(cameras_dict))
app.add_route("/camera/{camera_id}/images/download/{image_name}", ImageDownloadResource(cameras_dict))
