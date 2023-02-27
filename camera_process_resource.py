import falcon
import logging
import json
from multiprocessing import Pipe
from .camera_process import CameraProcessHandle, DONE_TOKEN, BUSY_TOKEN


log = logging.getLogger('main')


class CameraProcessResource:
    def __init__(self, processes, id_generator):
        self._processes = processes
        self._id_generator = id_generator
        print(f"Camera processes include: {self._processes}")
        self._busy = False

    def on_get(self, req: falcon.Request, resp: falcon.Response, camera_id, setting_name):
        try:
            camera_id = int(camera_id)
        except TypeError:
            resp.text = f"ID passed >>{camera_id}<< cannot be converted to int"
            resp.status = falcon.HTTP_412
            return
        log.debug(f"GET: Looking for resource named {setting_name} in camera no {camera_id}")
        if camera_id not in self._processes.keys():
            resp.text = f"There is no camera with number {camera_id}"
            resp.status = falcon.HTTP_417
            return
        cam_handle = self._processes[camera_id]
        self._process_get(resp, cam_handle, setting_name)

    def _check_state(self, handle: CameraProcessHandle, result_pipe: Pipe):
        if handle.state == "IDLE":
            print("Camera process idle")
            return handle.state
        if handle.state == "BUSY":
            print("Camera process WAS busy, polling...")
            if result_pipe.poll(timeout=0.1):
                print("Polling succeeded, getting status...")
                status_raw = result_pipe.recv()
                if status_raw.ok():
                    status = status_raw.get()
                else:
                    handle.state = "ERROR"
                    return handle.state
                print(f"Received status: {status}")
                if status == DONE_TOKEN:
                    handle.state = "IDLE"
                    return handle.state
            else:
                print("Polling failed, we are still busy...")
        return handle.state

    def _process_get(self, resp: falcon.Response, handle: CameraProcessHandle, setting_name: str):
        result_pipe = handle.result_pipe
        if "IDLE" != self._check_state(handle, result_pipe):
            resp.text = json.dumps({"Status": handle.state})
            resp.status = falcon.HTTP_412
            return
        command_pipe = handle.command_pipe

        command_pipe.send(setting_name)
        raw_result = result_pipe.recv()
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
