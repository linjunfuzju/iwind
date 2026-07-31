from deepwind_app.agent.chat import ChatOnlyAgent
from deepwind_app.agent.manus import Manus
from deepwind_app.llm import LLM


async def gpt_intent_classify(user_input: str) -> str:
    prompt = f"""你是一个意图识别模块，负责判断用户输入的内容是否需要调用工具执行具体操作，还是仅作为普通聊天对话。

判断规则：
- 如果用户请求执行具体操作，比如：
  - 运行代码、调试程序
  - 读取、写入、修改文件
  - 生成、编辑图片、绘图
  - 计算数学题、进行数据分析、统计
  - 任何需要外部工具辅助完成的任务
  则返回 "tool"

- 如果用户只是进行日常对话、提问知识性问题、闲聊、表达情感或想法，则返回 "chat"

注意事项：
- 只返回纯文本 "tool" 或 "chat"，不要添加任何多余的内容、解释或标点
- 返回内容全部小写
- 不要返回空白或其他词语
- 如果你有思考内容，请放在 <think> 和 </think> 标签中，最终判断在标签后单独输出

用户输入：{user_input}
你的判断："""

    llm = LLM(config_name="default")
    result = await llm.ask(
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )

    full_output = result.content.strip()
    
    # 处理 <think> 包裹的内容，提取最后一行的判断结果
    lines = [line.strip().lower() for line in full_output.splitlines() if line.strip()]
    for line in reversed(lines):
        if line in ("tool", "chat"):
            return line

    # fallback
    raise ValueError(f"无法识别意图分类结果，返回内容为: {full_output}")

class HybridAgent:
    def __init__(self, session_id: str):
        self.chat_agent = ChatOnlyAgent(name="chat")
        self.tool_agent = Manus(name="manus")

    async def run(self, prompt: str) -> str:
        intent = await gpt_intent_classify(prompt)
        if intent == "tool":
            return await self.tool_agent.run(prompt)
        else:
            print(f"intent: {intent}")
            return await self.chat_agent.run(prompt)
