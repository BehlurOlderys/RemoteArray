from typing import Union

from fastapi import FastAPI
from fastapi.responses import FileResponse

from guiding_app.camera.zwo_camera import ZwoCamera
from pydantic import BaseModel


class CameraName(BaseModel):
    name: str


ZwoCamera.initialize_library()

app = FastAPI()
camera = None


@app.get("/")
def read_root():
    return {"Hello": "World"}


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

