import falcon
import json


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
