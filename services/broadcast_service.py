"""Broadcast business rules. No SIP or hardware side effects yet."""

from dataclasses import dataclass
from pathlib import Path

from services.device_service import get_device_status


@dataclass(frozen=True)
class BroadcastDecision:
    code: str
    message: str
    device_id: str | None = None
    source_kind: str | None = None


def plan_start_broadcast(
    device_id: str | None,
    broadcast_type: str | None,
    source_kind: str | None,
    source_path: str | None = None,
) -> BroadcastDecision:
    """Validate a request without dialing or changing device state."""
    if not device_id:
        return BroadcastDecision("missing_device_id", "请提供目标设备编号。")

    device = get_device_status(device_id)
    if device is None:
        return BroadcastDecision("device_not_found", f"未找到设备 {device_id}。", device_id)
    if device.get("type") != "DACU":
        return BroadcastDecision("unsupported_device", "目前只规划 DACU 人工广播。", device_id)
    if device.get("status") != "active":
        return BroadcastDecision("device_unavailable", f"设备 {device_id} 未标记为可用。", device_id)
    if broadcast_type != "manual":
        return BroadcastDecision("unsupported_type", "目前只规划实时人工广播。", device_id)
    if source_kind not in {"microphone", "audio_file"}:
        return BroadcastDecision(
            "missing_audio_source",
            "请选择电脑麦克风或本地音频文件作为音源。",
            device_id,
        )
    if source_kind == "audio_file":
        if not source_path:
            return BroadcastDecision("missing_audio_file", "请提供本地音频文件路径。", device_id)
        path = Path(source_path)
        if not path.is_file():
            return BroadcastDecision("audio_file_not_found", "本地音频文件不存在。", device_id)
        if path.suffix.lower() not in {".wav", ".mp3"}:
            return BroadcastDecision("unsupported_audio_file", "目前仅接受 WAV 或 MP3 文件。", device_id)

    return BroadcastDecision(
        "awaiting_sip_setup",
        "请求已校验，但尚未配置独立测试 SIP 分机，未发起呼叫或播放音频。",
        device_id,
        source_kind,
    )


def plan_stop_broadcast(device_id: str | None) -> BroadcastDecision:
    if not device_id:
        return BroadcastDecision("missing_device_id", "请提供目标设备编号。")
    if get_device_status(device_id) is None:
        return BroadcastDecision("device_not_found", f"未找到设备 {device_id}。", device_id)
    return BroadcastDecision(
        "no_active_session",
        "当前服务未建立 SIP 广播会话，因此没有可停止的真实广播。",
        device_id,
    )
