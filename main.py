from typing import Union
import time
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse

from guiding_app.camera.zwo_camera import ZwoCamera
from pydantic import BaseModel


class CameraName(BaseModel):
    name: str


ZwoCamera.initialize_library()

app = FastAPI()
camera = None

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

favicon_path = 'favicon.ico'

@app.get('/favicon.ico')
async def favicon():
    print('Hosting favicon...')
    return FileResponse(favicon_path)

@app.get('/cameras_list')
def cameras_list():
    return {"cameras": ZwoCamera.get_cameras_list()}

@app.post('/init_camera')
def init_camera(data: CameraName):
    global camera
    cameras_list = ZwoCamera.get_cameras_list()
    camera_index = cameras_list.index(data.name)
    camera = ZwoCamera(camera_index)
    print(f"Initialized camera {data.name} with index {camera_index}")
    return data

@app.get('/camera/{camera_id}/demo')
def demo_camera(camera_id: int):
    if camera.demo():
        return FileResponse("image_mono.jpg")
    return {"error": "capture failed!"}

@app.get('/camera/{camera_id}/set_defaults')
def set_camera_defaults(camera_id: int):
    camera.set_defaults()

@app.get('/camera/{camera_id}/get_last_image')
def get_last_image(camera_id: int):
    is_ok, bytes_size, image_bytes = camera.get_last_image()
    return Response(content=image_bytes, media_type="application/octet-stream")

@app.get('/camera/{camera_id}/get_{setting}')
def get_camera_gain(camera_id: int, setting: str):
    is_success, value = camera.get_setting(setting)
    if is_success:
        return {"value": value}
    return {"error": value}


@app.get('/camera/{camera_id}/test')
def test_capture(camera_id: int):
    camera.capture("test.jpg")
    return FileResponse("test.jpg")

