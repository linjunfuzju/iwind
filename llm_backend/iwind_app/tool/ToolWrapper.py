# 替换原始工具的执行方法
class ToolWrapper:
    def __init__(self, original_tool, wrapper_func):
        self.original_tool = original_tool
        self.wrapper_func = wrapper_func
        # 复制原始工具的所有属性
        self.name = original_tool.name
        self.description = original_tool.description
        self.parameters = original_tool.parameters

    async def execute(self, *args, **kwargs):
        return await self.wrapper_func(*args, **kwargs)

    async def __call__(self, *args, **kwargs):
        return await self.wrapper_func(*args, **kwargs)

    def to_param(self):
        return self.original_tool.to_param()
