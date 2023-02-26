import falcon.status_codes
from .camera_server_utils import get_optional_query_params_for_ascom
from .camera_server_utils import check_camera_id
import json
import os
import logging
from traceback import format_exc
import glob


log = logging.getLogger('main')
capture_path = os.path.join(os.getcwd(), "capture")


camera_get_settings = {
    "connected": lambda camera: camera.get_connected(),
    "name": lambda camera: camera.get_name(),
    "sensorname": lambda camera: camera.get_sensorname(),
    "driverinfo": lambda camera: camera.get_driverinfo(),
    "driverversion": lambda camera: camera.get_driverversion(),
    "supportedactions": lambda camera: camera.get_supportedactions(),

    "canpulseguide": lambda camera: camera.get_canpulseguide(),
    "canfastreadout": lambda camera: camera.get_canfastreadout(),
    "canasymmetricbin": lambda camera: camera.get_canasymmetricbin(),
    "cansetccdtemperature": lambda camera: camera.get_cansetccdtemperature(),
    "cangetcoolerpower": lambda camera: camera.get_cangetcoolerpower(),
    "canstopexposure": lambda camera: camera.get_canstopexposure(),
    "canabortexposure": lambda camera: camera.get_canabortexposure(),

    "readoutmode": lambda camera: camera.get_readoutmode(),
    "readoutmodes": lambda camera: camera.get_readoutmodes(),
    "pixelsizex": lambda camera: camera.get_pixelsizex(),
    "pixelsizey": lambda camera: camera.get_pixelsizey(),
    "interfaceversion": lambda camera: camera.get_interfaceversion(),
    "binx": lambda camera: camera.get_binx(),
    "biny": lambda camera: camera.get_biny(),
    "cameraxsize": lambda camera: camera.get_cameraxsize(),
    "cameraysize": lambda camera: camera.get_cameraysize(),
    "description": lambda camera: camera.get_description(),
    "ccdtemperature": lambda camera: camera.get_ccdtemperature(),
    "maxbinx": lambda camera: camera.get_maxbinx(),
    "maxbiny": lambda camera: camera.get_maxbiny(),
    "sensortype": lambda camera: camera.get_sensortype(),
    "maxadu": lambda camera: camera.get_maxadu(),
    "exposuremin": lambda camera: camera.get_exposuremin(),
    "exposuremax": lambda camera: camera.get_exposuremax(),
    "exposureresolution": lambda camera: camera.get_exposureresolution(),
    "startx": lambda camera: camera.get_startx(),
    "starty": lambda camera: camera.get_starty(),
    "numx": lambda camera: camera.get_numx(),
    "numy": lambda camera: camera.get_numy(),
    "imageready": lambda camera: camera.get_imageready(),
    "camerastate": lambda camera: int(camera.get_camerastate()),
    "cooleron": lambda camera: camera.get_cooleron(),
    "bayeroffsetx": lambda camera: camera.get_bayeroffsetx(),
    "bayeroffsety": lambda camera: camera.get_bayeroffsety(),
    "imagearray": lambda camera: camera.get_imagearray(),
    "imagearraybase64": lambda camera: camera.get_imagearraybase64(),
    "gain": lambda camera: camera.get_gain(),
    "gainmin": lambda camera: camera.get_gainmin(),
    "gainmax": lambda camera: camera.get_gainmax(),
    "heatsinktemperature": lambda camera: camera.get_heatsinktemperature(),
    "imagefile": None,
    "imagebytes": None,
    "saveimageandsendbytes": None,
    "saveimage": None,
    "lastimage": None
}

camera_put_settings = {
    "gain": {
        "method": lambda camera, args: camera.set_gain(int(args["Gain"])),
    },
    "connected": {
        "method": lambda camera, args: camera.set_connected(bool(args["Connected"])),
    },
    "numx": {
        "method": lambda camera, args: camera.set_numx(int(args["NumX"])),
    },
    "numy": {
        "method": lambda camera, args: camera.set_numy(int(args["NumY"])),
    },
    "readoutmode": {
        "method": lambda camera, args: camera.set_readoutmode(int(args["ReadoutMode"])),
    },
    "binx": {
        "method": lambda camera, args: camera.set_binx(int(args["BinX"])),
    },
    "biny": {
        "method": lambda camera, args: camera.set_biny(int(args["BinY"])),
    },
    "startx": {
        "method": lambda camera, args: camera.set_startx(int(args["StartX"])),
    },
    "starty": {
        "method": lambda camera, args: camera.set_starty(int(args["StartY"])),
    },
    "startexposure": {
        "method": lambda camera, args: camera.startexposure(
            float(args["Duration"]),
            bool(args["Light"]),
            bool(args.get("Save", False))
        ),
    },
    "stopexposure": {
        "method": lambda camera, args: camera.stopexposure(),
    },
    "abortexposure": {
        "method": lambda camera, args: camera.abortexposure(),
    }
}


def send_image_bytes(camera, resp):
    image_bytes, length = camera.get_imagebytes()
    resp.content_type = "application/octet-stream"
    resp.data = image_bytes
    resp.content_length = length
    resp.status = falcon.HTTP_200


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


