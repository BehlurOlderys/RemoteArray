from guiding_app.ascom.ascom_camera import AscomCamera, CameraState
import zwoasi as asi
import numpy as np
import base64
import os
from PIL import Image
from guiding_app.app_utils import add_log
from enum import IntEnum
from threading import Event, Timer
import io
from guiding_app.interval_utils import start_interval_polling


if os.name == "nt": 
    asi_lib_path = "C:\\ASI SDK\\lib\\x64\\ASICamera2.dll"
else:
    asi_lib_path = "/usr/local/lib/libASICamera2.so"
asi_initialized = False

ONE_SECOND_IN_MILLISECONDS = 1000
ONE_MILLISECOND_IN_MICROSECONDS = 1000
ONE_SECOND_IN_MICROSECONDS = ONE_SECOND_IN_MILLISECONDS * ONE_MILLISECOND_IN_MICROSECONDS


exp_states = {
    asi.ASI_EXP_IDLE: "Idle",
    asi.ASI_EXP_FAILED: "Failed",
    asi.ASI_EXP_SUCCESS: "Success",
    asi.ASI_EXP_WORKING: "Working"
}


class CameraCaptureStatus(IntEnum):
    IDLE = 1
    ONLY_CAPTURE = 2
    CAPTURE_AND_SAVE = 3
    ERROR = 9


def one_second_capture(parent, stop_event: Event):
    camera_state: CameraCaptureStatus = parent.get_status_enum()
    print(f"Camera capture status = {camera_state}")
    if camera_state == CameraCaptureStatus.ONLY_CAPTURE:
        exp_status = parent.get_exposure_status()
        if exp_status == asi.ASI_EXP_IDLE:
            print("Starting new exposure (from IDLE)")
            parent.startexposure()
        elif exp_status == asi.ASI_EXP_SUCCESS:
            print("Starting new exposure (from SUCCESS)")
            parent.get_imagebytes()
            parent.startexposure()
        else:
            print(f"Strange: status = {exp_status}")

    parent._state_counters[parent._state] += 1
    if not stop_event.is_set():
        Timer(1, one_second_capture, [parent, stop_event]).start()


image_types_by_name = {
    "RAW8": asi.ASI_IMG_RAW8,
    "RGB24": asi.ASI_IMG_RGB24,
    "RAW16": asi.ASI_IMG_RAW16,
    "Y8": asi.ASI_IMG_Y8
}

image_types_by_value = {v: k for k, v in image_types_by_name.items()}


logs = {}


