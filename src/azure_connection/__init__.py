from .cert_loader import add_cert, remove_cert
from .IoTDevice import IoTDevice
from pathlib import Path

def create_iot_device(settings_azure):
    try:
        add_cert(settings_azure["certificate_name"])
        iot_device = IoTDevice(
            **{k: v for k, v in settings_azure.items() if k not in ["certificate_name"]},
            certificate=Path(__file__).parent.parent.parent/"data"/"certificate_python.pfx"
        )
    finally:
        remove_cert()

    return iot_device
