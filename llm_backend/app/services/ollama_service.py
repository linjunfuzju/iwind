from typing import List, Dict, AsyncGenerator, Optional, Callable
import aiohttp
import json
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(service = "ollama")


class OllamaService:
    def __init__(self):
        logger.info("Initializing Ollama Service for DeepWind")
        self.base_url = settings.OLLAMA_BASE_URL
        self.chat_model = settings.OLLAMA_CHAT_MODEL
        self.reason_model = settings.OLLAMA_REASON_MODEL

        # 海上风电领域专用系统提示词
        self.deepwind_prompt = (
            "你是浙江大学海上风电课题团队的多模态垂直领域大模型 Iwind，"
            "专注于海上风电领域的知识科普、载荷自动化仿真及运营维护辅助。"
            "回答问题时请从我们的视角出发，提供准确、有帮助的信息。\n"
            "具体要求：\n"
            "1. 技术问题回答要精确到具体参数和标准\n"
            "2. 科普内容要通俗易懂但保持专业性\n"
            "3. 仿真相关回答需注明假设条件和适用范围\n"
            "4. 运维建议应包含安全注意事项\n"
            "5. 引用数据需说明来源和时间"
        )

        # 专业子角色配置
        self.roles = {
            "default":self.deepwind_prompt,
            "expert":(
                "作为海上风电领域专家，用专业术语回答，"
                "提供详细技术参数和参考文献。"
            ),
            "educator":(
                "作为科普教育者，用简单易懂的方式解释复杂概念，"
                "适当使用比喻和示例。"
            ),
            "engineer":(
                "作为现场工程师，提供实用运维建议，"
                "强调安全规范和操作细节。"
            ),
            "researcher":(
                "作为前沿研究者，介绍最新技术和科研成果，"
                "分析发展趋势和挑战。"
            )
        }

    async def generate_stream(
            self,
            messages: List[Dict],
            user_id: Optional[int] = None,
            conversation_id: Optional[int] = None,
            on_complete: Optional[Callable] = None,
            *,
            role: Optional[str] = None,
            technical_level: str = "professional"  # 新增技术级别参数
    ) -> AsyncGenerator[str, None]:
        """流式生成回复（海上风电专用）

        Args:
            role: 子角色选择(expert/educator/engineer/researcher)
            technical_level: 技术深度(professional/technical/basic)
        """
        try:
            # 获取基础系统提示词
            system_prompt = self.roles.get(role, self.deepwind_prompt)

            # 根据技术级别调整提示词
            if technical_level == "basic":
                system_prompt += "\n当前用户是初学者，请用最简单的语言解释。"
            elif technical_level == "technical":
                system_prompt += "\n用户具备专业知识，可包含技术细节。"
            else:
                system_prompt += "\n用户是领域专家，需要深度技术分析。"

            # 准备消息列表
            processed_messages = self._prepare_messages(messages, system_prompt)

            # 使用推理模型
            full_response = []
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/api/chat",
                        json = {
                            "model":self.reason_model,
                            "messages":processed_messages,
                            "stream":True,
                            "keep_alive":-1,
                            "options":{
                                "temperature":0.5,  # 调低温度值提高确定性
                                "top_p":0.9
                            }
                        }
                ) as response:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                if content := chunk.get("message", {}).get("content"):
                                    full_response.append(content)
                                    yield f"data: {json.dumps(content, ensure_ascii = False)}\n\n"
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON decode error: {str(e)}")
                                continue

            if on_complete:
                complete_response = "".join(full_response)
                await on_complete(user_id, conversation_id, processed_messages, complete_response)

        except Exception as e:
            logger.error(f"DeepWind生成错误: {str(e)}")
            error_msg = json.dumps(f"[海上风电系统错误] {str(e)}", ensure_ascii = False)
            yield f"data: {error_msg}\n\n"
            raise

    def _prepare_messages(self, messages: List[Dict], system_prompt: str) -> List[Dict]:
        """特殊处理海上风电领域的消息格式"""
        # 确保系统提示词包含海上风电标识
        if not any("[海上风电]" in msg.get("content", "") for msg in messages if msg.get("role") == "system"):
            system_prompt = f"[海上风电系统]\n{system_prompt}"

        if messages and messages[0].get("role") == "system":
            return [{"role":"system", "content":system_prompt}] + messages[1:]
        return [{"role":"system", "content":system_prompt}] + messages

    async def generate(
            self,
            messages: List[Dict],
            *,
            role: Optional[str] = None,
            technical_level: str = "professional"
    ) -> str:
        """非流式生成（海上风电专用）"""
        try:
            system_prompt = self.roles.get(role, self.deepwind_prompt)
            if technical_level == "basic":
                system_prompt += "\n请用最简明的语言回答。"

            processed_messages = self._prepare_messages(messages, system_prompt)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/api/chat",
                        json = {
                            "model":self.chat_model,
                            "messages":processed_messages,
                            "stream":False,
                            "options":{
                                "temperature":0.3,  # 更保守的参数设置
                                "top_k":50
                            }
                        }
                ) as response:
                    result = await response.json()
                    return self._post_process(result["message"]["content"])

        except Exception as e:
            logger.error(f"DeepWind生成错误: {str(e)}")
            raise

    def _post_process(self, text: str) -> str:
        """后处理确保符合海上风电格式要求"""
        if "[海上风电]" not in text[:100]:
            return f"[Iwind回答]\n{text}"
        return text

