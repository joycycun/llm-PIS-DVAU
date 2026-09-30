import json
from pathlib import Path


DEVICES_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "devices.json"
)


def get_device_status(device_id: str) -> dict | None:
    with DEVICES_FILE.open("r", encoding="utf-8") as file:
        devices = json.load(file)

    return devices.get(device_id)