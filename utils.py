from datetime import datetime
import falcon
import json


default_format = "%Y-%m-%d %H:%M:%S.%f"


def add_timestamp_before(req, response, resource, params):
    datetime_string = datetime.now().strftime(default_format)
    resource.set_timestamp(datetime_string)
    pass


def add_timestamp_after(req: falcon.Request, response: falcon.Response, resource):
    b = resource.get_timestamp()
    e = datetime.now().strftime(default_format)
    response.append_header("timestamps", json.dumps({"before": b, "after": e}))
    pass
