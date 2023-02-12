import falcon.status_codes
from .zwo_asi_camera_grabber import ASICamera
from .camera_server_utils import get_optional_query_params_for_ascom
from .camera_server_utils import check_camera_id
import json
import os
import logging


log = logging.getLogger('main')


camera_get_settings = {
    "ccdtemperature": lambda camera: camera.get_camera_temperature()
}

camera_put_settings = {
    "gain": lambda camera, value: camera.set_gain(value)
}


class CameraSettingsResource:
    def __init__(self, cameras, generator):
        self._cameras = cameras
        self._server_transaction_id_generator = generator

    def on_get(self, req, resp, camera_id, setting_name):
        if setting_name not in camera_get_settings.keys():
            resp.status = falcon.HTTP_404
            return
        if not check_camera_id(camera_id, self._cameras, resp):
            return

        camera = self._cameras[int(camera_id)]["instance"]
        value = (camera_get_settings[setting_name])(camera)
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
        if setting_name not in camera_put_settings.keys():
            resp.status = falcon.HTTP_404
            return
        if not check_camera_id(camera_id, self._cameras, resp):
            return

        form = req.media

        camera = self._cameras[int(camera_id)]["instance"]
        camera_put_settings[setting_name](camera, int(form["Gain"]))
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
