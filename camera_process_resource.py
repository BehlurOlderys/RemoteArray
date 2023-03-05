from .camera_process import CameraProcessHandle, DONE_TOKEN, BUSY_TOKEN
from .camera_server_utils import CameraSimpleGETCommand, CameraSimplePUTCommand, \
    extract_client_and_transaction_id_for_put, create_ascom_response_dict

import falcon
import logging
import json
from multiprocessing import Queue
from traceback import format_exc
import os
import glob


log = logging.getLogger('main')
capture_path = os.path.join(os.getcwd(), "capture")


def get_latest_file_name():
    cwd_contents = [os.path.join(capture_path, d) for d in os.listdir(capture_path)]
    all_subdirs = [d for d in cwd_contents if os.path.isdir(d)]
    latest_subdir = max(all_subdirs, key=os.path.getmtime)
    list_of_files = glob.glob(latest_subdir+"/*.tif")
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def retrieve_file_image(resp, filename):
    resp.content_type = "image/tif"
    stream = open(filename, 'rb')
    content_length = os.path.getsize(filename)
    resp.stream, resp.content_length = stream, content_length
    resp.status = falcon.HTTP_200


def retrieve_last_image(resp):
    retrieve_file_image(resp, get_latest_file_name())


def save_image_to_file(camera, resp, filename):
    camera.save_image_to_file(filename)
    resp.status = falcon.HTTP_200


def save_image_and_send_bytes(camera, resp, filename):
    image_bytes, length = camera.save_to_file_and_get_imagebytes(filename)
    resp.content_type = "application/octet-stream"
    resp.data = image_bytes
    resp.content_length = length
    resp.status = falcon.HTTP_200


class CameraProcessResource:
    def __init__(self, processes, id_generator):
        self._processes = processes
        self._id_generator = id_generator

        print(f"Camera processes include: {self._processes}")
        self._capturing = False

    def _get_camera_handler(self, camera_id, setting_name, resp):
        try:
            camera_id = int(camera_id)
        except TypeError:
            resp.text = f"ID passed >>{camera_id}<< cannot be converted to int"
            resp.status = falcon.HTTP_412
            return None
        log.debug(f"GET: Looking for resource named {setting_name} in camera no {camera_id}")
        if camera_id not in self._processes.keys():
            resp.text = f"There is no camera with number {camera_id}"
            resp.status = falcon.HTTP_417
            return None
        return self._processes[camera_id]

    def on_get(self, req: falcon.Request, resp: falcon.Response, camera_id, setting_name):
        print(f"GET {setting_name}")
        if setting_name == "lastimage":
            self._handle_lastimage(resp)
            return
        cam_handle = self._get_camera_handler(camera_id, setting_name, resp)
        if cam_handle is None:
            return

        if setting_name == "imagebytes":
            self._handle_imagebytes(resp, cam_handle)
        else:
            self._process_get(req, resp, cam_handle, setting_name)

    def _handle_lastimage(self, resp: falcon.Response):
        try:
            retrieve_last_image(resp)
        except ValueError as e:
            resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
            resp.status = falcon.HTTP_412
        return

    def _handle_imagebytes(self, resp: falcon.Response, cam_handle: CameraProcessHandle):
        cam_handle.command_queue.put(CameraSimpleGETCommand("imagebytes"))
        raw_result = cam_handle.result_queue.get()
        if not raw_result.ok():
            resp.status = falcon.HTTP_500
            resp.text = raw_result.error()
            return

        data = cam_handle.data_pipe.recv()
        imagebytes, length = data
        resp.content_type = "application/octet-stream"
        resp.data = imagebytes
        resp.content_length = length
        resp.status = falcon.HTTP_200

    def _check_state(self, handle: CameraProcessHandle, result_queue: Queue):
        print(f"Current state = {handle.state}")
        if handle.state == "IDLE":
            print("Camera process idle")
            return handle.state
        if handle.state == "BUSY":
            print("Camera process WAS busy, polling...")

            at_least_one = False
            while not result_queue.empty():
                at_least_one = True
                status_raw = result_queue.get(block=False)
            if at_least_one:
                print("Polling succeeded, getting status...")
                if status_raw.ok():
                    status = status_raw.get()
                else:
                    handle.state = "ERROR"
                    return handle.state
                print(f"Received status: {status}")
                if status == DONE_TOKEN:
                    handle.state = "IDLE"
                    return status
                else:
                    return status
            else:
                print("Polling failed, we are still busy...")
        return handle.state

    def _process_get(self, req: falcon.Request, resp: falcon.Response, handle: CameraProcessHandle, setting_name: str):
        result_queue = handle.result_queue
        current_state = self._check_state(handle, result_queue)
        if "IDLE" != current_state:
            resp.text = json.dumps({"Status": current_state})
            resp.status = falcon.HTTP_412
            return
        command_queue = handle.command_queue

        try:
            client_id = int(req.params["ClientID"])
            client_transaction_id = int(req.params["ClientTransactionID"])
        except Exception as e:
            log.warning(f"Could not read params: {repr(e)}")
            resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
            resp.status = falcon.HTTP_400
            return

        command_queue.put(CameraSimpleGETCommand(setting_name))
        resp.status = falcon.HTTP_200
        server_transaction_id = self._id_generator.generate()
        raw_result = result_queue.get()

        error_msg = ""
        error_no = 0
        if not raw_result.ok():
            error_msg = raw_result.error()
            error_no = 500
            resp.status = falcon.HTTP_500

        result = raw_result.get()
        print(f"Acquired result: {result}")
        if result == BUSY_TOKEN:
            handle.state = "BUSY"

        response_dict = create_ascom_response_dict(client_transaction_id,
                                                   server_transaction_id,
                                                   error_number=error_no,
                                                   error_message=error_msg)
        response_dict.update({"Value": result})

        resp.text = json.dumps(response_dict)

    def on_put(self, req: falcon.Request, resp: falcon.Response, camera_id, setting_name):
        cam_handle = self._get_camera_handler(camera_id, setting_name, resp)
        if cam_handle is None:
            return
        print(f"PUT {setting_name}")
        self._process_put(req, resp, cam_handle, setting_name)

    def _process_put(self, req, resp, cam_handle: CameraProcessHandle, setting_name):
        if "IDLE" != self._check_state(cam_handle, cam_handle.result_queue):
            resp.text = json.dumps({"Status": cam_handle.state})
            resp.status = falcon.HTTP_412
            return

        try:
            form = req.media
            cid, ctid, params = extract_client_and_transaction_id_for_put(req)
            log.info(f"Send form = {form}")
        except Exception as e:
            log.warning(f"Could not read params: {repr(e)}")
            resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
            resp.status = falcon.HTTP_400
            return

        cam_handle.command_queue.put(CameraSimplePUTCommand(name=setting_name, params=params))
        log.info("Waiting for response")
        server_transaction_id = self._id_generator.generate()
        raw_result = cam_handle.result_queue.get()

        error_msg = ""
        error_no = 0
        resp.status = falcon.HTTP_200
        if not raw_result.ok():
            error_msg = raw_result.error()
            error_no = 500
            resp.status = falcon.HTTP_500

        result = raw_result.get()

        if result == BUSY_TOKEN:
            cam_handle.state = "BUSY"

        log.info(f"Response = {result}")
        response_dict = create_ascom_response_dict(ctid,
                                                   server_transaction_id,
                                                   error_number=error_no,
                                                   error_message=error_msg)
        response_dict.update({"Value": result})
        resp.text = json.dumps(response_dict)
