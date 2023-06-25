import time

from .zwo_camera import ZwoCamera
from .app_utils import add_log
from .camera_server_utils import Error, OK, CameraCommand
import os
from .app_utils import DefaultCaptureFilenameGenerator


log = None

capture_path = os.path.join(os.getcwd(), "capture")


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

regular_get_methods = [
    "connected",
    "name",
    "sensorname",
    "driverinfo",
    "driverversion",
    "supportedactions",
    "canpulseguide",
    "canfastreadout",
    "canasymmetricbin",
    "cansetccdtemperature",
    "cangetcoolerpower",
    "canstopexposure",
    "canabortexposure",
    "readoutmode",
    "readoutmodes",
    "pixelsizex",
    "pixelsizey",
    "interfaceversion",
    "binx",
    "biny",
    "cameraxsize",
    "cameraysize",
    "description",
    "ccdtemperature",
    "maxbinx",
    "maxbiny",
    "sensortype",
    "maxadu",
    "exposuremin",
    "exposuremax",
    "exposureresolution",
    "startx",
    "starty",
    "numx",
    "numy",
    "camerastate",
    "cooleron",
    "bayeroffsetx",
    "bayeroffsety",
    "imagearray",
    "imagearraybase64",
    "gain",
    "gainmin",
    "gainmax",
    "heatsinktemperature"
]

regular_put_methods = [
    "gain",
    "connected",
    "numx",
    "numy",
    "readoutmode",
    "binx",
    "biny",
    "startx",
    "starty"
]