class CameraResource:
    def __init__(self, cameras, id_generator):
        self._cameras = cameras
        self._server_transaction_id_generator = id_generator

    def _send_image_array(self, req, resp, camera):
        img = camera_get_settings["imagearray"](camera)
        log.info(req.headers)

        rank, dim0, dim1, dim2 = camera.get_image_specs()
        log.info(f"Image shape = {img.shape}, rank={rank}, dim0={dim0}, dim1={dim1}")
        try:
            client_id, client_transaction_id = get_optional_query_params_for_ascom(req, "GET")
        except Exception as e:
            resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
            resp.status = falcon.HTTP_400
            return

        if client_id < 0 or client_transaction_id < 0:
            resp.status = falcon.HTTP_400
            return

        log.debug(f"ClientID of request = {client_id}")
        server_transaction_id = self._server_transaction_id_generator.generate()
        log.debug(f"Responding with id = {server_transaction_id}")
        error_number = 0  # TODO!
        error_message = ""  # TODO!
        list_image = img.tolist()

        resp.text = json.dumps({
            "Type": 2,
            "Rank": rank,
            "ClientTransactionID": client_transaction_id,
            "ServerTransactionID": server_transaction_id,
            "ErrorNumber": error_number,
            "ErrorMessage": error_message,
            "Value": list_image
        })
        resp.status = falcon.HTTP_200

    def _handle_regular_get(self, camera, req, resp, method):
        value = method(camera)
        log.debug(f"Will try to respond with value={value}")
        try:
            client_id, client_transaction_id = get_optional_query_params_for_ascom(req, "GET")
        except Exception as e:
            resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
            resp.status = falcon.HTTP_400
            return
        log.debug(f"ClientID of request = {client_id}")
        server_transaction_id = self._server_transaction_id_generator.generate()
        log.debug(f"Responding with id = {server_transaction_id}")
        error_number = 0  # TODO!
        error_message = ""  # TODO!

        resp.text = json.dumps({
            "ClientTransactionID": client_transaction_id,
            "ServerTransactionID": server_transaction_id,
            "ErrorNumber": error_number,
            "ErrorMessage": error_message,
            "Value": value
        })
        resp.status = falcon.HTTP_200

    def on_get(self, req: falcon.Request, resp: falcon.Response, camera_id, setting_name):
        log.debug(f"GET: Looking for setting named {setting_name}")
        if not check_camera_id(camera_id, self._cameras, resp):
            return

        if setting_name not in camera_get_settings.keys():
            log.error(f"Setting >>{setting_name}<< not found, available keys are: {str(camera_get_settings.keys())}")
            resp.status = falcon.HTTP_404
            return

        log.debug("Prerequisites OK")
        cameras_entry = self._cameras[int(camera_id)]
        camera = cameras_entry["instance"]
        # TODO: an error can happen above!

        if setting_name == "lastimage":
            try:
                retrieve_last_image(resp)
            except ValueError as e:
                resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
                resp.status = falcon.HTTP_412
            return

        if setting_name == "saveimage":
            filename = cameras_entry["generator"].generate()
            save_image_to_file(camera, resp, filename)
            return

        if setting_name == "saveimageandsendbytes":
            filename = cameras_entry["generator"].generate()
            save_image_and_send_bytes(camera, resp, filename)
            return

        if setting_name == "imagebytes":
            send_image_bytes(camera, resp)
            return

        if setting_name == "imagearray":
            self._send_image_array(req, resp, camera)
            return
        else:
            method = camera_get_settings[setting_name]
            self._handle_regular_get(camera, req, resp, method)

    def on_put(self, req, resp, camera_id, setting_name):
        log.debug(f"PUT: Looking for setting named {setting_name}")
        if setting_name not in camera_put_settings.keys():
            log.error(f"Setting >>{setting_name}<< not found, available keys are: {str(camera_get_settings.keys())}")
            resp.status = falcon.HTTP_404
            return
        if not check_camera_id(camera_id, self._cameras, resp):
            return

        form = req.media
        log.info(f"Send form = {form}")

        camera = self._cameras[int(camera_id)]["instance"]
        method = camera_put_settings[setting_name]["method"]

        try:
            result = method(camera, form)
        except Exception as e:
            log.error(e)
            resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
            resp.status = falcon.HTTP_400
            return

        # TODO: an error can happen above!

        try:
            client_id, client_transaction_id = get_optional_query_params_for_ascom(req, "PUT")
        except Exception as e:
            resp.text = json.dumps({"error": repr(e), "trace": format_exc()})
            resp.status = falcon.HTTP_400
            return
        log.debug(f"ClientID of request = {client_id}")
        server_transaction_id = self._server_transaction_id_generator.generate()
        log.debug(f"Responding with id = {server_transaction_id}")
        error_number = 0  # TODO!
        error_message = ""  # TODO!

        response_json = {
          "ClientTransactionID": client_transaction_id,
          "ServerTransactionID": server_transaction_id,
          "ErrorNumber": error_number,
          "ErrorMessage": error_message,
        }
        if result is not None:
            response_json.update(result)

        resp.text = json.dumps(response_json)
        resp.status = falcon.HTTP_200
