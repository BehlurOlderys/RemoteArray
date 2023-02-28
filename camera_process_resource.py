from .camera_process import CameraProcessHandle, DONE_TOKEN, BUSY_TOKEN
from .camera_server_utils import CameraCommand, CameraSimpleCommand, get_optional_query_params_for_ascom

import falcon
import logging
import json
from multiprocessing import Queue


log = logging.getLogger('main')


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
        cam_handle = self._get_camera_handler(camera_id, setting_name, resp)
        if cam_handle is None:
            return
        self._process_get(resp, cam_handle, setting_name)

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

    def _process_get(self, resp: falcon.Response, handle: CameraProcessHandle, setting_name: str):
        result_queue = handle.result_queue
        current_state = self._check_state(handle, result_queue)
        if "IDLE" != current_state:
            resp.text = json.dumps({"Status": current_state})
            resp.status = falcon.HTTP_412
            return
        command_queue = handle.command_queue

        command_queue.put(CameraSimpleCommand(setting_name))
        raw_result = result_queue.get()
        if not raw_result.ok():
            resp.text = json.dumps({"Error": raw_result.error()})
            resp.status = falcon.HTTP_500
            return

        result = raw_result.get()
        print(f"Acquired result: {result}")
        if result == BUSY_TOKEN:
            handle.state = "BUSY"
        resp.text = json.dumps({"Result": result})
        resp.status = falcon.HTTP_200

    def on_put(self, req: falcon.Request, resp: falcon.Response, camera_id, setting_name):
        cam_handle = self._get_camera_handler(camera_id, setting_name, resp)
        if cam_handle is None:
            return
        self._process_put(req, resp, cam_handle, setting_name)

    def _process_put(self, req, resp, cam_handle: CameraProcessHandle, setting_name):
        if "IDLE" != self._check_state(cam_handle, cam_handle.result_queue):
            resp.text = json.dumps({"Status": cam_handle.state})
            resp.status = falcon.HTTP_412
            return
        form = req.media
        log.info(f"Send form = {form}")
        cam_handle.command_queue.put(CameraCommand(name=setting_name, params=form))
        log.info("Waiting for response")
        raw_result = cam_handle.result_queue.get()
        if not raw_result.ok():
            resp.text = json.dumps({"Error": raw_result.error()})
            resp.status = falcon.HTTP_500
            return
        result = raw_result.get()
        if result == BUSY_TOKEN:
            cam_handle.state = "BUSY"

        resp.text = json.dumps({"Result": result})
