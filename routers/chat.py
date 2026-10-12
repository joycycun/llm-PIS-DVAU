from fastapi import APIRouter, Response

from models.chat import ChatRequest
from services.broadcast_service import plan_start_broadcast, plan_stop_broadcast
from services.device_service import get_device_status
from services.llm_service import ask_llm


router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest, response: Response):
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    result = await ask_llm(request.message)

    if result.intent == "get_device_status":
        if not result.device_id:
            result.answer = "请提供需要查询的设备编号。"
        else:
            device = get_device_status(result.device_id)
            if device is None:
                result.answer = f"未找到设备 {result.device_id}。"
            else:
                broadcast_status = device.get("broadcast_status", "stopped")
                broadcast_type = device.get("broadcast_type")
                if broadcast_status == "running" and broadcast_type:
                    broadcast_text = f"文件记录的广播状态为 {broadcast_type} 运行中"
                else:
                    broadcast_text = "文件记录的广播状态为未运行"
                result.answer = (
                    f"设备 {result.device_id} 文件记录的状态为 {device.get('status')}，"
                    f"位置为 {device.get('location')}；{broadcast_text}。"
                    "这不是实时设备状态。"
                )

    elif result.intent == "start_broadcast":
        parameters = result.parameters or {}
        decision = plan_start_broadcast(
            result.device_id,
            parameters.get("broadcast_type", "manual"),
            parameters.get("source_kind"),
            parameters.get("source_path"),
        )
        result.answer = f"{decision.message}（代码：{decision.code}）"

    elif result.intent == "stop_broadcast":
        decision = plan_stop_broadcast(result.device_id)
        result.answer = f"{decision.message}（代码：{decision.code}）"

    return {"message": result}
