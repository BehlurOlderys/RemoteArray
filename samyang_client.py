import requests
import json
import time
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from ascom_camera import CameraState


ascom_states ={
    int(CameraState.IDLE): "IDLE",
    int(CameraState.WAITING): "WAITING",
    int(CameraState.EXPOSING): "EXPOSING",
    int(CameraState.READING): "READING",
    int(CameraState.DOWNLOAD): "DOWNLOAD",
    int(CameraState.ERROR): "ERROR",
}


class RequestCounter:
    def __init__(self):
        self._counter = 0

    def get_new_count(self):
        cc = self._counter
        self._counter += 1
        return cc


class AscomRequests:
    def __init__(self, address, counter: RequestCounter, cid=0):
        self._address = address + "/api/v1/"
        self._rc = counter
        self._cid = cid

    def _get_common_query(self):
        return {"ClientID": self._cid, "ClientTransactionID": self._rc.get_new_count()}


class CameraRequests(AscomRequests):
    def __init__(self, camera_no, **kwargs):
        super(CameraRequests, self).__init__(**kwargs)
        self._address += f"camera/{camera_no}"

    def _get_request(self, endpoint, query_params=None, headers=None):
        headers = headers if headers else {}
        query = self._get_common_query()
        if query_params is not None:
            query.update(query_params)
        return requests.get(f"{self._address}/{endpoint}", params=query, headers=headers)

    def _put_request(self, endpoint, query_params=None):
        query = self._get_common_query()
        if query_params is not None:
            query.update(query_params)
        return requests.put(f"{self._address}/{endpoint}", data=json.dumps(query))

    def get_camerastate(self):
        return self._get_request("camerastate").json()

    def put_startexposure(self, duration_s):
        return self._put_request("startexposure", {"Duration": duration_s, "Light": True, "Save": True}).json()

    def get_image_bytes(self):
        headers = {"Content-type": "application/octet-stream"}
        return self._get_request("imagebytes", headers=headers)

    def get_image_array(self):
        return self._get_request("imagearray")

    def get_image_file(self, filename):
        return self._get_request("imagefile", {"Filename": filename})

    def is_image_ready(self):
        r = self._get_request("imageready").json()
        return r["Value"]


rc = RequestCounter()
c = CameraRequests(camera_no=0, address="http://192.168.0.129:8080", counter=rc, cid=123)


root = tk.Tk()

refresh_time_ms = 1000


img = ImageTk.PhotoImage(Image.open("../file.png"))
panel = tk.Label(root, image=img)
panel.pack(side="bottom", fill="both", expand="yes")


def callback():
    exposure_s = 0.1
    image_w = 1280
    image_h = 960
    image_type = "RGB24"
    # TODO!!!! above constants!

    state = c.get_camerastate()["Value"]
    if state == 0:
        filename = c.put_startexposure(exposure_s)["Filename"]
        time.sleep(exposure_s)
        while not c.is_image_ready():
            state = c.get_camerastate()["Value"]
            print(f"Camera state = {ascom_states[state]}")
            time.sleep(5*exposure_s)
        # image_bytes = io.BytesIO(c.get_image_bytes().content)

        time_start = time.time()
        shape = [image_h, image_w]
        # if whbi[3] == asi.ASI_IMG_RAW8 or whbi[3] == asi.ASI_IMG_Y8:
        #     img = np.frombuffer(data, dtype=np.uint8)
        # elif whbi[3] == asi.ASI_IMG_RAW16:
        #     img = np.frombuffer(data, dtype=np.uint16)
        if image_type == "RGB24":
            img_array = np.frombuffer(c.get_image_bytes().content, dtype=np.uint8)
            shape.append(3)
        else:
            raise ValueError('Unsupported image type')

        img_array = img_array.reshape(shape)[:, :, ::-1]  # Convert BGR to RGB
        img2 = ImageTk.PhotoImage(Image.fromarray(img_array))
        panel.configure(image=img2)
        panel.image = img2
        time_stop = time.time()
        print(f"Time = {time_stop-time_start}")
    root.after(refresh_time_ms, callback)


root.after(refresh_time_ms, callback)
root.mainloop()
