# 在config/tools_config.py中定义工具路由
TOOL_CONFIG = {
    "opensees_nonlinear_analysis": {
        "endpoint": "http://localhost:8001/opensees/structural/nonlinear",
        "method": "POST",
        "timeout": 30.0,
    }
}
