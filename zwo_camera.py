from .ascom_camera import AscomCamera
import zwoasi as asi
import logging


log = logging.getLogger('main')


asi_lib_path = "C:\\ASI SDK\\lib\\x64\\ASICamera2.dll"
asi_initialized = False

ONE_SECOND_IN_MILLISECONDS = 1000
ONE_MILLISECOND_IN_MICROSECONDS = 1000
ONE_SECOND_IN_MICROSECODS = ONE_SECOND_IN_MILLISECONDS*ONE_MILLISECOND_IN_MICROSECONDS


class ZwoCamera(AscomCamera):
    def __init__(self, camera_index):
        self._camera = asi.Camera(camera_index)
        self._index = camera_index
        self._camera.set_control_value(asi.ASI_GAIN, 0)
        self._camera.set_control_value(asi.ASI_EXPOSURE, ONE_SECOND_IN_MICROSECODS)

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
        return True  # TODO maybe something more sophisticated?

    def set_connected(self, value):
        pass  # TODO maybe something more sophisticated?

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
        pass  # TODO!

    def get_bayeroffsety(self):
        pass  # TODO!

    def get_camerastate(self):
        pass  # TODO!

    def get_canabortexposure(self):
        pass  # TODO!

    def get_canfastreadout(self):
        pass  # TODO!

    def get_cangetcoolerpower(self):
        return False

    def get_canpulseguide(self):
        pass  # TODO!

    def get_cansetccdtemperature(self):
        return self._camera.get_camera_property()["IsCoolerCam"]

    def get_canstopexposure(self):
        pass  # TODO!

    def get_cooleron(self):
        pass  # TODO!

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
        pass  # TODO!

    def get_fullwellcapacity(self):
        pass  # TODO!

    def get_gain(self):
        pass  # TODO!

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
        pass  # TODO!

    def get_imagearrayvariant(self):
        pass  # TODO!

    def get_imageready(self):
        pass  # TODO!

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
        pass  # TODO!

    def get_setccdtemperature(self):
        pass  # TODO!

    def get_startx(self):
        return self._camera.get_roi()[0]

    def get_starty(self):
        return self._camera.get_roi()[1]

    def set_numx(self, value):
        _, h, bins, imf = self._camera.get_roi_format()
        self._camera.set_roi_format(value, h, bins, imf)

    def set_numy(self, value):
        w, _, bins, imf = self._camera.get_roi_format()
        self._camera.set_roi_format(w, value, bins, imf)

    def set_startx(self, value):
        _, sy, w, h = self._camera.get_roi()
        self._camera.set_roi(value, sy, w, h)

    def set_starty(self, value):
        sx, _, w, h = self._camera.get_roi()
        self._camera.set_roi(sx, value, w, h)
