import time

from .zwo_camera import ZwoCamera
from .app_utils import add_log
from .camera_server_utils import Error, OK, CameraCommand


class CameraProcessHandle:
    def __init__(self, info, process, name, command_queue, result_queue, data_pipe):
        self.info = info
        self.process = process
        self.name = name
        self.command_queue = command_queue
        self.result_queue = result_queue
        self.data_pipe = data_pipe
        self.state = "IDLE"  # TODO maybe enum?


class CameraProcessInfo:
    def __init__(self, cid, command, result, data, ke):
        self.camera_id = cid
        self.in_queue = command
        self.out_queue = result
        self.data_pipe = data
        self.kill_event = ke


DONE_TOKEN = "<DONE>"
BUSY_TOKEN = "<BUSY>"


def handle_capture(params, camera: ZwoCamera, info):
    print(f"Handling capture with params: {params}!")
    try:
        duration_s = float(params["Duration"])
        number = int(params["Number"])
    except KeyError as ke:
        info.out_queue.put(Error("Missing params: " + repr(ke)))
        return
    except TypeError as te:
        info.out_queue.put(Error("Could not extract params: " + repr(te)))
        return
    except Exception as e:
        info.out_queue.put(Error("Unknown exception: " + repr(e)))
        return

    if camera is None:
        info.out_queue.put(Error("Camera not initialized!"))
        return
    info.out_queue.put(OK(BUSY_TOKEN))

    camera.set_exposure(duration_s)
    ss = time.time()
    for i in range(0, number):
        print(f"Capturing file {i}")
        camera.capture(f"file{i}.tif")  # TODO
        info.out_queue.put(OK(f"{i}/{number}"))

    print(f"Capturing done! It took {time.time() - ss} s")
    info.out_queue.put(OK(DONE_TOKEN))


def camera_process(info: CameraProcessInfo):
    log = add_log(f"camera_{info.camera_id}")

    ZwoCamera.initialize_library()
    camera = None
    log.info(f"Starting process for camera no {info.camera_id}")

    while not info.kill_event.is_set():
        command_raw: CameraCommand = info.in_queue.get()
        if command_raw is None:
            break

        command = command_raw.get_name()
        if command == "capture":
            handle_capture(command_raw.get_params(), camera, info)
        elif command == "list":
            info.out_queue.put(OK(ZwoCamera.get_cameras_list()))
        elif command == "set_exposure":
            if camera is None:
                info.out_queue.put(Error("Camera not initialized!"))
                continue
            camera.set_exposure()  # value should be get from pipe, but PUT is not yet implemented!

        elif command == "testexp":
            if camera is None:
                info.out_queue.put(Error("Camera not initialized!"))
                continue

            info.out_queue.put(OK(BUSY_TOKEN))
            camera.set_exposure(1)
            ss = time.time()
            for i in range(0, 10):
                print(f"Capturing file {i}")
                camera.capture(f"file{i}.tif")  # TODO

            print(f"Capturing done! It took {time.time()-ss} s")
            info.out_queue.put(OK(DONE_TOKEN))

        elif command == "init":
            if camera is not None:
                info.out_queue.put(OK("Already initialized"))
                return
            camera = ZwoCamera(camera_index=info.camera_id)
            if camera is not None:
                info.out_queue.put(OK("Done init"))
            else:
                info.out_queue.put(Error("Failed to initialize"))
        elif command == "imageready":
            if camera is None:
                info.out_queue.put(Error("Camera not initialized!"))
            else:
                info.out_queue.put(OK(str(camera.get_imageready())))
        elif command == "capture":
            # data_pipe.send(camera.capture())
            pass
        elif command == "startexposure":
            # info.out_queue.put(camera.startexposure(duration=None))
            pass
        elif command == "imagebytes":
            info.out_queue.put("OK")
            info.data_pipe.send(camera.get_imagebytes())
        else:
            log.warning(f"Got strange command: {command}")
    log.info("Camera process ended!")
