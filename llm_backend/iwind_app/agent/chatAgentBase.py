from abc import ABC, abstractmethod
from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator

from deepwind_app.llm import LLM
from deepwind_app.logger import logger
from deepwind_app.schema import ROLE_TYPE, Memory, Message


class ChatAgentBase(BaseModel, ABC):
    name: str = Field(..., description="Unique name of the chat agent")
    description: Optional[str] = Field(None, description="Optional agent description")

    llm: LLM = Field(default_factory=LLM, description="Language model instance")
    memory: Memory = Field(default_factory=Memory, description="Agent's memory store")

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @model_validator(mode="after")
    def initialize_agent(self) -> "ChatAgentBase":
        if self.llm is None or not isinstance(self.llm, LLM):
            self.llm = LLM(config_name=self.name.lower())
        if not isinstance(self.memory, Memory):
            self.memory = Memory()
        return self

    def update_memory(
        self,
        role: ROLE_TYPE,  # type: ignore
        content: str,
        base64_image: Optional[str] = None,
        **kwargs,
    ) -> None:
        message_map = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda content, **kw: Message.tool_message(content, **kw),
        }

        if role not in message_map:
            raise ValueError(f"Unsupported message role: {role}")

        if role == "tool" and base64_image is not None:
            all_kwargs = {"base64_image": base64_image, **kwargs}
            self.memory.add_message(message_map[role](content, **all_kwargs))
        else:
            self.memory.add_message(message_map[role](content))

    async def run(self, user_input: Optional[str] = None) -> str:
        """执行单步聊天，更新记忆并调用模型获取回复"""
        if user_input:
            self.update_memory("user", user_input)

        messages = self.memory.messages
        logger.info(f"{self.name} running with {len(messages)} messages in memory.")

        # 调用 LLM 生成回复（假设llm.ask返回ChatCompletionMessage）
        response = await self.llm.ask(messages=messages, stream=True)

        if response and response.content:
            self.update_memory("assistant", response.content)
            return response.content
        else:
            logger.warning(f"{self.name} received empty response from LLM.")
            return ""

    @property
    def messages(self) -> List[Message]:
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        self.memory.messages = value
