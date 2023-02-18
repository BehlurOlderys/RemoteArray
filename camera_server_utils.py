import falcon
import json
import logging


log = logging.getLogger('main')


def get_optional_query_params_for_ascom(req: falcon.Request, method: str):

    if method == "GET":
        client_id = req.params.get("ClientID")
        client_transaction_id = req.params.get("ClientTransactionID")

    if method == "PUT":
        client_id = req.media.get("ClientID")
        client_transaction_id = req.media.get("ClientTransactionID")

    return int(client_id), int(client_transaction_id)


def check_camera_id(camera_id, cameras, resp):
    try:
        if int(camera_id) not in cameras.keys():
            log.warn(f"There is no camera no. {camera_id}")
            resp.text = json.dumps({"error": f"camera with id {camera_id} not found"})
            resp.status = falcon.HTTP_404
            return False
        else:
            resp.status = falcon.HTTP_200
            return True

    except ValueError:
        resp.text = json.dumps({"error": f"cannot convert {camera_id} to an integer"})
        resp.status = falcon.HTTP_400
        return False
