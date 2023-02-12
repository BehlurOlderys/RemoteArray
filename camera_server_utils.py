import falcon
import json


def get_optional_query_params_for_ascom(req: falcon.Request, method: str):
    client_id = 42
    client_transaction_id = 42

    if method == "GET":
        client_id = req.params.get("ClientID", 0)
        client_transaction_id = req.params.get("ClientTransactionID", 0)

    if method == "PUT":
        client_id = req.media.get("ClientID", 0)
        client_transaction_id = req.media.get("ClientTransactionID", 0)

    return client_id, client_transaction_id


def check_camera_id(camera_id, cameras, resp):
    try:
        if int(camera_id) not in cameras.keys():
            resp.status = falcon.HTTP_404
            return False
        else:
            resp.status = falcon.HTTP_200
            return True

    except ValueError:
        resp.text = json.dumps({"error": f"cannot convert {camera_id} to an integer"})
        resp.status = falcon.HTTP_400
        return False
