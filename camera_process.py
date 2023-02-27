import time

from .zwo_camera import ZwoCamera
from .app_utils import add_log
from .camera_server_utils import Error, OK


class CameraProcessHandle:
    def __init__(self, info, process, name, command_pipe, result_pipe, data_pipe):
        self.info = info
        self.process = process
        self.name = name
        self.command_pipe = command_pipe
        self.result_pipe = result_pipe
        self.data_pipe = data_pipe
        self.state = "IDLE"  # TODO maybe enum?


class CameraProcessInfo:
    def __init__(self, cid, command, result, data, ke):
        self.camera_id = cid
        self.in_pipe = command
        self.out_pipe = result
        self.data_pipe = data
        self.kill_event = ke


DONE_TOKEN = "<DONE>"
BUSY_TOKEN = "<BUSY>"


def camera_process(info: CameraProcessInfo):
    log = add_log(f"camera_{info.camera_id}")

    ZwoCamera.initialize_library()
    camera = None
    log.info(f"Starting process for camera no {info.camera_id}")

    while not info.kill_event.is_set():
        command = info.in_pipe.recv()
        if command is None:
            break

        if command == "list":
            info.out_pipe.send(OK(ZwoCamera.get_cameras_list()))
        elif command == "set_exposure":
            if camera is None:
                info.out_pipe.send(Error("Camera not initialized!"))
                continue
            camera.set_exposure()  # value should be get from pipe, but PUT is not yet implemented!

        elif command == "testexp":
            if camera is None:
                info.out_pipe.send(Error("Camera not initialized!"))
                continue

            info.out_pipe.send(OK(BUSY_TOKEN))
            camera.set_exposure(1)
            ss = time.time()
            for i in range(0, 10):
                print(f"Capturing file {i}")
                camera.capture(f"file{i}.tif")  # TODO

            print(f"Capturing done! It took {time.time()-ss} s")
            info.out_pipe.send(OK(DONE_TOKEN))

        elif command == "init":
            if camera is not None:
                info.out_pipe.send(OK("Already initialized"))
                return
            camera = ZwoCamera(camera_index=info.camera_id)
            if camera is not None:
                info.out_pipe.send(OK("Done init"))
            else:
                info.out_pipe.send(Error("Failed to initialize"))
        elif command == "imageready":
            info.out_pipe.send(OK(str(camera.get_imageready())))
        elif command == "capture":
            # data_pipe.send(camera.capture())
            pass
        elif command == "startexposure":
            # info.out_pipe.send(camera.startexposure(duration=None))
            pass
        elif command == "imagebytes":
            info.out_pipe.send("OK")
            info.data_pipe.send(camera.get_imagebytes())
        else:
            log.warning(f"Got strange command: {command}")
    log.info("Camera process ended!")
