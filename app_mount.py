import falcon
from .status_resource import MountStatusResource
from .mount_resource import MountResource
from .app_utils import add_log, DefaultServerTransactionIDGenerator
from .serial_utils import get_available_com_ports, SerialWriter


log = add_log("mount")

app = application = falcon.App()


server_transaction_id_generator = DefaultServerTransactionIDGenerator()
usb_ports = [p for p in get_available_com_ports() if "USB" in p]
mount_resource = MountResource(SerialWriter(usb_ports))
app.add_route("/mount/custom_command/{command_name}", mount_resource)
app.add_route("/status", MountStatusResource(usb_ports))
# app.add_route("/api/v1/camera/{camera_id}/{setting_name}", camera_resource)
