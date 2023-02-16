from .ascom_camera import AscomCamera, CameraState
import zwoasi as asi
import logging
import numpy as np


log = logging.getLogger('main')


asi_lib_path = "C:\\ASI SDK\\lib\\x64\\ASICamera2.dll"
asi_initialized = False

ONE_SECOND_IN_MILLISECONDS = 1000
ONE_MILLISECOND_IN_MICROSECONDS = 1000
ONE_SECOND_IN_MICROSECODS = ONE_SECOND_IN_MILLISECONDS*ONE_MILLISECOND_IN_MICROSECONDS


class ZwoCamera(AscomCamera):
    def __init__(self, camera_index):
        self._state = CameraState.IDLE
        self._camera = asi.Camera(camera_index)
        self._index = camera_index
        self._camera.set_control_value(asi.ASI_GAIN, 0)
        self._camera.set_control_value(asi.ASI_EXPOSURE, ONE_SECOND_IN_MICROSECODS)
        self._connected = True

        log.info(f"ROI FORMAT = {self._camera.get_roi_format()}")

    def get_property(self):
        return self._camera.get_camera_property()

    def get_controls(self):
        return self._camera.get_controls()

    @staticmethod
    def get_cameras_list():
        if not asi_initialized:
            raise RuntimeError("ASI library not initialized")
        if asi.get_num_cameras() == 0:
            return []
        return asi.list_cameras()

    @staticmethod
    def initialize_library():
        global asi_initialized
        if not asi_initialized:
            asi.init(asi_lib_path)
            asi_initialized = True

    # General ASCOM device methods:
    def get_connected(self):
        return self._connected

    def set_connected(self, value):
        if self._connected and not value:
            del self._camera
            self._connected = False
        elif not self._connected and value:
            self._camera = asi.Camera(self._index)
            self._connected = True

    def get_name(self):
        return self._camera.get_camera_property()["Name"]

    def get_description(self):
        return self._camera.get_camera_property()["Description"]

    def get_interfaceversion(self):
        print("ZWO CAMERA method")
        return "1"

    # Camera specific methods - as required by Sharpcap (for now) # TODO!

    def get_sensorname(self):
        return self._camera.get_camera_property()["Name"]

    def get_pixelsizex(self):
        return self._camera.get_camera_property()["PixelSize"]

    def get_pixelsizey(self):
        return self._camera.get_camera_property()["PixelSize"]

    def get_cameraxsize(self):
        return self._camera.get_camera_property()["MaxWidth"]

    def get_cameraysize(self):
        return self._camera.get_camera_property()["MaxHeight"]

    def get_canasymmetricbin(self):
        return False

    def get_binx(self):
        return self._camera.get_bin()

    def get_biny(self):
        return self._camera.get_bin()

    def get_ccdtemperature(self):
        return float(self._camera.get_control_value(asi.ASI_TEMPERATURE)[0]) / 10.0

    def set_gain(self, value):
        self._camera.set_control_value(asi.ASI_GAIN, value)

    def get_bayeroffsetx(self):
        return 0  # TODO!

    def get_bayeroffsety(self):
        return 0  # TODO!

    def get_camerastate(self):
        exp_status = self._camera.get_exposure_status()
        if exp_status == 3:
            return CameraState.ERROR
        if exp_status == 0:
            return CameraState.IDLE
        if exp_status == 1:
            return CameraState.EXPOSING

        return CameraState.WAITING  # TODO: for sure?
        # IDLE = 0
        # WAITING = 1
        # EXPOSING = 2
        # READING = 3
        # DOWNLOAD = 4
        # ERROR = 5
        #
        # ASI_EXP_IDLE = 0
        # ASI_EXP_WORKING = 1
        # ASI_EXP_SUCCESS = 2
        # ASI_EXP_FAILED = 3

    def get_canabortexposure(self):
        return False  # TODO - maybe?

    def get_canfastreadout(self):
        return "HighSpeedMode" in self._camera.get_controls()

    def get_cangetcoolerpower(self):
        return False

    def get_canpulseguide(self):
        pass  # TODO!

    def get_cansetccdtemperature(self):
        return self._camera.get_camera_property()["IsCoolerCam"]

    def get_canstopexposure(self):
        return False  # TODO! Maybe it can be done

    def get_cooleron(self):
        return False

    def get_coolerpower(self):
        pass  # TODO!

    def get_electronsperadu(self):
        pass  # TODO!

    def get_exposuremax(self):
        return self._camera.get_controls()["Exposure"]["MaxValue"]

    def get_exposuremin(self):
        return self._camera.get_controls()["Exposure"]["MinValue"]

    def get_exposureresolution(self):
        pass  # TODO!

    def get_fastreadout(self):
        return self._camera.get_controls().get("HighSpeedMode", 0)

    def get_fullwellcapacity(self):
        pass  # TODO!

    def get_gain(self):
        return self._camera.get_control_value(asi.ASI_GAIN)

    def get_gainmax(self):
        return self._camera.get_controls()["Gain"]["MaxValue"]

    def get_gainmin(self):
        return self._camera.get_controls()["Gain"]["MinValue"]

    def get_gains(self):
        pass  # TODO!

    def get_hasshutter(self):
        pass  # TODO!

    def get_heatsinktemperature(self):
        pass  # TODO!

    def get_imagearray(self):
        filename = None  # TODO this can be somehow customized
        data = self._camera.get_data_after_exposure(None)
        whbi = self._camera.get_roi_format()

        shape = [whbi[1], whbi[0]]
        if whbi[3] == asi.ASI_IMG_RAW8 or whbi[3] == asi.ASI_IMG_Y8:
            img = np.frombuffer(data, dtype=np.uint8)
        elif whbi[3] == asi.ASI_IMG_RAW16:
            img = np.frombuffer(data, dtype=np.uint16)
        elif whbi[3] == asi.ASI_IMG_RGB24:
            img = np.frombuffer(data, dtype=np.uint8)
            shape.append(3)
        else:
            raise ValueError('Unsupported image type')
        img = img.reshape(shape)

        # if filename is not None:
        #     from PIL import Image
        #     mode = None
        #     if len(img.shape) == 3:
        #         img = img[:, :, ::-1]  # Convert BGR to RGB
        #     if whbi[3] == ASI_IMG_RAW16:
        #         mode = 'I;16'
        #     image = Image.fromarray(img, mode=mode)
        #     image.save(filename)
        #     logger.debug('wrote %s', filename)
        return img

    def get_imagearrayvariant(self):
        pass  # TODO!

    def get_imageready(self):
        return self._camera.get_exposure_status() == 2

    def get_ispulseguiding(self):
        pass  # TODO!

    def get_lastexposureduration(self):
        pass  # TODO!

    def get_lastexposurestarttime(self):
        pass  # TODO!

    def get_maxadu(self):
        return 2**(self._camera.get_camera_property()["BitDepth"])

    def get_maxbinx(self):
        return max(self._camera.get_camera_property()["SupportedBins"])

    def get_maxbiny(self):
        return max(self._camera.get_camera_property()["SupportedBins"])

    def get_numx(self):
        return self._camera.get_roi_format()[0]

    def get_numy(self):
        return self._camera.get_roi_format()[1]

    def get_offset(self):
        pass  # TODO!

    def get_offsetmax(self):
        pass  # TODO!

    def get_offsetmin(self):
        pass  # TODO!

    def get_offsets(self):
        pass  # TODO!

    def get_percentcompleted(self):
        pass  # TODO!

    def get_readoutmode(self):
        pass  # TODO!

    def get_readoutmodes(self):
        pass  # TODO!

    def get_sensortype(self):
        if not self._camera.get_camera_property()["IsColorCam"]:
            return 0
        return self._camera.get_camera_property()["BayerPattern"]

    def get_setccdtemperature(self):
        pass  # TODO!

    def get_startx(self):
        return self._camera.get_roi()[0]

    def get_starty(self):
        return self._camera.get_roi()[1]

    def set_numx(self, value):
        sx, sy, _, h = self._camera.get_roi()
        self._camera.set_roi(sx, sy, value, h)

    def set_numy(self, value):
        sx, sy, w, _ = self._camera.get_roi()
        self._camera.set_roi(sx, sy, w, value)

    def set_startx(self, value):
        _, sy, w, h = self._camera.get_roi()
        self._camera.set_roi(value, sy, w, h)

    def set_starty(self, value):
        sx, _, w, h = self._camera.get_roi()
        self._camera.set_roi(sx, value, w, h)

    def abortexposure(self):
        pass  # TODO!

    def stoptexposure(self):
        self._camera.stop_exposure()

    def startexposure(self, duration: float, light=True):
        self._camera.start_exposure(is_dark=not light)
