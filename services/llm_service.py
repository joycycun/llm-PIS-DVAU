from openai import AsyncOpenAI, RateLimitError, APIStatusError
import os
import json
from models.chat import IntentResult


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
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],

                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "intent_result",
                        "strict": True,
                        "schema": IntentResult.model_json_schema()
                    }
                },

                max_tokens=500
            )

            response_message = response.choices[0].message

            print("实际模型:", response.model)
            print(
                "finish_reason:",
                response.choices[0].finish_reason
            )
            print(
                "content:",
                repr(response_message.content)
            )

            content = response_message.content

            if content is None:
                raise ValueError(
                    "LLM没有返回最终文本内容"
                )

            data = json.loads(content)

            return IntentResult.model_validate(data)

        except RateLimitError as e:
            print(f"{model} 被限流，尝试下一个模型")
            last_error = e
            continue

        except APIStatusError as e:

            if e.status_code in [429, 502, 503]:
                print(
                    f"{model} 暂时不可用，"
                    "尝试下一个模型"
                )
                last_error = e
                continue

            raise

    raise RuntimeError(
        "所有免费模型当前都不可用"
    ) from last_error

    response = await client.chat.completions.create(
        model="qwen/qwen3.8-27b:free",

        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": message
            }
        ],

        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "intent_result",
                "strict": True,
                "schema": IntentResult.model_json_schema()
            }
        },
        extra_body={
            "reasoning": {
                "max_tokens": 0
            }
        },

        max_tokens=1000
    )

    message = response.choices[0].message

    print("实际模型:", response.model)
    print("finish_reason:", response.choices[0].finish_reason)
    print("content:", repr(message.content))

    content = message.content

    if content is None:
        raise ValueError("LLM没有返回最终文本内容")

    data = json.loads(content)

    return IntentResult.model_validate(data)

# async def ask_llm(message: str):
    response = await client.responses.create(
        model="openrouter/free",
        instructions="""你是一名轨道交通PIS系统中的音频通信系统工程师。你只关注PIS系统中的广播、对讲、音频传输和相关设备通信，不要扩展到票务、手机APP、支付、客流预测、导航、广告等无关领域。你熟悉以下业务：

        1. 人工广播
        - 司机人工广播
        - 乘务员人工广播
        - 全列广播
        - 单车广播

        2. 自动广播
        - PIS触发自动广播
        - 广播内容与车内显示信息同步
        - 广播次数可配置

        3. 对讲功能
        - 司机对讲
        - 乘务员对讲
        - 乘客紧急对讲
        - 对讲呼叫、等待、接通、挂机等状态

        4. 广播和对讲优先级
        - 人工广播优先级高
        - 广播与对讲发生冲突时需要进行优先级处理
        - 乘客对讲可以在广播期间进行提示或等待

        5. 音频相关功能
        - 背景音乐
        - 娱乐音频
        - 卫生间语音
        - 音量控制
        - 静音车厢控制
        - 邻车冗余广播

        6. 相关设备
        - DACU
        - PAIU
        - Decoder
        - 编码板
        - 解码板
        - 广播控制盒
        - 报警器
        - SIP广播终端
        - SIP对讲终端
        - SIP网关

        7. 通信技术
        - TCP
        - UDP
        - HTTP
        - SIP
        - RTP
        - Socket
        - 设备通信协议

        当用户询问PIS系统时，
        默认从“广播、对讲、音频通信系统”的角度回答。

        如果用户的问题超出音频通信PIS范围，
        请明确说明该问题不属于当前PIS音频通信系统的主要范围，
        不要自行扩展无关业务。

        回答时优先结合工程实际，
        尽量使用设备、通信协议、状态流程和功能逻辑进行解释，
        避免泛泛介绍。""",
        input=message,
        max_output_tokens=500
    )
    return response.output_text