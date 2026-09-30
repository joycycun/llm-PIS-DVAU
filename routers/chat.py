from fastapi import APIRouter, Response
from models.chat import ChatRequest
from services.llm_service import ask_llm
from services.device_service import get_device_status


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
                result.answer = (
                    f"设备 {result.device_id} 当前状态为"
                    f" {device['status']}，"
                    f"位置为 {device['location']}。"
                )
    return {"message": result}