import falcon
from .status_resource import StatusResource
from .camera_process_resource import CameraProcessResource
from .zwo_camera import ZwoCamera
from .app_utils import add_log, DefaultServerTransactionIDGenerator
from .camera_process import camera_process, CameraProcessInfo, CameraProcessHandle

from multiprocessing import Event, Pipe, Process


def create_camera_process(cid: int, cname: str):
    kill_event = Event()
    command_pipe_recv, command_pipe_send = Pipe()
    result_pipe_recv, result_pipe_send = Pipe()
    data_pipe_recv, data_pipe_send = Pipe()

    info = CameraProcessInfo(cid=cid,
                             command=command_pipe_recv,
                             result=result_pipe_send,
                             data=data_pipe_send,
                             ke=kill_event)
    p = Process(target=camera_process, args=(info,))
    p.start()

    return CameraProcessHandle(info, p, cname,
                               result_pipe=result_pipe_recv,
                               command_pipe=command_pipe_send,
                               data_pipe=data_pipe_recv)


log = add_log("main")


ZwoCamera.initialize_library()
cameras = ZwoCamera.get_cameras_list()


camera_processes = {cid: create_camera_process(cid, cname) for cid, cname in enumerate(cameras)}

app = application = falcon.App()


server_transaction_id_generator = DefaultServerTransactionIDGenerator()
camera_resource = CameraProcessResource(camera_processes, server_transaction_id_generator)

app.add_route("/api/v1/status", StatusResource())
# app.add_route("/api/v1/cameras/list", CamerasListResource(cameras_dict))
app.add_route("/api/v1/camera/{camera_id}/{setting_name}", camera_resource)
