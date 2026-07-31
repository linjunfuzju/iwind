from deepwind_app.tool import BaseTool
from utils import global_variables
class AskHuman(BaseTool):
    """Add a tool to ask human for help."""

    name: str = "ask_human"
    description: str = """当你需要帮助、询问的时候调用这个工具"""
    parameters: str = {
        "type": "object",
        "properties": {
            "inquire": {
                "type": "string",
                "description": "The question you want to ask human.",
            }
        },
        "required": ["inquire"],
    }

    async def execute(self, inquire: str) -> str:
        print(f"Bot: {inquire}\n\nYou: ", end="", flush=True)
        q = global_variables.get_session_input_queue()
        print("ask_human session_id:", global_variables.get_current_session())
        user_input = await q.get()  # 先 await 获取用户输入
        return user_input.strip()  # 然后对字符串调用 strip()