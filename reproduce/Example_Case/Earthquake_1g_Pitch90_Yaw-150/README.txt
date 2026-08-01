===============================================
ZWind 仿真环境 - 科研复现
===============================================
环境就绪，可以开始使用。

注意事项：
1. API 服务端口: 8005
2. 仿真结果目录: /app/simulation_runs/
3. 如需使用 LLM 功能，请配置 /app/.env 文件

快速开始：
  ./start.sh
  或者
  python3 -m uvicorn main:app --host 0.0.0.0 --port 8005

API 端点：
  - /health                    : 健康检查
  - /tools/zwind_typhoon_LLM   : 台风仿真（直接参数）
  - /tools/zwind_earthquake_LLM: 地震仿真（直接参数）
  - /tools/zwind_typhoon_LLM_Chat   : 台风仿真（LLM交互）
  - /tools/zwind_earthquake_LLM_Chat : 地震仿真（LLM交互）
  - /tools/tiqu_plot           : 可视化

===============================================
