from deepwind_app.agent.chatAgentBase import ChatAgentBase
from deepwind_app.schema import Message, Role
from deepwind_app.llm import LLM
from deepwind_app.schema import Memory, Message
from deepwind_app.logger import logger
from typing import Optional, List
from deepwind_app.prompt.chat import SYSTEM_PROMPT
from transformers import AutoTokenizer
class ChatOnlyAgent(ChatAgentBase):
    async def run(self, user_input: Optional[str] = None) -> str:
        """执行单步聊天，更新记忆并调用模型获取回复"""
        if user_input:
            self.update_memory("user", user_input)

        logger.info(f"{self.name} running with {len(self.memory.messages)} messages in memory.")
        logger.info(f"[Manus] Thinking with current state: {len(self.memory.messages)}")
        # ❗ 将 system_prompt 通过参数传递，而不是添加到 messages 中
        response = await self.llm.ask(
            messages=self.memory.messages,
            stream=True,
            system_msgs=(
                    [Message.system_message(SYSTEM_PROMPT)]
                    if SYSTEM_PROMPT
                    else None
                )
        )

        if response and response.content:
            self.update_memory("assistant", response.content)
            return response.content
        else:
            logger.warning(f"{self.name} received empty response from LLM.")
            return ""