class CameraProcessor:
    def __init__(self, info: CameraProcessInfo):
        self._filename_generator = DefaultCaptureFilenameGenerator(prefix="")
        self._capturing = False
        self._camera_id = info.camera_id
        self._response_queue = info.out_queue
        self._command_queue = info.in_queue
        self._kill_event = info.kill_event
        self._data_pipe = info.data_pipe
        self._continuous = False
        ZwoCamera.initialize_library()
        self._camera: ZwoCamera = None
        log.info(f"Starting process for camera no {info.camera_id}")

        self._unusual_put_method_map = {
            "init": self._handle_set_init,
            "startexposure": self._handle_set_startexposure,
            "capture": self._handle_set_capture,
            "instantcapture": self._handle_instant_capture,
            "startcontinuous": self._handle_start_continuous,
            "stopcontinuous": self._handle_stop_continuous
        }

        self._unusual_get_method_map = {
            "list": self._handle_get_list,
            "imageready": self._handle_get_imageready,
            "imagebytes": self._handle_get_imagebytes,
            "currentimage": self._get_current_image
        }

    def run(self):
        while not self._kill_event.is_set():
            possible_when_continuous = [
                "init",
                "stopcontinuous",
                "currentimage"
            ]

            command_raw: CameraCommand = self._command_queue.get()
            if command_raw is None:
                break  # this is ultimate stopping condition

            if self._continuous and command_raw.get_name() not in possible_when_continuous:
                self._response_queue.put(Error(f"Not allowed when in continuous mode!"))
                continue

            if command_raw.is_get():
                self._handle_get(command_raw)

            elif command_raw.is_put():
                self._handle_put(command_raw)

    def _handle_get(self, command_raw):
        command_name = command_raw.get_name()
        if command_name in regular_get_methods:
            self._handle_regular_get(command_name)
        elif command_name in self._unusual_get_method_map.keys():
            self._handle_unusual_get(command_raw)
        else:
            self._response_queue.put(Error(f"Unknown get command: {command_name}"))

    def _handle_regular_get(self, command_name):
        if self._camera is None:
            self._response_queue.put(Error("Regular get: Camera not initialized!"))
            return
        method_name = "get_" + command_name
        log.debug(f"Calling method: {method_name}")
        result = getattr(self._camera, method_name)()
        log.debug(f"Got result: {result}")
        self._response_queue.put(OK(result))

    def _handle_unusual_get(self, command_raw):
        handle_for_get = self._unusual_get_method_map[command_raw.get_name()]
        handle_for_get()

    def _handle_get_list(self):
        self._response_queue.put(OK(ZwoCamera.get_cameras_list()))

    def _handle_get_imageready(self):
        if self._camera is None:
            self._response_queue.put(Error("Camera not initialized!"))
        elif self._capturing:
            self._response_queue.put(OK(False))
        else:
            self._response_queue.put(OK(self._camera.get_imageready()))

    def _handle_get_imagebytes(self):
        imagebytes, length = self._camera.get_imagebytes()
        self._response_queue.put(OK(DONE_TOKEN))
        self._data_pipe.send((imagebytes, length))

    def _handle_put(self, command_raw):
        command_name = command_raw.get_name()
        params = command_raw.get_params()
        if command_name in regular_put_methods:
            self._handle_regular_put(command_name, params)
        elif command_name in self._unusual_put_method_map.keys():
            self._handle_unusual_put(command_name, params)
        else:
            self._response_queue.put(Error(f"Unknown put command: {command_name}"))

    def _handle_regular_put(self, command_name, params):
        if self._camera is None:
            self._response_queue.put(Error("Regular put: Camera not initialized!"))
            return
        if params is None:
            self._response_queue.put(Error("No params passed for put method"))
            return

        params_no = len(params)
        if params_no > 1:
            self._response_queue.put(Error(f"Expecting only one argument, got {params_no}"))
            return
        try:
            value = list(params.values())[0]
            method_name = "set_"+command_name
            log.debug(f"Calling method {method_name}")
            getattr(self._camera, method_name)(value)
            self._response_queue.put(OK("OK"))
        except KeyError as ke:
            self._response_queue.put(Error("Missing params: " + repr(ke)))
        except TypeError as te:
            self._response_queue.put(Error("Could not extract params: " + repr(te)))
        except Exception as e:
            self._response_queue.put(Error("Unknown exception: " + repr(e)))

    def _handle_unusual_put(self, command_name, params):
        mapped_handle = self._unusual_put_method_map[command_name]
        mapped_handle(params)

    def _handle_start_continuous(self, params):
        log.debug("Starting continuous imaging!")
        self._continuous = True
        self._response_queue.put(OK(DONE_TOKEN))
        self._camera.startexposure(duration=1.0, light=True)

    def _handle_stop_continuous(self, params):
        log.debug("Starting continuous imaging!")
        self._continuous = False
        self._response_queue.put(OK(DONE_TOKEN))

    def _get_current_image(self):
        if not self._camera.get_imageready():
            self._response_queue.put(OK(BUSY_TOKEN))
            return

        imagebytes, length = self._camera.get_imagebytes()
        self._response_queue.put(OK(DONE_TOKEN))
        self._camera.startexposure(duration=1.0, light=True)
        self._data_pipe.send((imagebytes, length))

    def _handle_instant_capture(self, params):
        log.debug("Starting instant capture!")
        max_instant_capture_duration_s = 5
        instant_capture_wait_increment_s = 0.1
        instant_capture_max_counter = 10 + int(max_instant_capture_duration_s/instant_capture_wait_increment_s)
        duration = float(params["Duration"])
        light = bool(params["Light"])
        if duration > max_instant_capture_duration_s:
            self._response_queue.put(
                Error(f"Duration too long: allowed = {max_instant_capture_duration_s} "
                      f"while requested {duration}"))
            return
        self._camera.startexposure(duration=duration, light=light)
        for i in range(0, instant_capture_max_counter):
            if self._camera.get_imageready():
                imagebytes, length = self._camera.get_imagebytes()
                self._response_queue.put(OK(DONE_TOKEN))
                self._data_pipe.send((imagebytes, length))
                return
            time.sleep(instant_capture_wait_increment_s)
        self._response_queue.put(
            Error(f"Timeout: Could not get instant image on time!"))
        return

    def _handle_set_init(self, params):
        if self._camera is not None:
            self._response_queue.put(OK("Done init"))
            self._continuous = False
        else:
            self._camera = ZwoCamera(camera_index=self._camera_id)
            self._response_queue.put(Error("Failed to initialize"))

    def _handle_set_startexposure(self, params):
        duration = float(params["Duration"])
        light = bool(params["Light"])
        self._camera.startexposure(duration=duration, light=light)
        self._response_queue.put(OK(DONE_TOKEN))

    def _handle_set_capture(self, params):
        print(f"Handling capture with params: {params}!")
        try:
            duration_s = float(params["Duration"])
            number = int(params["Number"])
        except KeyError as ke:
            self._response_queue.put(Error("Missing params: " + repr(ke)))
            return
        except TypeError as te:
            self._response_queue.put(Error("Could not extract params: " + repr(te)))
            return
        except Exception as e:
            self._response_queue.put(Error("Unknown exception: " + repr(e)))
            return

        if self._camera is None:
            self._response_queue.put(Error("Camera not initialized!"))
            return
        self._capturing = True
        self._response_queue.put(OK(BUSY_TOKEN))

        self._camera.set_exposure(duration_s)
        ss = time.time()
        try:
            for i in range(0, number):
                print(f"Capturing file {i}")
                fn = self._filename_generator.generate()
                self._camera.capture(fn)
                self._response_queue.put(OK(f"{i+1}/{number}"))
        except PermissionError as pe:
            self._response_queue.put(Error("Permissions problems! Try running with sudo"))
            self._capturing = False
            return

        print(f"Capturing done! It took {time.time() - ss} s")
        self._response_queue.put(OK(DONE_TOKEN))
        self._capturing = False


def camera_process(info: CameraProcessInfo):
    global log
    log = add_log(f"camera_{info.camera_id}")
    cp = CameraProcessor(info)
    cp.run()
    log.info("Camera process ended!")
