import json
from fastapi import APIRouter,HTTPException

router=APIRouter()

def load_devices():
    with open("data/devices.json", "r",encoding="utf-8") as f:
        devices = json.load(f)
    return devices

@router.get("/devices/{device_id}")
async def get_device(device_id: str):
    devices=load_devices()
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    return devices[device_id]

@router.get("/devices")
async def get_devices():
    devices = load_devices()
    return devices