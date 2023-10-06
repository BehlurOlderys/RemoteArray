from typing import Union
import time
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse

from guiding_app.camera.zwo_camera import ZwoCamera
from pydantic import BaseModel


class CameraSetting(BaseModel):
    value: str

ZwoCamera.initialize_library()

app = FastAPI()
camera = None
favicon_path = '/home/pi/workspace/samyang_app/guiding_app/favicon.ico'
cameras = {}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get('/favicon.ico')
async def favicon():
    print('Hosting favicon...')
    return FileResponse(favicon_path)


@app.get('/cameras_list')
def cameras_list():
    return {"cameras": ZwoCamera.get_cameras_list()}


@app.post('/camera/{camera_id}/init_camera')
def init_camera(camera_id):
    camera_index = int(camera_id)
    if camera_index not in cameras.keys():
        cameras[camera_index] = ZwoCamera(camera_index)
        print(f"Initialized camera with index {camera_index}")
    else:
        print(f"Camera at index {camera_index} already initialized, nothing to do")
    return {"status": "OK"}


@app.get('/camera/{camera_id}/set_defaults')
def set_camera_defaults(camera_id: int):
    cameras[camera_id].set_defaults()


@app.get('/camera/{camera_id}/get_last_image')
def get_last_image(camera_id: int):
    camera = cameras[camera_id]
    r = camera.capture_to_buffer()
    is_ok, image_bytes, bytes_size = camera.get_last_image()
    by2 = bytes(image_bytes)
    print(f"Capturing result: {r}. Responding with image_size={bytes_size}")
    headers = {"x-image-mode": camera.get_readoutmode_str()}
    return Response(content=by2, headers=headers, media_type="application/octet-stream")


@app.get('/camera/{camera_id}/get_{setting}')
def get_camera_setting(camera_id: int, setting: str):
    camera = cameras[camera_id]
    is_success, value = camera.get_setting(setting)
    if is_success:
        return {"value": value}
    return {"error": value}


@app.post('/camera/{camera_id}/set_{setting}')
def set_camera_setting(camera_id: int, setting: str, data: CameraSetting):
    value = data.value
    camera = cameras[camera_id]
    is_success, output = camera.set_setting(setting, value)
    if is_success:
        return {"value": output}
    return {"error": output}


@app.get('/camera/{camera_id}/test')
def test_capture(camera_id: int):
    camera = cameras[camera_id]
    camera.capture("test.jpg")
    return FileResponse("test.jpg")
