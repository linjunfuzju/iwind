import re
import logging
from typing import Dict, List, Optional
from deepwind_app.agent.chat import ChatOnlyAgent
from deepwind_app.agent.manus import Manus
from deepwind_app.schema import Memory
from deepwind_app.llm import LLM
from utils.global_variables import get_session_queue, set_current_session
from utils.global_variables import get_current_session
# 日志初始化
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

tool_list = [
    "PythonExecute",
    "openfast_5MW_ITIBarge_DLL_WTurb_WavesIrr",
    "openfast_5MW_Land_DLL_WTurb",
    "openfast_5MW_Land_ModeShapes",
    "openfast_5MW_OC3Mnpl_DLL_WTurb_WavesIrr",
    "openfast_5MW_OC3Spar_DLL_WTurb_WavesIrr",
    "openfast_5MW_OC3Trpd_DLL_WSt_WavesReg",
    "openfast_5MW_OC4Jckt_DLL_WTurb_WavesIrr_MGrowth",
    "openfast_5MW_OC4Jckt_ExtPtfm",
    "openfast_5MW_OC4Semi_WSt_WavesWN",
    "openfast_5MW_TLP_DLL_WTurb_WavesIrr_WavesMulti",
    "yolo_detection"
]
tool_set = set(tool_list)


def extract_tool_name_from_text(text: str, valid_tools: set) -> Optional[str]:
    candidates = re.findall(r"`([^`]+)`", text)
    for c in candidates:
        if c in valid_tools:
            return c
    for tool in valid_tools:
        if tool.lower() in text.lower():
            return tool
    return None


async def is_user_confirming_execution(user_input: str) -> bool:
    prompt = f"""你是一个模块，负责判断用户输入是否明确确认执行操作。
yes 或 no，

规则：
- 如果用户明确表示想执行某操作(比如：执行上面的代码，执行，运行，确认，确认执行，开始等），返回 yes
- 如果不明确，或者说“加上，修改，换一个，给我完整的代码”等不是确认执行，返回 no

用户输入：{user_input}
判断："""

    llm = LLM(config_name="intent")
    result = await llm.ask(messages=[{"role": "user", "content": prompt}], stream=False)
    normalized = result.content.strip().split("</think>")[1].strip().lower()
    logger.info(f"[is_user_confirming_execution] 判断结果: {normalized}")
    return "yes" == normalized


def extract_code_blocks(text: str) -> List[str]:
    pattern = r"```(?:python)?\s*([\s\S]*?)```"
    return [block.strip() for block in re.findall(pattern, text) if block.strip()]


class TwoStageAgent:
    def __init__(self, session_id: str, images: List[Dict] = None):
        self.session_id = session_id
        self.shared_memory = Memory()
        self.chat_agent = ChatOnlyAgent(name="chat", memory=self.shared_memory)
        self.tool_agent = Manus(name="manus", memory=self.shared_memory)
        self.waiting_execute_confirmation = False
        self.chosed_tool: Optional[str] = None
        self.last_chat_response: Optional[str] = None
        self.images = images

    async def run(self, prompt: str) -> str:
        logger.info(f"[TwoStageAgent] 用户输入: {prompt}")
        logger.info(f"[TwoStageAgent] 当前状态: waiting_execute_confirmation={self.waiting_execute_confirmation}, chosed_tool={self.chosed_tool}")
        set_current_session(self.session_id)
        if self.images:
            await self.tool_agent.run_with_tool(prompt, 'YoloDetection')
            await self.emit_final_signal()
            return f"已处理图片内容，当前状态：{self.waiting_execute_confirmation}"
        
        if self.waiting_execute_confirmation:
            confirmed = await is_user_confirming_execution(prompt)
            logger.info(f"[TwoStageAgent] 用户执行确认: {confirmed}")
            if not confirmed:
                chat_response = await self.chat_agent.run(prompt)
                self.waiting_execute_confirmation = False
                self.chosed_tool = False

                # ➕ 重新进行工具提取
                self.chosed_tool = await self.extract_tool_from_response(prompt, chat_response)
                if self.chosed_tool:
                    self.waiting_execute_confirmation = True
                    await self.emit_final_signal()
                    return chat_response + f"\n\n✅ 检测到工具推荐：`{self.chosed_tool}`，是否需要我执行？请回复“执行”。"
                
                await self.emit_final_signal()
                return chat_response

            logger.info(f"[TwoStageAgent] 用户确认执行工具: {self.chosed_tool}")
            self.waiting_execute_confirmation = False

            if not self.chosed_tool:
                self.chat_agent.run(prompt)
                await self.emit_final_signal()
                return

            prompt_with_tool = f"请使用 {self.chosed_tool} 工具：{prompt}"
            exec_result = await self.tool_agent.run_with_tool(prompt_with_tool, self.chosed_tool)
            await self.tool_agent.cleanup()
            wrapped_result = await self.chat_agent.run(f"工具执行结果如下：\n{exec_result}")
            await self.emit_final_signal()
            return wrapped_result

        # 正常对话流程
        chat_response = await self.chat_agent.run(prompt)
        self.last_chat_response = chat_response
        self.chosed_tool = await self.extract_tool_from_response(prompt, chat_response)

        if self.is_generic_knowledge_question(prompt, chat_response) and self.chosed_tool != "PythonExecute":
            logger.info("[TwoStageAgent] 普通知识问答，不推荐工具")
            self.chosed_tool = None

        if self.chosed_tool:
            self.waiting_execute_confirmation = True
            await self.emit_final_signal()
            return chat_response + f"\n\n✅ 检测到工具推荐：`{self.chosed_tool}`，是否需要我执行？请回复“执行”。"

        await self.emit_final_signal()
        return chat_response

    async def extract_tool_from_response(self, user_input: str, model_response: str) -> Optional[str]:
        if self.is_generic_knowledge_question(user_input, model_response):
            logger.info("[extract_tool_from_response] 是知识问答，不调用工具")
            return None

        for tool in tool_set:
            if tool.lower() in user_input.lower():
                logger.info(f"[extract_tool_from_response] 用户输入中匹配工具: {tool}")
                return tool

        prompt = f"""
你是一个助手，请结合用户输入和助手回复，从下面工具中选择一个最合适的。

工具列表：{", ".join(tool_list)}

用户输入：{user_input}
助手回复：{model_response}

返回推荐的工具名（若无匹配，返回 None）：
"""

        llm = LLM(config_name="choose")
        result = await llm.ask(messages=[{"role": "user", "content": prompt}], stream=False)
        raw = result.content.strip()
        tool_extracted = extract_tool_name_from_text(raw, tool_set)

        if raw.lower() == "none" or tool_extracted is None:
            tool_extracted = None

        if not tool_extracted and re.search(r"```(?:python)?[\s\S]*?```", model_response, re.IGNORECASE):
            if "PythonExecute" in tool_set and not self.is_generic_knowledge_question(user_input, model_response):
                logger.info("[extract_tool_from_response] 检测代码块，默认选择 PythonExecute")
                tool_extracted = "PythonExecute"

        logger.info(f"[extract_tool_from_response] LLM提取工具: {tool_extracted}")
        return tool_extracted if tool_extracted in tool_set else None

    def is_generic_knowledge_question(self, user_input: str, model_response: str) -> bool:
        knowledge_keywords = ["介绍", "是什么", "定义", "解释", "原理", "基本概念", "怎么理解", "详细说明", "说明", "为什么"]
        return any(kw in user_input for kw in knowledge_keywords) and not any(tool in model_response for tool in tool_list)

    async def emit_final_signal(self):
        queue = get_session_queue()
        await queue.put({"is_final":True})
