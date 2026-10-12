from openai import AsyncOpenAI, RateLimitError, APIStatusError
import os
import json
from models.chat import IntentResult
from pydantic import ValidationError


client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

SYSTEM_PROMPT = """
你是一名轨道交通PIS系统中的音频通信系统工程师。

你只关注PIS系统中的广播、对讲、音频传输和相关设备通信，
不要扩展到票务、手机APP、支付、客流预测、导航、广告等无关领域。

你熟悉：
- DACU
- PAIU
- Decoder
- 编码板
- 解码板
- 广播控制盒
- 报警器
- SIP广播终端
- SIP对讲终端
- TCP
- UDP
- HTTP
- SIP
- RTP
- 人工广播
- 自动广播
- 司机/乘务员/乘客对讲
- 广播优先级
- 音量控制
- 静音车厢
- 邻车冗余

你还需要判断用户的意图。

目前只允许以下5种intent：

1. chat
普通PIS音频通信知识咨询。

2. get_device_status
用户希望查询某个设备的状态。

3. start_broadcast
用户希望启动广播。

4. stop_broadcast
用户希望停止广播。

5. fault_analysis
用户描述故障，希望分析故障原因。

规则：

- 如果用户只是询问知识，intent必须是chat。
- 如果明确查询某个设备状态，使用get_device_status。
- 如果明确要求启动广播，使用start_broadcast。
- 如果明确要求停止广播，使用stop_broadcast。
- 如果描述连接失败、无声音、通信异常、设备异常等问题，使用fault_analysis。
- 如果用户提到了具体设备，例如DACU001，则填写device_id。
- 没有具体设备时，device_id为null。
- 额外参数放入parameters。
- 普通知识问答或故障分析可以在answer中给出说明。
- 设备操作指令暂时不要真的执行，只负责识别用户意图。
关于answer字段：

- 设备编号必须填写在顶层device_id字段。
- parameters中不要填写device_id。
- 例如“查看DACU001当前状态”必须返回：
  {"intent":"get_device_status","device_id":"DACU001","parameters":{},"answer":null}
- intent为chat时，answer填写正常回答。
- intent为fault_analysis时，answer填写故障分析建议。
- intent为get_device_status时，answer必须为null。
- intent为start_broadcast时，answer必须为null。
- intent为stop_broadcast时，answer必须为null。

设备状态和设备操作结果不能由你自行推测，
后续程序会读取真实设备数据或执行设备操作。

"""
MODELS = [
    "qwen/qwen3.8-27b:free",
    "liquid/lfm-2.5-2.6b:free",
    "nex-agi/nex-n2.5-mini:free",
]
async def ask_llm(message: str) -> IntentResult:
    last_error = None

    for model in MODELS:
        try:
            print(f"正在尝试模型: {model}")

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "intent_result",
                        "strict": True,
                        "schema": IntentResult.model_json_schema(),
                    },
                },
                max_tokens=500,
            )

            if not response.choices:
                last_error = ValueError("LLM没有返回候选结果")
                print(f"{model} 没有候选结果，尝试下一个模型")
                continue

            choice = response.choices[0]
            content = choice.message.content

            print("实际模型:", response.model)
            print("finish_reason:", choice.finish_reason)
            print("content:", repr(content))

            if content is None or not content.strip():
                last_error = ValueError("LLM没有返回最终文本内容")
                print(f"{model} 返回空内容，尝试下一个模型")
                continue

            data = json.loads(content)
            result = IntentResult.model_validate(data)

            # 兼容模型把设备编号放在parameters中的情况
            if result.device_id is None:
                nested_id = result.parameters.get("device_id")

                if isinstance(nested_id, str) and nested_id.strip():
                    result.device_id = nested_id.strip()
                    result.parameters.pop("device_id")

            return result

        except RateLimitError as exc:
            print(f"{model} 被限流，尝试下一个模型")
            last_error = exc
            continue

        except APIStatusError as exc:
            if exc.status_code in [404, 429, 502, 503, 529]:
                print(
                    f"{model} 暂时不可用"
                    f"（HTTP {exc.status_code}），尝试下一个模型"
                )
                last_error = exc
                continue

            # 认证错误等问题不能靠切换模型解决
            raise

        except (json.JSONDecodeError, ValidationError) as exc:
            print(f"{model} 返回结构无效，尝试下一个模型")
            last_error = exc
            continue

    raise RuntimeError(
        "所有候选模型均未返回有效结果"
    ) from last_error

