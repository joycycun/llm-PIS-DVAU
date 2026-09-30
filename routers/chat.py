from fastapi import APIRouter, Response
from models.chat import ChatRequest
from services.llm_service import ask_llm
from services.device_service import (get_device_status,start_broadcast,)
from services.device_service import (
    get_device_status,
    start_broadcast,
    stop_broadcast,
)

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest, response: Response):
    response.headers["Content-Type"] = (
        "application/json; charset=utf-8"
    )
    result = await ask_llm(request.message)
    if result.intent == "get_device_status":
        if result.device_id is None:
            result.answer = "请提供需要查询的设备编号。"
        else:
            device = get_device_status(result.device_id)

            if device is None:
                result.answer = (
                    f"未找到设备 {result.device_id}。"
                )
            else:
                broadcast_status = device.get(
                    "broadcast_status",
                    "stopped"
                )

                broadcast_type = device.get("broadcast_type")

                if (
                    broadcast_status == "running"
                    and broadcast_type is not None
                ):
                    broadcast_text = (
                        f"正在进行 {broadcast_type} 广播"
                    )
                else:
                    broadcast_text = "当前未进行广播"

                result.answer = (
                    f"设备 {result.device_id} 当前状态为"
                    f" {device['status']}，"
                    f"位置为 {device['location']}，"
                    f"{broadcast_text}。"
                )
    elif result.intent == "start_broadcast":
        if result.device_id is None:
            result.answer = "请提供需要启动广播的设备编号。"
        else:
            broadcast_type = result.parameters.get(
                "broadcast_type",
                "manual"
            )

            device = start_broadcast(
                result.device_id,
                broadcast_type
            )

            if device is None:
                result.answer = (
                    f"未找到设备 {result.device_id}，"
                    "无法启动广播。"
                )
            else:
                result.answer = (
                    f"设备 {result.device_id} 已模拟启动广播，"
                    f"广播类型为 {broadcast_type}。"
                )
    elif result.intent == "stop_broadcast":
        if result.device_id is None:
            result.answer = "请提供需要停止广播的设备编号。"
        else:
            device = stop_broadcast(result.device_id)

            if device is None:
                result.answer = (
                    f"未找到设备 {result.device_id}，"
                    "无法停止广播。"
                )
            else:
                result.answer = (
                    f"设备 {result.device_id} 已模拟停止广播。"
                )
    return {"message": result}