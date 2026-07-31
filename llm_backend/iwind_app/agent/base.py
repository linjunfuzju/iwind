from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator

from deepwind_app.llm import LLM
from deepwind_app.logger import logger
from deepwind_app.sandbox.client import SANDBOX_CLIENT
from deepwind_app.schema import ROLE_TYPE, AgentState, Memory, Message


class StepResult(BaseModel):
    content: Optional[str] = None
    terminate: bool = False
    force_tool: Optional[str] = None


class BaseAgent(BaseModel, ABC):
    name: str = Field(..., description="Unique name of the agent")
    description: Optional[str] = Field(None, description="Optional agent description")

    system_prompt: Optional[str] = Field(None, description="System-level instruction prompt")
    next_step_prompt: Optional[str] = Field(None, description="Prompt for determining next action")

    llm: LLM = Field(default_factory=LLM, description="Language model instance")
    memory: Memory = Field(default_factory=Memory, description="Agent's memory store")
    state: AgentState = Field(default=AgentState.IDLE, description="Current agent state")

    max_steps: int = 60
    current_step: int = 0
    duplicate_threshold: int = 2
    max_prompt_tokens: int = 40960  # 限制 next_step_prompt 长度

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        if self.llm is None or not isinstance(self.llm, LLM):
            self.llm = LLM(config_name=self.name.lower())
        if not isinstance(self.memory, Memory):
            self.memory = Memory()
        return self

    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        if not isinstance(new_state, AgentState):
            raise ValueError(f"Invalid state: {new_state}")

        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR
            raise e
        finally:
            self.state = previous_state

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

    async def run(self, request: Optional[str] = None) -> str:
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Cannot run agent from state: {self.state}")

        if request:
            self.update_memory("user", request)

        results: List[str] = []
        async with self.state_context(AgentState.RUNNING):
            while self.current_step < self.max_steps and self.state != AgentState.FINISHED:
                self.current_step += 1
                logger.info(f"Executing step {self.current_step}/{self.max_steps}")

                step_output = await self.step()

                if isinstance(step_output, StepResult):
                    results.append(f"Step {self.current_step}: {step_output.content}")
                    if step_output.terminate:
                        self.state = AgentState.FINISHED
                        break
                    if step_output.force_tool:
                        self.update_memory("system", f"Consider invoking tool: {step_output.force_tool}")
                else:
                    results.append(f"Step {self.current_step}: {step_output}")

                if self.is_stuck():
                    self.handle_stuck_state()
                    # Optional: early termination if stuck too long
                    if self.current_step >= 3:
                        self.update_memory("system", "Terminating due to repeated stuck state.")
                        self.state = AgentState.FINISHED
                        break

            if self.current_step >= self.max_steps:
                self.update_memory("system", f"Terminated: Reached max steps ({self.max_steps})")
                results.append(f"Terminated: Reached max steps ({self.max_steps})")

            self.current_step = 0
            self.state = AgentState.IDLE

        await SANDBOX_CLIENT.cleanup()
        return "\n".join(results) if results else "No steps executed"

    @abstractmethod
    async def step(self) -> Union[str, StepResult]:
        """Must be implemented by subclasses."""

    def handle_stuck_state(self):
        """Handle stuck state by adding a prompt to change strategy"""
        stuck_prompt = "\
        Observed duplicate responses. Consider new strategies and avoid repeating ineffective paths already attempted."
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt}"
        logger.warning(f"Agent detected stuck state. Added prompt: {stuck_prompt}")

    def is_stuck(self) -> bool:
        """Check if the agent is stuck in a loop by detecting duplicate content"""
        if len(self.memory.messages) < 2:
            return False

        last_message = self.memory.messages[-1]
        if not last_message.content:
            return False

        # Count identical content occurrences
        duplicate_count = sum(
            1
            for msg in reversed(self.memory.messages[:-1])
            if msg.role == "assistant" and msg.content == last_message.content
        )

        return duplicate_count >= self.duplicate_threshold

    def tool_call_count(self, tool_name: str) -> int:
        return sum(
            1 for msg in self.memory.messages
            if msg.role == "tool" and tool_name in msg.content
        )

    @property
    def messages(self) -> List[Message]:
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        self.memory.messages = value
