import falcon.status_codes
from .camera_server_utils import get_optional_query_params_for_ascom
from .camera_server_utils import check_camera_id
import json
import logging


log = logging.getLogger('main')


camera_get_settings = {
    "connected": lambda camera: camera.get_connected(),
    "name": lambda camera: camera.get_name(),
    "sensorname": lambda camera: camera.get_sensorname(),
    "canasymmetricbin": lambda camera: camera.get_canasymmetricbin(),
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
    "startx": lambda camera: camera.get_startx(),
    "starty": lambda camera: camera.get_starty(),
    "cansetccdtemperature": lambda camera: camera.get_cansetccdtemperature(),
    "cangetcoolerpower": lambda camera: camera.get_cangetcoolerpower(),
    "numx": lambda camera: camera.get_numx(),
    "numy": lambda camera: camera.get_numy(),
}

camera_put_settings = {
    "gain": {
        "method": lambda camera, value: camera.set_gain(value),
        "argname": "Gain",
        "argtype": int
    },
    "connected": {
        "method": lambda camera, value: camera.set_connected(value),
        "argname": "Connected",
        "argtype": bool
    },
    "numx": {
        "method": lambda camera, value: camera.set_numx(value),
        "argname": "NumX",
        "argtype": int
    },
    "numy": {
        "method": lambda camera, value: camera.set_numy(value),
        "argname": "NumY",
        "argtype": int
    },
    "startx": {
        "method": lambda camera, value: camera.set_startx(value),
        "argname": "StartX",
        "argtype": int
    },
    "starty": {
        "method": lambda camera, value: camera.set_starty(value),
        "argname": "StartY",
        "argtype": int
    },
    "startexposure": {
        # TODO!!!!
    }
}


class CameraSettingsResource:
    def __init__(self, cameras, generator):
        self._cameras = cameras
        self._server_transaction_id_generator = generator

    def on_get(self, req, resp, camera_id, setting_name):
        log.debug(f"GET: Looking for setting named {setting_name}")
        if setting_name not in camera_get_settings.keys():
            log.error(f"Setting >>{setting_name}<< not found, available keys are: {str(camera_get_settings.keys())}")
            resp.status = falcon.HTTP_404
            return
        if not check_camera_id(camera_id, self._cameras, resp):
            return

        camera = self._cameras[int(camera_id)]["instance"]
        value = camera_get_settings[setting_name](camera)
        log.debug(f"Will try to respond with value={value}")
        # TODO: an error can happen above!

        client_id, client_transaction_id = get_optional_query_params_for_ascom(req, "GET")
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

    def on_put(self, req, resp, camera_id, setting_name):
        log.debug(f"PUT: Looking for setting named {setting_name}")
        if setting_name not in camera_put_settings.keys():
            log.error(f"Setting >>{setting_name}<< not found, available keys are: {str(camera_get_settings.keys())}")
            resp.status = falcon.HTTP_404
            return
        if not check_camera_id(camera_id, self._cameras, resp):
            return

        form = req.media

        camera = self._cameras[int(camera_id)]["instance"]
        method = camera_put_settings[setting_name]["method"]
        argname = camera_put_settings[setting_name]["argname"]
        argtype = camera_put_settings[setting_name]["argtype"]

        try:
            method(camera, argtype(form[argname]))
        except Exception as e:
            log.error(e)
            resp.text = str(e)
            resp.status = falcon.HTTP_400
            return

        # TODO: an error can happen above!

        client_id, client_transaction_id = get_optional_query_params_for_ascom(req, "PUT")
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
        })
        resp.status = falcon.HTTP_200
