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

def start_broadcast(
    device_id: str,
    broadcast_type: str
) -> dict | None:
    with DEVICES_FILE.open("r", encoding="utf-8") as file:
        devices = json.load(file)

    device = devices.get(device_id)

    if device is None:
        return None

    device["broadcast_status"] = "running"
    device["broadcast_type"] = broadcast_type

    with DEVICES_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            devices,
            file,
            ensure_ascii=False,
            indent=2
        )
    return device

def stop_broadcast(device_id: str) -> dict | None:
    with DEVICES_FILE.open("r", encoding="utf-8") as file:
        devices = json.load(file)

    device = devices.get(device_id)

    if device is None:
        return None

    device["broadcast_status"] = "stopped"
    device["broadcast_type"] = None

    with DEVICES_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            devices,
            file,
            ensure_ascii=False,
            indent=2
        )

    return device