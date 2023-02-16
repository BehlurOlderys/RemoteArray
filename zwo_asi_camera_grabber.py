import zwoasi as asi
import matplotlib.pyplot as plt


asi_lib_path = "C:\\ASI SDK\\lib\\x64\\ASICamera2.dll"
asi_initialized = False

image_types_by_name = {
    "raw8": asi.ASI_IMG_RAW8,
    "rgb24": asi.ASI_IMG_RGB24,
    "raw16": asi.ASI_IMG_RAW16,
    "y8": asi.ASI_IMG_Y8
}


image_types_by_value = {v: k for k, v in image_types_by_name.items()}


class ASICamera:
    def __init__(self, camera_index):
        self._camera = asi.Camera(camera_index)
        self._index = camera_index

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

    def connect(self):
        asi._open_camera(self._index)

    def disconnect(self):
        asi._close_camera(self._index)

    def get_property(self):
        return self._camera.get_camera_property()

    def get_controls(self):
        return self._camera.get_controls()

    def set_exposure_us(self, exposure_us):
        self._camera.set_control_value(asi.ASI_EXPOSURE, exposure_us)

    def get_exposure_us(self):
        return self._camera.get_control_value(asi.ASI_EXPOSURE)[0]

    def set_gain(self, value):
        print(f"Will set gain as {value} DELETE ME!!!")  # TODO!
        self._camera.set_control_value(asi.ASI_GAIN, value)

    def get_gain(self):
        return self._camera.get_control_value(asi.ASI_GAIN)[0]

    def set_bandwidth(self, value):
        self._camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, value)

    def get_bandwidth(self):
        r = self._camera.get_control_value(asi.ASI_BANDWIDTHOVERLOAD)[0]
        print(f"bandwidth oveload = {r}")
        return r

    def set_high_speed_mode(self, value):
        self._camera.set_control_value(asi.ASI_HIGH_SPEED_MODE, 1)

    def get_high_speed_mode(self):
        r = self._camera.get_control_value(asi.ASI_HIGH_SPEED_MODE)[0]
        print(f"high speed mode = {r}")
        return r

    def get_properties(self):
        return self._camera.get_camera_property()

    def get_bin(self):
        return self._camera.get_bin()

    def get_supported_image_types(self):
        camera_info = self._camera.get_camera_property()
        supported = camera_info['SupportedVideoFormat']
        print(f"Supported = {supported}")
        return [image_types_by_value[s] for s in supported]

    def set_image_type(self, new_type):
        print(f"Trying to set new type {new_type} for images!")
        if new_type in image_types_by_name.keys():
            self._camera.set_image_type(image_types_by_name[new_type])

    def translate_image_type(self, value):
        return image_types_by_value[value]

    def get_image_type(self):
        return self._camera.get_image_type()

    def print_info(self):
        camera_info = self._camera.get_camera_property()
        print("CAMERA INFO:")
        print(camera_info)
        print("CAMERA CONTROLS:")
        for kk, v in self._camera.get_controls().items():
            print(f"{kk}:{v}")

    def connect_and_prepare_camera(self, exposure_ms=50, gain=0, roi=(256, 512)):
        camera_info = self._camera.get_camera_property()
        print(camera_info)
        # Use minimum USB bandwidth permitted
        self._camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, 40)
        print(f"HS = {self._camera.get_control_value(asi.ASI_HIGH_SPEED_MODE)}")
        controls = self._camera.get_controls()
        for cn in sorted(controls.keys()):
            print('    %s:' % cn)
            for k in sorted(controls[cn].keys()):
                print('        %s: %s' % (k, repr(controls[cn][k])))
        # Set ROI
        if roi is not None:
            image_w, image_h = roi
            start_x = (camera_info["MaxWidth"] - image_w) // 2
            start_y = (camera_info["MaxHeight"] - image_h) // 2
            image_w = image_w
            image_h = image_h
            print(f"ROI = {start_x}, {start_y}")
            self._camera.set_roi(start_x=start_x, start_y=start_y, width=image_w, height=image_h)
        self._camera.set_image_type(asi.ASI_IMG_RAW16)
        self._camera.set_control_value(asi.ASI_GAIN, gain)
        self._camera.set_control_value(asi.ASI_EXPOSURE, exposure_ms*1000)  # us

    def get_camera_temperature(self):
        return float(self._camera.get_control_value(asi.ASI_TEMPERATURE)[0]) / 10.0

    def capture_file(self, filename):
        try:
            self._camera.capture(filename=filename)
            return True
        except asi.ZWO_CaptureError as ce:
            print(f"error = {ce}, status = {ce.exposure_status}")
            return False

    def capture_image(self):
        return self._camera.capture()


def ask_user_for_camera_to_choose(list_of_cameras):
    choice = -1
    while choice < 0 or choice >= len(list_of_cameras):
        print(f"Choose camera by pressing number and hitting Enter key:")
        list_to_display = "".join([f"[{i}]: {c}\n" for i, c in enumerate(list_of_cameras)])
        print(list_to_display)
        choice = int(input())
    return choice


if __name__ == "__main__":
    """
    Some of the code is taken from examples:
    https://github.com/python-zwoasi/python-zwoasi/blob/master/zwoasi/examples/zwoasi_demo.py
    """

    asi_camera = ASICamera()
    # camera_id = ask_user_for_camera_to_choose(asi_camera.get_cameras_list())
    camera_id = 0
    asi_camera.connect_and_prepare_camera(camera_id=camera_id)

    image_buffer = asi_camera.capture_image()
    plt.imshow(image_buffer)
    plt.show()
