import asyncio

from services.llm_service import ask_llm


async def main():
    test_messages = [
        "DACU是什么？",
        "查看DACU001当前状态",
        "启动DACU001人工广播",
        "停止DACU001广播",
        "DACU001 TCP连接失败"
    ]

    for message in test_messages:
        print("=" * 50)
        print("用户输入:", message)

        result = await ask_llm(message)

        print("intent:", result.intent)
        print("device_id:", result.device_id)
        print("parameters:", result.parameters)
        print("answer:", result.answer)


asyncio.run(main())