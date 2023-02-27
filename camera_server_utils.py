import falcon
import json
import logging


log = logging.getLogger('main')


def get_optional_query_params_for_ascom(req: falcon.Request, method: str):
    if method == "GET":
        client_id = req.params["ClientID"]
        client_transaction_id = req.params["ClientTransactionID"]
    elif method == "PUT":
        client_id = req.media["ClientID"]
        client_transaction_id = req.media["ClientTransactionID"]
    else:
        raise RuntimeError(f"Method will not be handled: {method}")

    return int(client_id), int(client_transaction_id)


def check_camera_id(camera_id, cameras, resp):
    try:
        if int(camera_id) not in cameras.keys():
            log.warning(f"There is no camera no. {camera_id}")
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


class Result:
    def __init__(self, result, error):
        self._result = result
        self._error = error

    def ok(self):
        return len(self._error) == 0

    def get(self):
        return self._result

    def error(self):
        return self._error


class Error(Result):
    def __init__(self, error):
        super(Error, self).__init__("", error)


class OK(Result):
    def __init__(self, result):
        super(OK, self).__init__(result, "")