class ZwoCamera(AscomCamera):
    def __init__(self, camera_index):
        if camera_index not in logs.keys():
            logs[camera_index] = add_log(f"camera_{camera_index}")

        self._log = logs[camera_index]
        self._state = CameraCaptureStatus.IDLE

        self._state_counters = {
            CameraCaptureStatus.IDLE: 0,
            CameraCaptureStatus.ONLY_CAPTURE: 0,
            CameraCaptureStatus.CAPTURE_AND_SAVE: 0,
            CameraCaptureStatus.ERROR: 0
        }

        self._loop_event = Event()
        self._camera = asi.Camera(camera_index)
        self._index = camera_index
        self._camera.set_control_value(asi.ASI_HIGH_SPEED_MODE, 0)
        self._camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, 40)
        self._camera.set_control_value(asi.ASI_GAIN, 100)
        self._camera.set_control_value(asi.ASI_EXPOSURE, 1 * ONE_SECOND_IN_MICROSECONDS)
        supported = self._camera.get_camera_property()['SupportedVideoFormat']
        self._camera.set_image_type(supported[0])
        self._connected = True
        self._new_filename = None
        self._last_duration = 1
        print(f"ROI FORMAT = {self._camera.get_roi_format()}")
        self._log.info(f"ROI FORMAT = {self._camera.get_roi_format()}")
        self._capture_directory = "Capture"
        self._max_captures = 1
        self._current_capture_number = 0
        self._image_prefix = "image"

        self._capturing = False
        self._buffer = None
        self._buffer_size = 0
        self._reserve_buffer()

    def __del__(self):
        self._loop_event.set()

    def _capturing_loop(self):
        camera_state: CameraCaptureStatus = self._state
        print(f"Camera capture status = {camera_state}")
        if camera_state == CameraCaptureStatus.ONLY_CAPTURE or camera_state == CameraCaptureStatus.CAPTURE_AND_SAVE:
            exp_status = self.get_exposure_status()
            print(f"Camera exp status = {exp_status}")
            if exp_status == asi.ASI_EXP_IDLE:
                print("Starting new exposure (from IDLE)")
                self.startexposure()
            elif exp_status == asi.ASI_EXP_SUCCESS:
                print("Starting new exposure (from SUCCESS)")
                self.get_imagebytes()
                if camera_state == CameraCaptureStatus.CAPTURE_AND_SAVE:
                    filename = os.path.join(
                        self._capture_directory,
                        f"{self._image_prefix}_{self._current_capture_number:05d}.tif"
                    )
                    self._current_capture_number += 1
                    print(f"Saving to {filename}")
                    self._save_imagebytes_to_file(filename)
                    if self._current_capture_number >= self._max_captures:
                        print(f"Saving {self._max_captures} images completed!")
                        self._stop_saving_impl()
                        return
                    print(f"Starting exposure number {self._current_capture_number}")
                self.startexposure()
            elif exp_status == asi.ASI_EXP_WORKING:
                print("Camera is working, wait another 1s...")
            else:
                print(f"Strange: status = {exp_status}")

        self._state_counters[self._state] += 1

    def start_capturing(self):
        self._loop_event.clear()
        self._state = CameraCaptureStatus.ONLY_CAPTURE
        start_interval_polling(self._loop_event, self._capturing_loop, 1, None)
        pass

    def stop_capturing(self):
        self._stop_saving_impl()
        self._loop_event.set()
        self._state = CameraCaptureStatus.IDLE
        pass

    def start_saving(self, dir_name, number, prefix):
        self._capture_directory = dir_name
        self._max_captures = number
        self._image_prefix = prefix
        self._current_capture_number = 0
        self._state = CameraCaptureStatus.CAPTURE_AND_SAVE
        pass

    def stop_saving(self):
        print("Stopping saving!")
        self._stop_saving_impl()

    def _stop_saving_impl(self):
        self._state = CameraCaptureStatus.ONLY_CAPTURE
        self._max_captures = 1
        self._current_capture_number = 0

    def _save_imagebytes_to_file(self, filename):
        # from PIL import Image
        # mode = None
        # if len(img.shape) == 3:
        #     img = img[:, :, ::-1]  # Convert BGR to RGB
        # if whbi[3] == ASI_IMG_RAW16:
        #     mode = 'I;16'
        # image = Image.fromarray(img, mode=mode)
        # image.save(filename)
        # logger.debug('wrote %s', filename)
        pass

    def set_defaults(self):
        self._camera.set_control_value(asi.ASI_HIGH_SPEED_MODE, 0)
        self._camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, self._camera.get_controls()['BandWidth']['MinValue'])
        self._camera.disable_dark_subtract()
        self._camera.set_control_value(asi.ASI_GAIN, 150)
        self._camera.set_control_value(asi.ASI_EXPOSURE, ONE_SECOND_IN_MICROSECONDS)
        self._camera.set_control_value(asi.ASI_WB_B, 99)
        self._camera.set_control_value(asi.ASI_WB_R, 75)
        self._camera.set_control_value(asi.ASI_GAMMA, 50)
        self._camera.set_control_value(asi.ASI_BRIGHTNESS, 50)
        self._camera.set_control_value(asi.ASI_FLIP, 0)
        try: 
            self._camera.stop_video_capture()
            self._camera.stop_exposure()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass
        self._camera.set_image_type(asi.ASI_IMG_RAW16)

    def get_last_image(self):
        return True, *self._get_buffer()

    def get_buffer_as_jpg(self):
        data, bsize = self._get_buffer()
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

        mode = None
        if len(img.shape) == 3:
            img = img[:, :, ::-1]  # Convert BGR to RGB
        if whbi[3] == asi.ASI_IMG_RAW16:
            mode = 'I;16'
        pil_image = Image.fromarray(img, mode=mode)
        img_bytes = io.BytesIO()
        pil_image.point(lambda i: i * (1. / 256)).convert('L').save(img_bytes, format='JPEG', quality=85)  # Save image to BytesIO
        img_bytes.seek(0)
        return img_bytes

    def get_setting(self, setting_name: str):
        allowed_settings = [
                "binx",
                "gain",
                "exposure",
                "cansetccdtemperature",
                "cansetcooleron",
                "cangetcoolerpower",
                "ccdtemperature",
                "controls",
                "properties",
                "setccdtemperature",
                "numx",
                "numy",
                "maxbinx",
                "cooleron",
                "coolerpower",
                "offset",
                "offsetmin",
                "offsetmax",
                "readoutmode_str",
                "readoutmodes",
                "fastreadout",
                "imageready",
                "iscapturing",
                "iscooled",
                "tempandstatus",
                "status"
        ]
        if setting_name in allowed_settings:
            return True, getattr(self, "get_"+setting_name)()
        return False, {"allowed_settings": allowed_settings}

    def set_setting(self, setting_name: str, value: str):
        allowed_settings = [
            "binx",
            "readoutmode_str",
            "exposure",
            "gain",
            "offset",
            "setccdtemperature",
            "cooleron",
            "capturing",
            "status"
        ]
        if setting_name in allowed_settings:
            return True, getattr(self, "set_"+setting_name)(value)
        return False, {"allowed_settings": allowed_settings}

    def get_cansetcooleron(self):
        return self._camera.get_controls()["CoolerOn"]["IsWritable"]

    def demo(self):
        camera_info = self._camera.get_camera_property()

        # Get all of the camera controls
        print('Camera controls:')
        controls = self._camera.get_controls()
        for cn in sorted(controls.keys()):
            print('    %s:' % cn)
            for k in sorted(controls[cn].keys()):
                print('        %s: %s' % (k, repr(controls[cn][k])))


        # Use minimum USB bandwidth permitted
        self._camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, self._camera.get_controls()['BandWidth']['MinValue'])

        # Set some sensible defaults. They will need adjusting depending upon
        # the sensitivity, lens and lighting conditions used.
        self._camera.disable_dark_subtract()

        self._camera.set_control_value(asi.ASI_GAIN, 150)
        self._camera.set_control_value(asi.ASI_EXPOSURE, 30000)
        self._camera.set_control_value(asi.ASI_WB_B, 99)
        self._camera.set_control_value(asi.ASI_WB_R, 75)
        self._camera.set_control_value(asi.ASI_GAMMA, 50)
        self._camera.set_control_value(asi.ASI_BRIGHTNESS, 50)
        self._camera.set_control_value(asi.ASI_FLIP, 0)


        print('Enabling stills mode')
        try:
            # Force any single exposure to be halted
            self._camera.stop_video_capture()
            self._camera.stop_exposure()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass

        print('Capturing a single 8-bit mono image')
        filename = 'image_mono.jpg'
        self._camera.set_image_type(asi.ASI_IMG_RAW8)
        try:
            self._camera.capture(filename=filename)
            return True
        except asi.ZWO_CaptureError as ce:
            print(f"error = {ce}, status = {ce.exposure_status}")
            return False

    def get_tempandstatus(self):
        return {
            "temperature": self.get_ccdtemperature(),
            "capture_status": self.get_status(),
            "exposure_status": self.get_exposure_status(),
            "counters": self._state_counters
        }

    def get_status_enum(self):
        return self._state

    def get_status(self):
        if self._state == CameraCaptureStatus.IDLE:
            return "IDLE"
        elif self._state == CameraCaptureStatus.ONLY_CAPTURE:
            return "CAPTURE"
        elif self._state == CameraCaptureStatus.CAPTURE_AND_SAVE:
            return "SAVE"
        return "ERROR_STATE"

    def set_status(self, value):
        print(f"Setting status to {value}")
        if value == "IDLE":
            self._state = CameraCaptureStatus.IDLE
        elif value == "CAPTURE":
            self._state = CameraCaptureStatus.ONLY_CAPTURE
        elif value == "SAVE":
            self._state = CameraCaptureStatus.CAPTURE_AND_SAVE
        return value

    def get_exposure(self):
        return self._camera.get_control_value(asi.ASI_EXPOSURE)[0]

    def set_exposure(self, duration_s):
        duration_s = float(duration_s)
        self._camera.set_control_value(asi.ASI_EXPOSURE, int(duration_s * ONE_SECOND_IN_MICROSECONDS))
        self._last_duration = duration_s

    def capture_to_buffer(self):
        try:
            self._camera.capture(buffer_=self._buffer)
            return True
        except asi.ZWO_CaptureError as ce:
            print(f"error = {ce}, status = {ce.exposure_status}")
            return False

    def capture(self, filename):
        try:
            self._camera.capture(filename=filename)
            return True
        except asi.ZWO_CaptureError as ce:
            print(f"error = {ce}, status = {ce.exposure_status}")
            return False

    def _reserve_buffer(self):
        whbi = self._camera.get_roi_format()
        sz = whbi[0] * whbi[1]
        if whbi[3] == asi.ASI_IMG_RGB24:
            sz *= 3
        elif whbi[3] == asi.ASI_IMG_RAW16:
            sz *= 2
        self._log.info(f"Reserving buffer of size {whbi[0]}x{whbi[1]}={sz}")

        print(f"Size of reserved buffer = {sz}")

        if self._buffer is None:
            self._buffer_size = sz
            self._buffer = bytearray(sz)
            return

        if sz != self._buffer_size:
            del self._buffer
            self._buffer_size = sz
            self._buffer = bytearray(sz)

    def _get_buffer(self):
        return self._buffer, self._buffer_size

    def _store_imagebytes(self):
        self._camera.get_data_after_exposure(self._buffer)

    def get_imagebytes(self):
        self._store_imagebytes()
        return self._get_buffer()

    def save_image_to_file(self, filename):
        self._store_imagebytes()
        whbi = self._camera.get_roi_format()
        shape = [whbi[1], whbi[0]]
        if whbi[3] == asi.ASI_IMG_RAW8 or whbi[3] == asi.ASI_IMG_Y8:
            img = np.frombuffer(self._buffer, dtype=np.uint8)
        elif whbi[3] == asi.ASI_IMG_RAW16:
            img = np.frombuffer(self._buffer, dtype=np.uint16)
        elif whbi[3] == asi.ASI_IMG_RGB24:
            img = np.frombuffer(self._buffer, dtype=np.uint8)
            shape.append(3)
        else:
            raise ValueError('Unsupported image type')
        img = img.reshape(shape)

        mode = None
        if len(img.shape) == 3:
            img = img[:, :, ::-1]  # Convert BGR to RGB
        if whbi[3] == asi.ASI_IMG_RAW16:
            mode = 'I;16'
        image = Image.fromarray(img, mode=mode)
        image.save(filename)
        self._log.debug('wrote %s', filename)

    def save_to_file_and_get_imagebytes(self, filename):
        self.save_image_to_file(filename)
        return self._get_buffer()

    def get_image_specs(self):
        """
        :return: tuple with elements:
        rank, dim0, dim1, dim2
        """
        whbi = self._camera.get_roi_format()
        im_type = whbi[3]
        if im_type in [asi.ASI_IMG_RAW8, asi.ASI_IMG_Y8, asi.ASI_IMG_RAW16]:
            rank = 2
        elif im_type == asi.ASI_IMG_RGB24:
            rank = 3
        else:
            return -1
        dim3 = 0 if rank == 2 else 3
        return rank, whbi[0], whbi[1], dim3

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
        value = bool(value)
        if self._connected and not value:
            del self._camera
            self._connected = False
        elif not self._connected and value:
            self._camera = asi.Camera(self._index)
            self._connected = True

    def get_name(self):
        return self._camera.get_camera_property()["Name"]

    def get_properties(self):
        return self._camera.get_camera_property()

    def get_description(self):
        if "Description" in self._camera.get_camera_property():
            return self._camera.get_camera_property()["Description"]
        return "<no description available>"

    def get_driverinfo(self):
        return "This is ALPACA driver by Bartlomiej Hnatio"

    def get_driverversion(self):
        return "v1.0"

    def get_interfaceversion(self):
        return 1

    def get_supportedactions(self):
        return []

    # Camera specific methods - as required by Sharpcap (for now) # TODO!

    def get_canpulseguide(self):
        return False  # TODO as for now

    def get_canfastreadout(self):
        return "HighSpeedMode" in self._camera.get_controls()

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

    def get_iscooled(self):
        return self._camera.get_camera_property()["IsCoolerCam"]

    def get_canasymmetricbin(self):
        return False

    def get_binx(self):
        return self._camera.get_bin()

    def get_biny(self):
        return self._camera.get_bin()

    def get_ccdtemperature(self):
        return float(self._camera.get_control_value(asi.ASI_TEMPERATURE)[0]) / 10.0

    def set_gain(self, value):
        gain = int(value)
        self._camera.set_control_value(asi.ASI_GAIN, gain)
        
    def set_offset(self, value):
        offset = int(value)
        self._camera.set_control_value(asi.ASI_OFFSET, offset)

    def get_bayeroffsetx(self):
        return 0  # TODO!

    def get_bayeroffsety(self):
        return 0  # TODO!

    def get_exposure_status(self):
        return self._camera.get_exposure_status()

    def get_capturestate(self):
        exp_status = self._camera.get_exposure_status()
        if exp_status == 2:
            return CameraState.IDLE
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

    def get_cangetcoolerpower(self):
        if "CoolPowerPerc" in self._camera.get_controls():
            return True
        return False

    def get_cansetccdtemperature(self):
        return self._camera.get_controls()["TargetTemp"]["IsWritable"]

    def get_canstopexposure(self):
        return False  # TODO! Maybe it can be done

    def get_coolerpower(self):
        return self._camera.get_control_value(asi.ASI_COOLER_POWER_PERC)[0]

    def get_electronsperadu(self):
        pass  # TODO!

    def get_exposuremax(self):
        return self._camera.get_controls()["Exposure"]["MaxValue"] / ONE_SECOND_IN_MICROSECONDS

    def get_exposuremin(self):
        return self._camera.get_controls()["Exposure"]["MinValue"] / ONE_SECOND_IN_MICROSECONDS

    def get_exposureresolution(self):
        return 1.0 / ONE_SECOND_IN_MICROSECONDS

    def get_fastreadout(self):
        return self._camera.get_controls().get("HighSpeedMode", 0)

    def get_fullwellcapacity(self):
        pass  # TODO!

    def get_gain(self):
        return self._camera.get_control_value(asi.ASI_GAIN)[0]

    def get_gainmax(self):
        return self._camera.get_controls()["Gain"]["MaxValue"]

    def get_gainmin(self):
        return self._camera.get_controls()["Gain"]["MinValue"]

    def get_gains(self):
        pass  # TODO!

    def get_hasshutter(self):
        pass  # TODO!

    def get_heatsinktemperature(self):
        return 0  # TODO!!!

    def get_camerastate(self):
        return self.get_capturestate()

    def get_imagearray(self):
        filename = self._new_filename  # TODO this can be somehow customized
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
        # img = np.transpose(img, (1, 0, 2))

        # if filename is not None:
        #     mode = None
        #     if len(img.shape) == 3:
        #         img = img[:, :, ::-1]  # Convert BGR to RGB
        #     if whbi[3] == asi.ASI_IMG_RAW16:
        #         mode = 'I;16'
        #     image = Image.fromarray(img, mode=mode)
        #     image.save(filename)
        #     log.debug('wrote %s', filename)
        return img, filename

    def get_imagearraybase64(self):
        img = self.get_imagearray()
        base64_bytes = base64.b64encode(img)
        return base64_bytes.decode('ascii')

    def get_imagearrayvariant(self):
        pass  # TODO!

    def get_imageready(self):
        return self._camera.get_exposure_status() == 2

    def get_iscapturing(self):
        return self._capturing

    def set_capturing(self, value):
        self._capturing = bool(value)

    def get_ispulseguiding(self):
        pass  # TODO!

    def get_lastexposureduration(self):
        return self._last_duration

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
        return self._camera.get_control_value(asi.ASI_OFFSET)[0]

    def get_offsetmax(self):
        return self._camera.get_controls()["Gain"]["MaxValue"]

    def get_offsetmin(self):
        return self._camera.get_controls()["Gain"]["MinValue"]

    def get_offsets(self):
        pass  # TODO!

    def get_percentcompleted(self):
        pass  # TODO!

    def get_readoutmode(self):
        camera_info = self._camera.get_camera_property()
        supported = camera_info['SupportedVideoFormat']
        sorted_supported = [s for s in sorted(supported)]
        mode = self._camera.get_image_type()
        return sorted_supported.index(mode)

    def get_readoutmode_str(self):
        mode = self._camera.get_image_type()
        return image_types_by_value.get(mode, "<FAIL>")

    def get_readoutmodes(self):
        camera_info = self._camera.get_camera_property()
        supported = camera_info['SupportedVideoFormat']
        print(f"Supported = {supported}")
        return [image_types_by_value[s] for s in sorted(supported)]

    def get_sensortype(self):
        # if not self._camera.get_camera_property()["IsColorCam"]:
        #     return 0
        # return self._camera.get_camera_property()["BayerPattern"]
        return 2  # TODO!!!! it should be variable, this is good only for ASI120MC

    def get_setccdtemperature(self):
        return self._camera.get_control_value(asi.ASI_TARGET_TEMP)[0]

    def set_setccdtemperature(self, value):
        degrees = int(value)
        self._camera.set_control_value(asi.ASI_TARGET_TEMP, degrees)

    def get_cooleron(self):
        return self._camera.get_control_value(asi.ASI_COOLER_ON)[0]

    def set_cooleron(self, value):
        print(f"Set cooler on: {value}")
        value_bool = (1 if value == "True" else 0)
        self._camera.set_control_value(asi.ASI_COOLER_ON, value_bool)

    def get_startx(self):
        return self._camera.get_roi()[0]

    def get_starty(self):
        return self._camera.get_roi()[1]

    def _set_bins(self, value):
        whbi = self._camera.get_roi_format()
        new_bins = int(value)
        supported = self._camera.get_camera_property()["SupportedBins"]
        print(f"Supported bins = {supported}")
        if new_bins < 0 or new_bins > max(supported):
            raise Exception

        old_bins = whbi[2]
        whbi[0] = 2*int(whbi[0]*old_bins / new_bins / 2)
        whbi[1] = 2*int(whbi[1]*old_bins / new_bins / 2)
        whbi[2] = new_bins
        print(f"Trying to set new res: {whbi}")

        self._camera.set_roi_format(*whbi)

    def get_readoutmode_str(self):
        it = self._camera.get_image_type()
        return image_types_by_value[it]

    def set_readoutmode_str(self, value):
        self._camera.set_image_type(image_types_by_name[value])
        self._reserve_buffer()

    def set_readoutmode(self, value):
        value = int(value)
        camera_info = self._camera.get_camera_property()
        supported = camera_info['SupportedVideoFormat']

        # list like "RGB8, RAW16"
        used_list = [image_types_by_value[s] for s in sorted(supported)]

        # value of 1 means RAW16 in above example
        image_type_name = used_list[value]

        # finally translate name into camera index and change:
        self._camera.set_image_type(image_types_by_name[image_type_name])
        self._reserve_buffer()

    def set_binx(self, value):
        value = int(value)
        self._set_bins(value)
        self._reserve_buffer()

    def set_biny(self, value):
        self._set_bins(value)
        self._reserve_buffer()

    def set_numx(self, value):
        value = int(value)
        sx, sy, _, h = self._camera.get_roi()
        self._camera.set_roi(sx, sy, value, h)
        self._reserve_buffer()

    def set_numy(self, value):
        value = int(value)
        sx, sy, w, _ = self._camera.get_roi()
        self._camera.set_roi(sx, sy, w, value)
        self._reserve_buffer()

    def set_startx(self, value):
        value = int(value)
        _, sy, w, h = self._camera.get_roi()
        self._camera.set_roi(value, sy, w, h)
        self._reserve_buffer()

    def set_starty(self, value):
        value = int(value)
        sx, _, w, h = self._camera.get_roi()
        self._camera.set_roi(sx, value, w, h)
        self._reserve_buffer()

    def abortexposure(self):
        pass  # TODO!

    def stoptexposure(self):
        self._camera.stop_exposure()

    def startexposure(self):
        self._camera.start_exposure(is_dark=False)
