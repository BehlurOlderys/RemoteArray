import falcon
import json


class StatusResource:
    # noinspection PyMethodMayBeStatic
    def on_get(self, _req, resp):
        resp.text = json.dumps({"server": "OK"})
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
