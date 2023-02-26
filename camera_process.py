import logging
from multiprocessing import Event, Pipe
from zwo_camera import ZwoCamera


log = logging.getLogger('camera_process')
log.setLevel(logging.DEBUG)
camHandler = logging.FileHandler('camera.log')
formatter = logging.Formatter('%(levelname)s: %(asctime)s %(filename)s %(funcName)s(%(lineno)d) -- %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
camHandler.setFormatter(formatter)
log.addHandler(camHandler)


class CameraProcessInfo:
    def __init__(self, cid):
        self.camera_id = cid


def camera_process(info: CameraProcessInfo, in_pipe: Pipe, out_pipe: Pipe, data_pipe: Pipe, kill_event: Event):
    ZwoCamera.initialize_library()
    camera = None

    while not kill_event.is_set():
        command = in_pipe.recv()
        if command is None:
            break

        if command == "list":
            out_pipe.send(ZwoCamera.get_cameras_list())
        elif command == "init":
            camera = ZwoCamera(camera_index=info.camera_id)
            if camera is not None:
                out_pipe.send("OK")
            else:
                out_pipe.send("Failure")
        elif command == "imageready":
            out_pipe.send(camera.get_imageready())
        elif command == "capture":
            # data_pipe.send(camera.capture())
            pass
        elif command == "startexposure":
            # out_pipe.send(camera.startexposure(duration=None))
            pass
        elif command == "imagebytes":
            out_pipe.send("OK")
            data_pipe.send(camera.get_imagebytes())
        else:
            log.warning(f"Got strange command: {command}")
    log.info("Camera process ended!")
